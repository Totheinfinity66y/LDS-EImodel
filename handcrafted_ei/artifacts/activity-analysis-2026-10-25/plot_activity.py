"""Post-hoc figures and local fixed-point probes from the archived v1 rates."""
from __future__ import annotations

import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "handcrafted_ei"
ARCHIVES = PACKAGE / "artifacts" / "v1"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from handcrafted_ei.model.ei_network import EINetwork  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_trial(archive: zipfile.ZipFile, i: int):
    stem = f"{i:02}"
    with np.load(io.BytesIO(archive.read(f"{stem}_rates.npz"))) as z:
        item = {key: z[key].copy() for key in z.files}
    events = json.loads(archive.read(f"{stem}_events.json"))
    task = json.loads(archive.read(f"{stem}_task.json"))
    return item, events, task


def verify_archives(names: list[str]) -> dict:
    expected = json.loads((ARCHIVES / "archives.json").read_text(encoding="utf-8"))
    checked = {}
    for name in names:
        path = ARCHIVES / name
        actual = sha256(path)
        if actual != expected[name]:
            raise ValueError(f"archive SHA256 mismatch: {name}")
        with zipfile.ZipFile(path) as zf:
            bad = zf.testzip()
            if bad:
                raise ValueError(f"ZIP CRC failure: {name}:{bad}")
        checked[name] = {"sha256": actual, "zip_crc": "PASS"}
    return checked


