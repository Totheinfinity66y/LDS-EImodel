"""Evaluation-only targets and reproducible exports; never imported by model."""

from __future__ import annotations

from dataclasses import asdict
from itertools import product
from pathlib import Path
import csv
import json
import platform
import sys

import numpy as np

from .model import CompressedCode, RateDecompressor


def expected_sequence(location: int, direction: int, step: int) -> tuple[int, ...]:
    """Arithmetic oracle lives exclusively on the evaluation side."""
    return tuple(1 + (location - 1 + direction * offset) % 6
                 for offset in (0, 1, 1 + step, 2 + step))


def evaluate_conditions(model: RateDecompressor):
    rows, results = [], []
    for location, direction, step in product(range(1, 7), (1, -1), (1, 2)):
        result = model.decompress(CompressedCode(location, direction, step))
        target = expected_sequence(location, direction, step)
        rows.append(dict(
            L=location, D=direction, S=step,
            target=list(target), predicted=list(result.positions),
            shifts=[t.selected_shift for t in result.transitions],
            correct=result.positions == target,
            rank_correct=[int(a == b) for a, b in zip(result.positions, target)],
            maximum_blocked_relay=float(max(
                t.relay_rates[-1, np.arange(4) != np.argmax(t.readout.activity)].max()
                for t in result.transitions)),
        ))
        results.append(result)
    return rows, results


def spatial_probes(model: RateDecompressor, n_angles: int = 72):
    """Probe off-site states, with L's six-label task domain kept unchanged.

    A finite angular grid is diagnostic evidence, not a proof for all angles.
    Halfway-boundary states have ambiguous labels and are not sampled.
    """
    if not isinstance(n_angles, int) or n_angles < 6:
        raise ValueError("n_angles must be an integer >= 6")
    rows = []
    for angle in (np.arange(n_angles) + 0.173) * 2 * np.pi / n_angles:
        nearest = int(np.floor(angle / (np.pi / 3) + 0.5)) % 6 + 1
        for direction, step in product((1, -1), (1, 2)):
            initial = model.initialize_population(model.encode_angle(float(angle)),
                                                  model.encode_tuning(direction, step))
            result = model.resume(initial)
            target = expected_sequence(nearest, direction, step)
            rows.append(dict(angle_clockwise_radians=float(angle), nearest_site=nearest,
                             D=direction, S=step, predicted=list(result.positions),
                             target=list(target), correct=result.positions == target))
    return rows


def _save_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value) if isinstance(value, list) else value
                             for key, value in row.items()})


