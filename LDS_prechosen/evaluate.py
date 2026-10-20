"""Evaluation owns all targets. Geometry is fitted to recorded end states."""
import argparse
import csv
import hashlib
import json
from dataclasses import replace
from pathlib import Path
import platform
import numpy as np
from .model import BranchModel, Code, PREFERENCES, decode


def conditions():
    return [Code(l, d, s) for d, s in PREFERENCES for l in range(1, 7)]


def expected(code):
    l, d, s = code.location-1, code.direction, code.step
    return tuple((l + x) % 6 + 1 for x in (0, d, d+d*s, 2*d+d*s))


def geometry(runs):
    values = np.array([[state.embedded() for state in run] for run in runs])
    counts, dimensions, angle_matrices, residuals = [], [], [], []
    for rank in range(4):
        bases, dims, errs = [], [], []
        for group in range(4):
            x = values[group*6:(group+1)*6, rank]
            x = x-x.mean(axis=0)
            _, singular, vt = np.linalg.svd(x, full_matrices=False)
            dim = int(np.count_nonzero(singular > 1e-9))
            dims.append(dim)
            basis = vt[:dim].T
            bases.append(basis)
            errs.append(float(np.linalg.norm(x-x@basis@basis.T)))
        # Count distinct orientation projection matrices, not configured blocks.
        unique = []
        for basis in bases:
            projection = basis@basis.T
            if not any(np.linalg.norm(projection-p) < 1e-7 for p in unique):
                unique.append(projection)
        angles = np.zeros((4, 4, 2))
        for a in range(4):
            for b in range(4):
                cosines = np.linalg.svd(bases[a].T@bases[b], compute_uv=False)
                if len(cosines) != 2:
                    raise ValueError('Expected 2D spatial geometry; cannot report 2D angles')
                angles[a, b] = np.degrees(np.arccos(np.clip(cosines, 0, 1)))
        counts.append(len(unique))
        dimensions.append(dims)
        angle_matrices.append(angles.tolist())
        residuals.append(errs)
    return dict(measured_orientation_counts=counts, centered_spatial_dimensions=dimensions,
                principal_angles_degrees=angle_matrices, projection_residuals=residuals)


def evaluate():
    runs, rows = [], []
    for code in conditions():
        states, _ = BranchModel().run(code)
        actual = tuple(map(decode, states))
        runs.append(states)
        rows.append(dict(location=code.location, direction=code.direction, step=code.step,
                         actual=list(actual), expected=list(expected(code)), correct=actual == expected(code)))
    controls = {}
    for mode in ('no_direction', 'no_step', 'no_content', 'cut_final', 'identity_first_shift', 'all_gates_open'):
        correct = 0
        for code in conditions():
            model = BranchModel()
            state = model.initialize(code)
            if mode == 'no_direction':
                state = replace(state, direction_cue=[0, 0])
            elif mode == 'no_step':
                state = replace(state, step_cue=[0, 0])
            elif mode == 'no_content':
                state = replace(state, response=np.zeros((1, 6)))
            elif mode == 'cut_final':
                model.weights[2][:] = 0
            elif mode == 'identity_first_shift':
                model.weights[0][:, 0] = np.eye(6)
            elif mode == 'all_gates_open':
                state = replace(state, direction_cue=[1, 1], step_cue=[1, 1])
            states, _ = model.resume(state)
            correct += tuple(map(decode, states)) == expected(code)
        controls[mode] = correct
    source_hashes = {name: hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
                     for name in ('model.py', 'evaluate.py', 'tests/test_model.py')}
    summary = dict(conditions=24, correct=sum(r['correct'] for r in rows),
                   geometry=geometry(runs), negative_controls_correct=controls,
                   python=platform.python_version(), numpy=np.__version__, device='CPU',
                   source_sha256=source_hashes,
                   claims='Hand-wired mechanism sufficiency; no training or neural-data fit')
    return summary, rows, runs