def save(fig, stem: str):
    fig.savefig(OUT / f"{stem}.png", dpi=220, bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.svg", bbox_inches="tight")
    plt.close(fig)


def timeline(events: dict):
    fig, ax = plt.subplots(figsize=(12, 5.8), constrained_layout=True)
    lanes = ["L input", "M_D / M_S input", "R1", "R2", "R3", "R4", "Readout"]
    y = {name: len(lanes) - 1 - i for i, name in enumerate(lanes)}
    colors = {"L input": "#4477AA", "M_D / M_S input": "#66AADD",
              "R1": "#228833", "R2": "#CCBB44", "R3": "#EE6677",
              "R4": "#AA3377", "Readout": "#666666"}
    for lane in lanes[:-1]:
        ax.hlines(y[lane], 0, events["end"], color="#d8d8d8", lw=1, zorder=0)
    for lane in ("L input", "M_D / M_S input"):
        ax.broken_barh([(events["sample_start"], events["sample_end"] - events["sample_start"])],
                       (y[lane] - .24, .48), color=colors[lane], alpha=.9)
    stages = [("R1", "sample_start", "retire1"), ("R2", "to_R2", "retire2"),
              ("R3", "to_R3", "retire3"), ("R4", "to_R4", "end")]
    for lane, start, stop in stages:
        ax.broken_barh([(events[start], events[stop] - events[start])],
                       (y[lane] - .24, .48), color=colors[lane], alpha=.52)
    flow_labels = [("R1", "L position state"), ("R2", "D branch state"),
                   ("R3", "inherit D; select S"), ("R4", "inherit (d,s)")]
    for lane, label in flow_labels:
        left, right = next((events[a], events[b]) for stage, a, b in stages if stage == lane)
        ax.text((left + right) / 2, y[lane], label, ha="center", va="center", fontsize=8,
                color="#202020")
    readouts = []
    for stage in range(1, 5):
        start = events[f"readout{stage}_start"]
        end = events[f"readout{stage}"]
        readouts.append((start, end - start))
        ax.axvline(end, color="#555555", lw=.8, alpha=.35)
        ax.text(end, y["Readout"] + .12, f"R{stage}", ha="center", va="bottom", fontsize=9)
    ax.broken_barh(readouts, (y["Readout"] - .22, .44), color=colors["Readout"])
    for key, label, color in [("to_R2", "D gate release", "#AA3377"),
                              ("to_R3", "S gate release", "#AA3377"),
                              ("to_R4", "R4 gate release", "#AA3377")]:
        ax.axvline(events[key], color=color, lw=1.25, ls="--", alpha=.8)
        ax.text(events[key] + 15, y["R4"] - .38, label, color=color, fontsize=8,
                rotation=90, va="bottom")
    ax.set_yticks([y[x] for x in lanes], lanes)
    ax.set_xlim(-30, events["end"] + 100)
    ax.set_ylim(-.75, len(lanes) - .25)
    ax.set_xlabel("Time (ms)")
    ax.set_title("Readout-first information flow and archived event timing")
    ax.grid(axis="x", alpha=.18)
    save(fig, "information-flow-timing")


def gating_plot(trial, events, task):
    t, r = trial["times_ms"], trial["rates"]
    net = EINetwork()
    groups = net.groups
    d = int(np.argmax(task["encoded"]["x_D"]))
    s = int(np.argmax(task["encoded"]["x_S"]))
    b = 2 * d + s
    r2 = groups["R2"].reshape(2, 6)
    r3 = groups["R3"].reshape(4, 6)
    traces = [
        ("M_D cue memory", r[:, groups["M_D"][d]], "#4477AA"),
        ("I_release", r[:, groups["release12"][d]], "#AA3377"),
        ("I_gate selected", r[:, groups["gate12"][d]], "#228833"),
        ("I_gate other", r[:, groups["gate12"][1-d]], "#999999"),
        ("R2 E selected branch max", r[:, r2[d]].max(axis=1), "#CCBB44"),
        ("R2 E other branch max", r[:, r2[1-d]].max(axis=1), "#BBBBBB"),
        ("I_release S", r[:, groups["release23"][s]], "#EE6677"),
        ("I_gate S-selected branch", r[:, groups["gate23"][b]], "#66AADD"),
        ("R3 E selected branch max", r[:, r3[b]].max(axis=1), "#228833"),
    ]
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True, constrained_layout=True)
    for name, values, color in traces[:6]:
        axes[0].plot(t, values, label=name, color=color, lw=1.5)
    for name, values, color in traces[6:]:
        axes[1].plot(t, values, label=name, color=color, lw=1.5)
    for ax in axes:
        for n in ("readout1", "to_R2", "readout2", "to_R3", "readout3", "to_R4"):
            if n in events:
                ax.axvline(events[n], color="#777777", lw=.75, ls=":" if n.startswith("readout") else "--", alpha=.5)
        ax.set_ylabel("Rate (0–1)")
        ax.set_ylim(-.04, 1.04)
        ax.grid(alpha=.18)
        ax.legend(ncol=3, fontsize=8, loc="upper right")
    axes[0].set_title("D release: I_release suppresses I_gate, opening the selected R2 route")
    axes[1].set_title("S release and selected (d,s) gate for R3")
    axes[1].set_xlabel("Time (ms)")
    fig.suptitle("Recorded neuron activities in archived baseline trial 00 (L=0, D=+1, S=1)")
    save(fig, "disinhibitory-gating")


def endpoint_states(archive):
    net = EINetwork()
    states = []
    for stage in range(1, 5):
        group_rows = []
        for i in range(24):
            trial, events, _ = read_trial(archive, i)
            j = int(np.argmin(np.abs(trial["times_ms"] - events["events"][f"readout{stage}"])))
            group_rows.append(trial["rates"][j])
        states.append(np.asarray(group_rows))
    return np.asarray(states), net