def run(output: Path, *, n_angles: int = 72):
    """Evaluate defaults once and export the actual rates used in plots."""
    model = RateDecompressor()
    rows, results = evaluate_conditions(model)
    spatial = spatial_probes(model, n_angles)
    output.mkdir(parents=True, exist_ok=True)
    _save_csv(output / "conditions.csv", rows)
    _save_csv(output / "spatial_probes.csv", spatial)
    # Representative L=1, D=+1, S=2; full numerical dynamics, not targets.
    example = results[1]
    tuning = [model.encode_tuning(d, s) for d, s in product((1, -1), (1, 2))]
    payload = dict(
        conditions=np.array([[r["L"], r["D"], r["S"]] for r in rows]),
        positions=np.array([r.positions for r in results]),
        position_activity=np.stack([r.position_activity for r in results]),
        direction_raw=np.stack([e.direction.raw_drive for e in tuning]),
        direction_rates=np.stack([e.direction.rates for e in tuning]),
        direction_activity=np.stack([e.direction.activity for e in tuning]),
        step_raw=np.stack([e.step.raw_drive for e in tuning]),
        step_rates=np.stack([e.step.rates for e in tuning]),
        step_activity=np.stack([e.step.activity for e in tuning]),
        joint_raw=np.stack([e.joint.raw_drive for e in tuning]),
        joint_rates=np.stack([e.joint.rates for e in tuning]),
        joint_activity=np.stack([e.joint.activity for e in tuning]),
        displacement_raw=np.stack([[t.readout.raw_drive for t in r.transitions] for r in results]),
        displacement_rates=np.stack([[t.readout.rates for t in r.transitions] for r in results]),
        displacement_activity=np.stack([[t.readout.activity for t in r.transitions] for r in results]),
        gate_i_rates=np.stack([[t.gate_i_rates for t in r.transitions] for r in results]),
        example_time=example.transitions[0].time,
        example_e=np.stack([t.e_rates for t in example.transitions]),
        example_i=np.stack([t.i_rates for t in example.transitions]),
        example_relays=np.stack([t.relay_rates for t in example.transitions]),
        example_e_drive=np.stack([t.e_drive for t in example.transitions]),
        example_relay_raw=np.stack([t.relay_raw_drive for t in example.transitions]),
        example_relay_inhibition=np.stack([t.relay_inhibitory_drive for t in example.transitions]),
        example_relay_target=np.stack([t.relay_target for t in example.transitions]),
        **{name: getattr(model.connections, name) for name in vars(model.connections)},
    )
    np.savez_compressed(output / "activities.npz", **payload)
    # The model owns every raw rate, including held controls. Plotters only read.
    from .timeline import SequenceTimeline
    recording = example.recording
    rank_times = np.r_[0.0, np.cumsum([t.time[-1] for t in example.transitions])]
    SequenceTimeline.from_recording(
        recording, rank_times, example.positions, [1, 1, 2],
    ).save(output / "sequence_timeline.npz")
    summary = dict(
        model="handcrafted L/D/S rate circuit; no training",
        parameters=asdict(model.params),
        runtime=dict(python=sys.version, executable=sys.executable,
                     numpy=np.__version__, platform=platform.platform(), backend="CPU"),
        conditions=len(rows), correct=sum(r["correct"] for r in rows),
        rank_accuracy=np.mean([r["rank_correct"] for r in rows], axis=0).tolist(),
        maximum_blocked_relay=max(r["maximum_blocked_relay"] for r in rows),
        spatial_probe_conditions=len(spatial), spatial_probe_correct=sum(r["correct"] for r in spatial),
        representative=dict(L=1, D=1, S=2, predicted=list(example.positions)),
        claims=["Supplied symbolic code and fixed ring/rank operators",
                "No evidence of learned rules, continuous attractors, or autonomous rank timing",
                "Off-site probes test quantized decoding on a finite angular grid"],
    )
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    from .plotting import plot_artifacts
    plot_artifacts(output)
    passed = summary["correct"] == 24 and summary["spatial_probe_correct"] == len(spatial)
    report = f"""# 实际运行结果

- 六位置 × 两方向 × 两步长：{summary['correct']}/24 条完整序列正确。
- 四秩准确率：{summary['rank_accuracy']}。
- 未选中继的最大末态率：{summary['maximum_blocked_relay']}。
- 环周诊断：{summary['spatial_probe_correct']}/{len(spatial)} 条通过；使用 {n_angles} 个非边界角度、4 个 D/S 组合。
- 示例 L=1,D=+1,S=2：实际输出 {list(example.positions)}。

模型读取的是给定 L/D/S，固定环移和秩连接包含任务规则；以上结果只验证该工程回路的执行能力。
环周诊断以最近的六位置标签评分，不是连续位置精确恢复或吸引子证明。
目标序列只存在于 evaluation.py；绘图读取 activities.npz 中的真实模型活动。

## 图与原始数据

- [联合调谐](joint_tuning.png)
- [编码率与归一化活动](encoding_activity.png)
- [三秩位移读出和门控](rank_readout.png)
- [真实 E/I 与中继时间过程](ei_dynamics.png)
- [完整序列时间轴：E1…E6、读出、门控与中继](sequence_dynamics.png)
- [全部47个率单元的活动总览](all_units_timeline.png)
- [时间轴解释与复现](../VISUALIZATION.md)
- [时间轴原始数组](sequence_timeline.npz)
- [24 条条件与实际输出](conditions.csv)
- [环周诊断](spatial_probes.csv)
- [运行配置和结果](summary.json)
- [活动及连接矩阵](activities.npz)
"""
    (output / "REPORT.md").write_text(report, encoding="utf-8")
    return summary, passed
