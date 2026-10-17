"""Targets, validation comparisons, and artifact export; never imported by model."""

from __future__ import annotations

from dataclasses import asdict, replace
from itertools import product
from pathlib import Path
import csv
import json
import platform
import sys
import numpy as np

from .model import CompressedCode, ModelParameters, RateDecompressor
from .diagnostics import (
    AGGREGATION_TOLERANCE, BLOCKED_TOLERANCE, DT_DIFFERENCE_LIMIT,
    EQUILIBRIUM_TOLERANCE, ODE_COARSE_LIMIT, ODE_REFINEMENT_RATIO,
    SETTLING_LIMIT, TAIL_SECONDS, packed_trace, transition_metrics,
)
from .reference import expanded_euler, ode_reference
from .timeline import build_timeline


def expected_sequence(location, direction, step):
    return tuple(1 + (location - 1 + direction * offset) % 6
                 for offset in (0, 1, 1 + step, 2 + step))


def evaluate_conditions(model):
    rows, results, metrics = [], [], []
    for l, d, s in product(range(1, 7), (1, -1), (1, 2)):
        result = model.decompress(CompressedCode(l, d, s))
        target = expected_sequence(l, d, s)
        rows.append(dict(L=l, D=d, S=s, target=list(target), predicted=list(result.positions),
                         correct=result.positions == target,
                         rank_correct=[int(a == b) for a, b in zip(result.positions, target)]))
        results.append(result)
        for trace in result.transitions:
            metrics.append(dict(L=l, D=d, S=s, **transition_metrics(trace)))
    return rows, results, metrics


def spatial_probes(model, n_angles=72):
    rows = []
    for angle in (np.arange(n_angles) + .173) * 2 * np.pi / n_angles:
        nearest = int(np.floor(angle / (np.pi / 3) + .5)) % 6 + 1
        for d, s in product((1, -1), (1, 2)):
            state = model.initialize_population(model.encode_angle(float(angle)), model.encode_tuning(d, s))
            result = model.resume(state)
            target = expected_sequence(nearest, d, s)
            rows.append(dict(angle_clockwise=float(angle), nearest_label=nearest, D=d, S=s,
                             predicted=list(result.positions), target=list(target),
                             correct=result.positions == target))
    return rows


def numerical_validation(model, rows, results):
    fine_model = RateDecompressor(replace(model.params, dt=model.params.dt / 2))
    largest_dt_error, largest_aggregation = 0.0, 0.0
    labels_match = True
    fine_by_code = {}
    for row, result in zip(rows, results):
        code = CompressedCode(row["L"], row["D"], row["S"])
        fine = fine_model.decompress(code)
        fine_by_code[row["L"], row["D"], row["S"]] = fine
        labels_match &= result.positions == fine.positions
        error = np.max(np.abs(build_timeline(result).rates - build_timeline(fine).rates[::2]))
        largest_dt_error = max(largest_dt_error, float(error))
        refs = expanded_euler(model, result.initial_state)
        for trace, ref in zip(result.transitions, refs):
            largest_aggregation = max(largest_aggregation, float(np.abs(packed_trace(trace) - ref["rates"]).max()))
    ode_rows, ode_samples, fine_samples, coarse_samples = [], [], [], []
    for index, (d, s) in enumerate(product((1, -1), (1, 2))):
        coarse, fine = results[index], fine_by_code[1, d, s]
        ref = ode_reference(model, model.encode_angle(0), model.encode_tuning(d, s), fine_model.params.dt)
        c_arrays = np.stack([packed_trace(t) for t in coarse.transitions])
        f_arrays = np.stack([packed_trace(t) for t in fine.transitions])
        o_arrays = np.stack(ref)
        ce, fe = float(np.abs(c_arrays - o_arrays[:, ::2]).max()), float(np.abs(f_arrays - o_arrays).max())
        ode_rows.append(dict(D=d, S=s, coarse_max_error=ce, fine_max_error=fe,
                             refinement_ratio=fe / ce, passed=ce <= ODE_COARSE_LIMIT and fe <= ODE_REFINEMENT_RATIO * ce))
        ode_samples.append(o_arrays)
        fine_samples.append(f_arrays)
        coarse_samples.append(c_arrays)
    example_expanded = expanded_euler(model, results[1].initial_state)
    payload = dict(ode_rates=np.stack(ode_samples), fine_rates=np.stack(fine_samples),
                   coarse_rates=np.stack(coarse_samples), fine_dt=fine_model.params.dt,
                   example_expanded_branches=np.stack([r["branches"] for r in example_expanded]),
                   example_expanded_aggregate=np.stack([r["rates"] for r in example_expanded]))
    report = dict(dt_halving_max_error=largest_dt_error, dt_halving_labels_match=bool(labels_match),
                  aggregation_max_error=largest_aggregation, independent_ode=ode_rows,
                  passed=bool(labels_match and largest_dt_error <= DT_DIFFERENCE_LIMIT
                              and largest_aggregation <= AGGREGATION_TOLERANCE and all(r["passed"] for r in ode_rows)))
    return report, payload