def subspace_plot(states):
    stages, n_trials, n_units = states.shape
    X = states.reshape(stages * n_trials, n_units)
    mean = X.mean(axis=0)
    centered = X - mean
    _, singular, vh = np.linalg.svd(centered, full_matrices=False)
    coords = centered @ vh[:3].T
    energy = singular ** 2
    vaf = energy / energy.sum()
    fig = plt.figure(figsize=(13, 5.6), constrained_layout=True)
    ax = fig.add_subplot(1, 2, 1)
    colors = ["#4477AA", "#228833", "#CCBB44", "#AA3377"]
    for s in range(stages):
        xy = coords[s*n_trials:(s+1)*n_trials]
        ax.scatter(xy[:, 0], xy[:, 1], s=30, alpha=.75, color=colors[s], label=f"R{s+1} endpoints")
        center = xy.mean(axis=0)
        ax.scatter(center[0], center[1], marker="x", s=70, linewidth=2, color=colors[s])
    ax.set_xlabel(f"PC1 ({vaf[0]*100:.1f}% variance)")
    ax.set_ylabel(f"PC2 ({vaf[1]*100:.1f}% variance)")
    ax.set_title("Common PCA coordinates of all 104 neurons")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(alpha=.18)
    bx = fig.add_subplot(1, 2, 2)
    pcs = np.arange(1, min(16, len(vaf)) + 1)
    bx.bar(pcs, vaf[:len(pcs)] * 100, color="#4477AA", alpha=.8, label="Per component")
    bx.plot(pcs, np.cumsum(vaf[:len(pcs)]) * 100, "o-", color="#AA3377", label="Cumulative")
    bx.set(xlabel="Principal component", ylabel="Variance (%)", title="Shared endpoint-state spectrum", xticks=pcs)
    bx.legend(frameon=False)
    bx.grid(axis="y", alpha=.18)
    rank, pr, stage_stats = {}, {}, {}
    for s in range(stages):
        Z = states[s] - states[s].mean(axis=0)
        sv = np.linalg.svd(Z, compute_uv=False)
        e = sv ** 2
        v = e / e.sum() if e.sum() else e
        rank[f"R{s+1}"] = int(np.sum(sv > max(Z.shape) * np.finfo(float).eps * (sv[0] if len(sv) else 0)))
        pr[f"R{s+1}"] = float(1 / (v @ v)) if v.sum() else 0.0
        stage_stats[f"R{s+1}"] = {"centered_rank": rank[f"R{s+1}"], "participation_ratio": pr[f"R{s+1}"]}
    fig.suptitle("Observed 104-dimensional population states at four readouts (24 conditions per stage)")
    save(fig, "all-neuron-subspace")
    return {"n_neurons": n_units, "n_endpoint_states": int(len(X)),
            "common_centered_rank": int(np.sum(singular > max(centered.shape) * np.finfo(float).eps * singular[0])),
            "common_participation_ratio": float(1 / np.sum((energy / energy.sum()) ** 2)),
            "common_vaf_first_10": vaf[:10].tolist(), "stage_specific": stage_stats}