def export(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    summary, rows, runs = evaluate()
    (output/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf8')
    with (output/'conditions.csv').open('w', encoding='utf8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    values = np.array([[s.embedded() for s in run] for run in runs])
    example, traces = BranchModel().run(Code(1, 1, 2))
    arrays = dict(response_endpoints=values, codes=np.array([[c.location,c.direction,c.step] for c in conditions()]))
    for k, trace in enumerate(traces, 1):
        for name in ('time', 'source', 'content', 'control', 'drive', 'target_rates'):
            arrays[f'transition{k}_{name}'] = getattr(trace, name)
    np.savez_compressed(output/'activities.npz', **arrays)
    # All graphics below consume saved arrays, never synthetic targets.
    with np.load(output/'activities.npz') as saved:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 4, figsize=(13, 3.5), constrained_layout=True)
        for rank, ax in enumerate(axes):
            for group, (d, s) in enumerate(PREFERENCES):
                data = saved['response_endpoints'][group*6:(group+1)*6, rank]
                center = data.mean(axis=0)
                _, _, vt = np.linalg.svd(data-center, full_matrices=False)
                xy = (data-center)@vt[:2].T
                # Display each group's own local PCA; offsets for readability only.
                ax.plot(xy[:, 0]+3*(group%2), xy[:, 1]+3*(group//2), 'o-', label=f'D={d}, S={s}')
            ax.set_title(f'R{rank+1}: {summary["geometry"]["measured_orientation_counts"][rank]} orientations')
            ax.set_aspect('equal')
            ax.set_xticks([]); ax.set_yticks([])
        axes[-1].legend(fontsize=7)
        fig.suptitle('Local 2D PCA per group; display offsets only. Angles in separate plot.')
        fig.savefig(output/'local_geometry.png', dpi=160)
        plt.close(fig)
        fig, axes = plt.subplots(1, 4, figsize=(12, 3), constrained_layout=True)
        angles = np.asarray(summary['geometry']['principal_angles_degrees'])
        for rank, ax in enumerate(axes):
            im = ax.imshow(angles[rank, :, :, 0], vmin=0, vmax=90, cmap='viridis')
            ax.set_title(f'R{rank+1} min principal angle')
            ax.set_xticks(range(4), ['+1','+2','-1','-2'])
            ax.set_yticks(range(4), ['+1','+2','-1','-2'])
        fig.colorbar(im, ax=list(axes), label='degrees')
        fig.savefig(output/'principal_angles.png', dpi=160)
        plt.close(fig)
        fig, axes = plt.subplots(1, 3, figsize=(12, 3), constrained_layout=True)
        for k, ax in enumerate(axes, 1):
            rates = saved[f'transition{k}_target_rates']
            ax.plot(saved[f'transition{k}_time'], rates.reshape(len(rates), -1))
            ax.set_title(f'R{k} -> R{k+1}: actual destination rates')
            ax.set_xlabel('seconds within external pulse'); ax.set_ylim(0, 1)
        fig.savefig(output/'rate_traces.png', dpi=160)
        plt.close(fig)
    controls = '\n'.join(f'- {name}: {value}/24' for name,value in summary['negative_controls_correct'].items())
    (output/'REPORT.md').write_text(
        '# 独立 response 分支模型验证报告\n\n'
        f'完整序列：{summary["correct"]}/24。实际末态拟合的方向子空间数：'
        f'{summary["geometry"]["measured_orientation_counts"]}。每组中心化位置维数均为 2。\n\n'
        '失败对照（完整序列正确数；沉默或并列峰均判失败）：\n\n'+controls+'\n\n'
        '原始末态及三次转移时间序列见 activities.npz；各条件见 conditions.csv；源码哈希与完整角度矩阵见 summary.json。\n\n'
        'local_geometry.png 的各组分别投影到自身 PCA，且添加展示平移，不能用图上的距离判定子空间关系；'
        'principal_angles.png 才显示共同 66 维空间内中心化位置子空间的夹角。\n\n'
        '这是预设分支和环移的工程验证，不是数据拟合、泛化学习或生物机制发现。'
        '未模拟真实神经元重叠、仿射偏置的提前分离、block 推断、噪声稳定性或自主时钟。\n', encoding='utf8')
    print(json.dumps(dict(correct=summary['correct'], geometry=summary['geometry']['measured_orientation_counts'],
                          controls=summary['negative_controls_correct']), ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default=str(Path(__file__).parent/'artifacts'))
    export(parser.parse_args().output)