def _write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value) if isinstance(value, (list, tuple)) else value
                             for key, value in row.items()})


def run(output, *, probe_angles=72):
    import scipy
    import matplotlib
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    model = RateDecompressor()
    rows, results, metrics = evaluate_conditions(model)
    spatial = spatial_probes(model, probe_angles)
    numerical, reference_data = numerical_validation(model, rows, results)
    timelines = [build_timeline(result) for result in results]
    first = timelines[0]
    payload = dict(
        conditions=np.array([[r["L"], r["D"], r["S"]] for r in rows]),
        positions=np.array([r.positions for r in results]),
        position_activity=np.stack([r.position_activity for r in results]),
        time=first.time, rates=np.stack([t.rates for t in timelines]),
        labels=first.labels, groups=first.groups, modes=first.modes, rank_times=first.rank_times,
        local_time=results[0].transitions[0].time,
        integrated=np.stack([[packed_trace(t) for t in r.transitions] for r in results]),
    )
    for key in ("source_activity", "readout_raw_drive", "readout_drive", "readout_net_drive", "gate_drive",
                "branch_excitation", "branch_inhibition", "branch_target", "pooled_drive"):
        payload[key] = np.stack([[getattr(t, key) for t in r.transitions] for r in results])
    for group in ("direction", "step", "joint"):
        for key in ("raw_drive", "rates", "activity"):
            payload[f"{group}_{key}"] = np.stack([getattr(getattr(r.initial_state.encoding, group), key) for r in results])
    for key in vars(model.connections):
        payload[f"connection_{key}"] = getattr(model.connections, key)
    np.savez_compressed(output / "activities.npz", **payload)
    np.savez_compressed(output / "numerical_reference.npz", **reference_data)
    timelines[1].save(output / "sequence_timeline.npz")
    _write_csv(output / "conditions.csv", rows)
    _write_csv(output / "control_metrics.csv", metrics)
    _write_csv(output / "spatial_probes.csv", spatial)
    contract = dict(tail_seconds=TAIL_SECONDS, blocked_tolerance=BLOCKED_TOLERANCE,
                    equilibrium_tolerance=EQUILIBRIUM_TOLERANCE, settling_limit=SETTLING_LIMIT,
                    dt_difference_limit=DT_DIFFERENCE_LIMIT, ode_coarse_limit=ODE_COARSE_LIMIT,
                    ode_refinement_ratio=ODE_REFINEMENT_RATIO, aggregation_tolerance=AGGREGATION_TOLERANCE)
    summary = dict(
        model="29-rate shared relay with continuous competitive inhibitory gates; no training",
        parameters=asdict(model.params), validation_contract=contract,
        runtime=dict(executable=sys.executable, python=platform.python_version(), numpy=np.__version__,
                     matplotlib=matplotlib.__version__, scipy=scipy.__version__, backend="CPU"),
        conditions=24, correct=sum(r["correct"] for r in rows),
        rank_accuracy=np.mean([r["rank_correct"] for r in rows], axis=0).tolist(),
        control_checks=len(metrics), control_passes=sum(r["control_pass"] for r in metrics),
        maximum_settling_time=max(r["settling_time"] if r["settling_time"] is not None else float("inf") for r in metrics),
        maximum_terminal_vg_error=max(r["terminal_vg_error"] for r in metrics),
        maximum_terminal_blocked_drive=max(r["terminal_blocked_drive"] for r in metrics),
        maximum_transient_leakage=max(r["leakage_peak"] for r in metrics),
        maximum_leakage_integral=max(r["leakage_integral"] for r in metrics),
        minimum_position_margin=min(r["position_peak_margin"] for r in metrics),
        spatial_probes=len(spatial), spatial_correct=sum(r["correct"] for r in spatial),
        timeline_shape=list(payload["rates"].shape), numerical=numerical,
        representative=dict(L=1, D=1, S=2, predicted=list(results[1].positions)),
        passed=bool(all(r["correct"] for r in rows) and all(r["control_pass"] for r in metrics) and numerical["passed"]),
    )
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    from .plotting import plot_artifacts
    plot_artifacts(output)
    _write_report(output, summary)
    return summary