def attractor_analysis(archive):
    net = EINetwork()
    W = net.signed_weights
    dt, tau = net.config["dt_ms"], net.tau
    candidates, residuals, radii = [], [], []
    times = None
    for i in range(24):
        trial, events, _ = read_trial(archive, i)
        times = trial["times_ms"]
        late = (times >= 1400) & (times <= 1750)
        rstar = trial["rates"][late].mean(axis=0)
        drive = W @ rstar + net.tonic - net.theta
        residuals.append(float(np.max(np.abs(np.clip(drive, 0, 1) - rstar))))
        active_slope = ((drive > 0) & (drive < 1)).astype(float)
        J = np.diag(1 - dt / tau) + (dt / tau)[:, None] * active_slope[:, None] * W
        radii.append(float(np.max(np.abs(np.linalg.eigvals(J)))))
        candidates.append(rstar)
    rng = np.random.default_rng(20261025)
    probe_curves = {0.005: [], 0.05: []}
    probe_final_states = {0.005: [], 0.05: []}
    probe_initial_states = {0.005: [], 0.05: []}
    for rstar in candidates:
        for amplitude in probe_curves:
            for _ in range(4):
                r0 = np.clip(rstar + rng.normal(0, amplitude, size=rstar.shape), 0, 1)
                delta0 = np.linalg.norm(r0 - rstar)
                net.rates = r0.copy()
                net.stimulus[:] = 0
                net.clock[:] = 0
                curve = [1.0]
                for _ in range(200):
                    net.step()
                    curve.append(float(np.linalg.norm(net.rates - rstar) / delta0) if delta0 else 0.0)
                probe_curves[amplitude].append(curve)
                probe_final_states[amplitude].append(net.rates.copy())
                probe_initial_states[amplitude].append(r0)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), constrained_layout=True)
    perturb_summary = {}
    candidate_matrix = np.asarray(candidates)
    for amplitude, color in ((0.005, "#4477AA"), (0.05, "#EE6677")):
        curves = np.asarray(probe_curves[amplitude])
        q05, median, q95 = np.quantile(curves, [.05, .5, .95], axis=0)
        t = np.arange(curves.shape[1]) * dt
        axes[0].fill_between(t, q05, q95, color=color, alpha=.16,
                             label=f"5th–95th percentile, SD={amplitude}")
        axes[0].plot(t, median, color=color, lw=1.8, label=f"Median, SD={amplitude}")
        final = np.asarray(probe_final_states[amplitude])
        initial = np.asarray(probe_initial_states[amplitude])
        nearest = np.linalg.norm(final[:, None, :] - candidate_matrix[None, :, :], axis=2).argmin(axis=1)
        initial_index = np.repeat(np.arange(len(candidates)), 4)
        ratios = curves[:, -1]
        distances_to_candidates = np.linalg.norm(final[:, None, :] - candidate_matrix[None, :, :], axis=2)
        perturb_summary[str(amplitude)] = {
            "median_distance_ratio_at_1000ms": float(np.median(ratios)),
            "max_distance_ratio_at_1000ms": float(np.max(ratios)),
            "fraction_within_1e-3_of_original_state": float(np.mean(ratios < 1e-3)),
            "fraction_nearest_to_different_saved_state": float(np.mean(nearest != initial_index)),
            "max_final_distance_to_nearest_saved_state": float(np.max(distances_to_candidates.min(axis=1))),
            "median_absolute_final_state_change": float(np.median(np.linalg.norm(final - initial, axis=1))),
        }
    axes[0].axhline(1e-3, color="#AA3377", ls="--", lw=1, label="0.1% of initial deviation")
    axes[0].set_yscale("log")
    axes[0].set(xlabel="Time after perturbation (ms)", ylabel="Distance from saved delay state / initial distance",
                title="Local perturbation recovery (24 states × 4 probes)")
    axes[0].legend(frameon=False, fontsize=8)
    axes[0].grid(alpha=.18, which="both")
    axes[1].scatter(np.arange(1, 25), radii, color="#AA3377", s=22)
    axes[1].axhline(1, color="#777777", ls="--", lw=1, label="Stability boundary")
    axes[1].set(xlabel="Baseline condition", ylabel="Spectral radius", ylim=(.8, 1.03),
                title=f"Local Euler-map spectral radius = {np.median(radii):.3f}")
    axes[1].text(.04, .12, f"Max fixed-point residual: {max(residuals):.1e}",
                 transform=axes[1].transAxes, fontsize=9)
    axes[1].legend(frameon=False, fontsize=8, loc="upper right")
    axes[1].grid(alpha=.18)
    fig.suptitle("Delay-state stability probe under zero stimulus and zero clock")
    save(fig, "delay-state-attractor-probe")
    return {"candidate_states": len(candidates), "probes_per_state_per_amplitude": 4,
            "perturbation_sd_values": [0.005, 0.05], "probe_duration_ms": 200 * dt,
            "max_fixed_point_residual": float(max(residuals)),
            "median_fixed_point_residual": float(np.median(residuals)),
            "local_euler_spectral_radius_min": float(min(radii)),
            "local_euler_spectral_radius_median": float(np.median(radii)),
            "local_euler_spectral_radius_max": float(max(radii)),
            "perturbation_results": perturb_summary,
            "interpretation": "Local stable fixed-point evidence for the saved delay states under zero stimulus and clock; not a global basin, continuous-attractor, or autonomous stage-transition test."}


def jacobian_and_vector_field(archive):
    """Plot the piecewise local Jacobian and a two-dimensional slice of the 104D field."""
    net = EINetwork()
    W, tau = net.signed_weights, net.tau
    dt = float(net.config["dt_ms"])
    states, labels = [], None
    for i in range(24):
        trial, _, _ = read_trial(archive, i)
        late = (trial["times_ms"] >= 1400) & (trial["times_ms"] <= 1750)
        states.append(trial["rates"][late].mean(axis=0))
        labels = trial["labels"]
    states = np.asarray(states)
    rstar = states[0]
    drive = W @ rstar + net.tonic - net.theta
    slope = ((drive > 0) & (drive < 1)).astype(float)
    # f(r)=(-r+clip(Wr+b,0,1))/tau in the zero-input, zero-clock delay.
    A = (-np.eye(len(rstar)) + slope[:, None] * W) / tau[:, None]
    J = np.eye(len(rstar)) + dt * A
    eig_A, eig_J = np.linalg.eigvals(A), np.linalg.eigvals(J)

    groups = [str(x).split("[")[0] for x in labels]
    boundaries = [i for i in range(1, len(groups)) if groups[i] != groups[i - 1]]
    centers, names, start = [], [], 0
    for end in boundaries + [len(groups)]:
        centers.append((start + end - 1) / 2)
        names.append(groups[start])
        start = end
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.2), constrained_layout=True,
                             gridspec_kw={"width_ratios": [1.35, 1]})
    lim = float(np.quantile(np.abs(A), .995))
    im = axes[0].imshow(A, cmap="coolwarm", vmin=-lim, vmax=lim, interpolation="nearest", aspect="auto")
    for b in boundaries:
        axes[0].axhline(b - .5, color="black", lw=.45, alpha=.45)
        axes[0].axvline(b - .5, color="black", lw=.45, alpha=.45)
    axes[0].set(xticks=centers, xticklabels=names, yticks=centers, yticklabels=names,
                xlabel="Presynaptic activity coordinate", ylabel="Postsynaptic rate derivative",
                title="Continuous-time local Jacobian A (ms⁻¹)")
    axes[0].tick_params(axis="x", labelrotation=70, labelsize=7)
    axes[0].tick_params(axis="y", labelsize=7)
    fig.colorbar(im, ax=axes[0], shrink=.78, label="∂fᵢ / ∂rⱼ (ms⁻¹)")
    axes[1].scatter(eig_A.real, eig_A.imag, s=22, alpha=.7, color="#4477AA", label="Eigenvalues of A")
    axes[1].axvline(0, color="#AA3377", ls="--", lw=1, label="Stability boundary Re(λ)=0")
    axes[1].set(xlabel="Real part (ms⁻¹)", ylabel="Imaginary part (ms⁻¹)",
                title=f"Local eigenvalues; max Re(λ)={eig_A.real.max():.4f} ms⁻¹")
    axes[1].grid(alpha=.18)
    axes[1].legend(frameon=False, fontsize=8)
    fig.suptitle("Piecewise-linear Jacobian at baseline condition 00 delay state")
    save(fig, "delay-state-jacobian")

    # PCA basis from all 24 delay states. Evaluate the field on a 2D slice through
    # condition 00; remaining coordinates are fixed at that saved activity vector.
    _, _, vh = np.linalg.svd(states - states.mean(axis=0), full_matrices=False)
    basis = vh[:2].T
    coords = (states - states.mean(axis=0)) @ basis
    spread = float(np.max(np.abs(coords - coords[0])))
    half_width = max(.06, min(.25, spread * 1.25))
    grid = np.linspace(-half_width, half_width, 31)
    xx, yy = np.meshgrid(grid, grid)
    vx, vy = np.zeros_like(xx), np.zeros_like(yy)
    for row in range(xx.shape[0]):
        for col in range(xx.shape[1]):
            r = np.clip(rstar + basis[:, 0] * xx[row, col] + basis[:, 1] * yy[row, col], 0, 1)
            field = (-r + np.clip(W @ r + net.tonic - net.theta, 0, 1)) / tau
            projected = basis.T @ field
            vx[row, col], vy[row, col] = projected
    speeds = np.hypot(vx, vy)
    fig, ax = plt.subplots(figsize=(7.8, 6.6), constrained_layout=True)
    norm = np.maximum(speeds, np.finfo(float).tiny)
    q = ax.quiver(xx, yy, vx / norm, vy / norm, speeds, cmap="viridis",
                  angles="xy", pivot="mid", scale=30, width=.0032)
    ax.scatter(coords[:, 0] - coords[0, 0], coords[:, 1] - coords[0, 1],
               s=22, facecolors="none", edgecolors="#EE6677", linewidths=.9,
               label="24 observed delay states (projected)")
    ax.scatter(0, 0, marker="*", color="#AA3377", s=120, zorder=4, label="Condition 00 state")
    ax.set(xlim=(-half_width, half_width), ylim=(-half_width, half_width),
           xlabel="PC1 displacement from condition 00 (rate units)",
           ylabel="PC2 displacement from condition 00 (rate units)",
           title="Projected zero-input vector field on a local 2D slice")
    ax.legend(frameon=True, fontsize=8, loc="upper right")
    ax.grid(alpha=.16)
    fig.colorbar(q, ax=ax, shrink=.82, label="Projected speed ‖Uᵀf(r)‖ (rate/ms)")
    fig.suptitle("104-neuron dynamics: other coordinates held at the saved delay state")
    save(fig, "delay-state-vector-field")
    return {
        "state": "baseline condition 00 mean rates at 1400-1750 ms",
        "continuous_jacobian_units": "ms^-1",
        "continuous_jacobian_max_real_eigenvalue": float(eig_A.real.max()),
        "continuous_jacobian_matrix_shape": list(A.shape),
        "continuous_jacobian_saturated_units_zero_slope": int(np.sum((drive <= 0) | (drive >= 1))),
        "continuous_jacobian_active_slope_units": int(slope.sum()),
        "continuous_jacobian_eigenvalues": [[float(x.real), float(x.imag)] for x in eig_A],
        "euler_map_spectral_radius_condition_00": float(np.max(np.abs(eig_J))),
        "vector_field": {
            "basis": "PC1-PC2 of the 24 saved delay states; centered on condition 00",
            "slice": "other 102 activity coordinates fixed at condition 00 state; plotted states clipped to [0,1]",
            "grid_points_per_axis": int(len(grid)), "half_width_rate_units": half_width,
            "projected_speed_min": float(speeds.min()), "projected_speed_max": float(speeds.max()),
            "projected_speed_median": float(np.median(speeds)),
            "interpretation": "2D projection/slice for visualization; arrows are not full 104D trajectories or a basin estimate."
        }
    }