def _write_report(output, summary):
    n = summary["numerical"]
    text = f"""# 实际运行报告

默认公式和参数按批准设计独立实现，未训练、未调参。模型执行器不导入目标生成器。

- 完整序列：{summary['correct']}/24；四秩准确率：{summary['rank_accuracy']}。
- 控制验收：{summary['control_passes']}/{summary['control_checks']}；最大稳定时间：{summary['maximum_settling_time']:.6g} s。
- 最后0.1 s最大V/G平衡误差：{summary['maximum_terminal_vg_error']:.6g}；未选分支最大驱动：{summary['maximum_terminal_blocked_drive']:.6g}。
- 瞬态未选分支驱动峰值：{summary['maximum_transient_leakage']:.6g}；最大泄漏积分：{summary['maximum_leakage_integral']:.6g}。
- 最小秩末E峰值差：{summary['minimum_position_margin']:.6g}。
- 展开四路中继与共享模型最大误差：{n['aggregation_max_error']:.6g}。
- dt减半的全部率最大差：{n['dt_halving_max_error']:.6g}；标签相同：{n['dt_halving_labels_match']}。
- 独立ODE参考粗步长最大误差：{max(r['coarse_max_error'] for r in n['independent_ode']):.6g}；细步长/粗步长误差最大比：{max(r['refinement_ratio'] for r in n['independent_ode']):.6g}。
- 非边界角度诊断：{summary['spatial_correct']}/{summary['spatial_probes']}，不构成任意连续角度保证。
- 实际数组：{summary['timeline_shape']}，即24条件×1201时刻×29个原始率。

## 主要图片

- [全部29率变量](all_units_timeline.png)、[PDF](all_units_timeline.pdf)
- [完整机制过程](sequence_dynamics.png)、[PDF](sequence_dynamics.pdf)
- [联合调谐](joint_tuning.png)、[PDF](joint_tuning.pdf)
- [编码率与归一化活动](encoding_activity.png)、[PDF](encoding_activity.pdf)
- [全部24条件的29率变量多页PDF](all_conditions_rates.pdf)
- [全部条件图片索引](all_conditions/INDEX.md)

全部热图采用相同的原始率色标，不逐行归一化、不平滑。八个D/S/J保持率以棕色标签标出，21个积分率以青色标出。分支驱动只作为计算量展示，不冒充额外神经元。

## 数据与复现

- [24条件输出](conditions.csv)、[72次转移控制指标](control_metrics.csv)、[连续角度诊断](spatial_probes.csv)
- [全部实际活动与连接](activities.npz)、[代表条件唯一时间轴](sequence_timeline.npz)
- [独立ODE与展开参考数据，仅用于验证](numerical_reference.npz)
- [配置、环境与验收数值](summary.json)

时间从位置初始化结束开始；E/I/V/G在秩边界接续，M在新秩起点重置。图中的M重置属于明确的模型操作。初始和切换瞬态有未选路径活动，不能据末段静默称全程无泄漏。

29是率变量数，另有H采样保持、24分支整流、乘积与归一化等资源。这些结果验证已知L/D/S及固定环结构下的工程执行，不证明学习、自主记忆、时钟或六位置吸引子。
"""
    (output / "REPORT.md").write_text(text, encoding="utf-8")