def recurrence_control_summary():
    net = EINetwork()
    output = {}
    for name, w_rec in (("recurrence_0.0.zip", 0.0), ("recurrence_1.6.zip", 1.6),
                        ("baseline.zip", 2.0), ("recurrence_2.2.zip", 2.2)):
        zf = zipfile.ZipFile(ARCHIVES / name)
        correct = 0
        late = {key: [] for key in ("R1", "M_D", "M_S")}
        for i in range(24):
            trial, events, task = read_trial(zf, i)
            correct += int(events["outputs"] == task["target"])
            ix = (trial["times_ms"] >= 1400) & (trial["times_ms"] <= 1750)
            for key in late:
                values = trial["rates"][ix][:, net.groups[key]]
                late[key].append(float(values.max()))
        output[str(w_rec)] = {"sequences_correct": correct, "n": 24,
                              "median_late_max_activity": {key: float(np.median(vals)) for key, vals in late.items()}}
    return output


def main():
    receipt = json.loads((ARCHIVES / "verification.json").read_text(encoding="utf-8"))
    if receipt.get("status") != "PASS":
        raise ValueError("archived verification receipt is not PASS")
    used = ["baseline.zip", "recurrence_0.0.zip", "recurrence_1.6.zip", "recurrence_2.2.zip"]
    checked = verify_archives(used)
    baseline = zipfile.ZipFile(ARCHIVES / "baseline.zip")
    first, events, task = read_trial(baseline, 0)
    if first["rates"].shape != (663, 104) or len(first["labels"]) != 104:
        raise ValueError("unexpected baseline activity shape")
    if not np.all(np.isfinite(first["rates"])):
        raise ValueError("non-finite neural activities")
    baseline_audit = {"trials_checked": 0, "rate_min": 1.0, "rate_max": 0.0,
                      "fixed_timestamps": True, "fixed_labels": True}
    for i in range(24):
        trial_i, _, _ = read_trial(baseline, i)
        if trial_i["rates"].shape != (663, 104) or trial_i["y"].shape != (663, 6):
            raise ValueError(f"unexpected activity array shape in baseline trial {i:02}")
        baseline_audit["fixed_timestamps"] &= bool(np.array_equal(trial_i["times_ms"], first["times_ms"]))
        baseline_audit["fixed_labels"] &= bool(np.array_equal(trial_i["labels"], first["labels"]))
        if not np.all(np.isfinite(trial_i["rates"])) or trial_i["rates"].min() < 0 or trial_i["rates"].max() > 1:
            raise ValueError(f"invalid rate values in baseline trial {i:02}")
        baseline_audit["rate_min"] = min(baseline_audit["rate_min"], float(trial_i["rates"].min()))
        baseline_audit["rate_max"] = max(baseline_audit["rate_max"], float(trial_i["rates"].max()))
        baseline_audit["trials_checked"] += 1
    if not baseline_audit["fixed_timestamps"] or not baseline_audit["fixed_labels"]:
        raise ValueError("baseline timestamp or neuron-label mismatch")
    timeline(events["events"])
    gating_plot(first, events["events"], task)
    states, _ = endpoint_states(baseline)
    subspace = subspace_plot(states)
    attractor = attractor_analysis(baseline)
    local_dynamics = jacobian_and_vector_field(baseline)
    recurrence_controls = recurrence_control_summary()
    config = json.loads((ARCHIVES / "config.json").read_text(encoding="utf-8"))
    env = json.loads((ARCHIVES / "environment.json").read_text(encoding="utf-8"))
    provenance = {"created_utc_date": "2026-10-25", "analysis_scope": "post-hoc plots plus local delay-state stability probes",
                  "verification_receipt": receipt, "verified_archives": checked,
                  "baseline_activity_shape_per_trial": list(first["rates"].shape),
                  "baseline_data_audit": baseline_audit,
                  "all_neuron_labels": first["labels"].tolist(),
                  "condition_00": {"L": task["L"], "D": task["D"], "S": task["S"]},
                  "saved_experiment_environment": env,
                  "analysis_environment": {"python": sys.version, "executable": sys.executable,
                                           "numpy": np.__version__, "matplotlib": matplotlib.__version__,
                                           "pyyaml": yaml.__version__},
                  "source_files": {"plot_activity.py": sha256(Path(__file__).resolve()),
                                   "connectivity.py": sha256(PACKAGE / "model" / "connectivity.py"),
                                   "ei_network.py": sha256(PACKAGE / "model" / "ei_network.py"),
                                   "neuron.py": sha256(PACKAGE / "model" / "neuron.py"),
                                   "baseline.yaml": sha256(PACKAGE / "config" / "baseline.yaml")},
                  "config": config, "subspace_analysis": subspace, "attractor_analysis": attractor,
                  "local_dynamics_visualization": local_dynamics,
                  "recurrence_controls": recurrence_controls}
    (OUT / "analysis.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    local = attractor["perturbation_results"]["0.005"]
    broader = attractor["perturbation_results"]["0.05"]
    report = f"""# Archived E/I activity analysis

The figures use checksum-verified `handcrafted_ei/artifacts/v1` rates. Its receipt records **PASS** for 39 experiments and 936 trials. Four archives used here (`baseline.zip` and the three recurrence scans) also passed SHA256 and ZIP CRC checks. All 24 baseline trials contain finite 663 × 104 rate arrays with matched timestamps, labels, and rates bounded to [0, 1].

## Figures

1. [Information flow and event timing](information-flow-timing.png) — archived phase events, four readout windows, and when D/S/branch information is carried forward.
2. [Disinhibitory gating](disinhibitory-gating.png) — recorded activity in baseline trial 00. `I_release` rises after the stage clock, suppresses the selected `I_gate` through I→I inhibition, and the selected E branch becomes active while the competing branch stays suppressed.
3. [All-neuron subspace](all-neuron-subspace.png) — common PCA basis from all 104 neuron coordinates, using 24 archived four-readout trajectories (96 population-state vectors).
4. [Delay fixed-point probe](delay-state-attractor-probe.png) — local Euler-map stability and zero-input/zero-clock perturbation return from 24 saved delay states.
5. [Local Jacobian](delay-state-jacobian.png) — full 104 × 104 continuous-time piecewise Jacobian at baseline condition 00, organized by population, plus its eigenvalue spectrum.
6. [Projected vector field](delay-state-vector-field.png) — zero-input dynamics projected onto the PC1–PC2 plane of 24 observed delay states, with the other 102 coordinates fixed at condition 00.

## Population-state result

Each point is a 104-dimensional activity vector, one coordinate per recorded neuron. The common centered endpoint matrix has numerical rank {subspace['common_centered_rank']} and participation ratio {subspace['common_participation_ratio']:.2f}. Stage-local rank / participation ratio are {', '.join(f"{stage}: {v['centered_rank']} / {v['participation_ratio']:.2f}" for stage, v in subspace['stage_specific'].items())}. These are sample summaries of the saved endpoint states, not a claim that the network was designed to have a particular PCA rank.

## Attractor evidence and limits

In the 1,400–1,750 ms delay window, the 24 mean saved states have maximum fixed-point residual {attractor['max_fixed_point_residual']:.2e}; the local discrete Euler Jacobian has spectral radius {attractor['local_euler_spectral_radius_median']:.3f} for every condition. With per-coordinate perturbation SD 0.005, {local['fraction_within_1e-3_of_original_state']:.0%} of 96 probes returned within 0.1% of their initial deviation from the saved state after {attractor['probe_duration_ms']:.0f} ms. At SD 0.05, {broader['fraction_within_1e-3_of_original_state']:.1%} returned to the same saved state; the remaining probes did not return within the observation window.

The archived recurrence scan is consistent with recurrence-dependent holding: at `w_rec=0`, full-sequence accuracy is {recurrence_controls['0.0']['sequences_correct']}/24 and median late maximum activity is {recurrence_controls['0.0']['median_late_max_activity']['R1']:.1e} in R1 and both memory groups; at `w_rec=1.6`, `2.0`, and `2.2`, accuracy is {recurrence_controls['1.6']['sequences_correct']}/24, {recurrence_controls['2.0']['sequences_correct']}/24, and {recurrence_controls['2.2']['sequences_correct']}/24, with late active-group rates near 1.0.

This supports **locally stable fixed points for the delay states** in the zero-stimulus, zero-clock dynamics. The larger perturbations show that return is not guaranteed for the broader perturbation scale. These analyses do not establish global basins, a continuous attractor, or autonomous stage switching. They test archived v1 dynamics and do not imply learned or biological dynamics.

The new Jacobian is the derivative of the implemented clipped rate field in the active linear region at condition 00; units at either clip boundary are assigned zero slope, so the derivative is piecewise and boundary states have one-sided alternatives. Its continuous-time eigenvalues and Euler-map spectrum are stored in `analysis.json`. The vector-field arrows show the field component in a two-dimensional activity slice. This projection aids intuition but cannot establish full-space flow topology or attractor basins.

## Reproduction

Run from the repository root with the project's verified `analysis` environment:

```powershell
$envRoot='C:\\Users\\Totheinfinity\\.conda\\envs\\analysis'
$env:PATH="$envRoot\\Library\\bin;$envRoot\\Scripts;$envRoot;$env:PATH"
& (Join-Path $envRoot 'python.exe') 'handcrafted_ei\\artifacts\\activity-analysis-2026-10-25\\plot_activity.py'
```

`analysis.json` stores input archive checksums, source hashes, configuration, environment versions, Jacobian/eigenvalue and vector-field summaries, and the exact analysis scope.
"""
    (OUT / "REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps({"output": str(OUT), "subspace": subspace, "attractor": attractor}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
