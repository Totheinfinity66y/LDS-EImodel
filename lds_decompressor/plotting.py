"""Static scientific figures drawn only from saved actual circuit activity."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .core import PATH_NAMES as PATHS


CONDITIONS = ("D=+1,S=1", "D=+1,S=2", "D=-1,S=1", "D=-1,S=2")


def _heat(ax, data, xticks, yticks, title, *, vmax=1):
    picture = ax.imshow(data, vmin=0, vmax=vmax, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(xticks)), xticks, rotation=35, ha="right")
    ax.set_yticks(range(len(yticks)), yticks)
    ax.set_title(title, fontsize=11)
    for (row, col), value in np.ndenumerate(data):
        ax.text(col, row, f"{value:.3f}", ha="center", va="center", fontsize=8,
                color="black" if value > vmax * 0.55 else "white")
    return picture


def _save(fig, output, name):
    fig.savefig(output / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_artifacts(output: Path):
    with np.load(output / "activities.npz", allow_pickle=False) as data:
        fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
        for ax, key, title in zip(axes, ("joint_raw", "joint_activity"),
                                  ("Joint raw product drive", "Joint normalized activity")):
            im = _heat(ax, data[key], [f"J_{p}" for p in PATHS], CONDITIONS, title)
        fig.colorbar(im, ax=axes, label="dimensionless activity", shrink=0.8)
        _save(fig, output, "joint_tuning.png")

        fig, axes = plt.subplots(2, 3, figsize=(13, 7), layout="constrained")
        for col, (name, names) in enumerate((("direction", ("D_CW", "D_CCW")),
                                            ("step", ("S1", "S2")),
                                            ("joint", PATHS))):
            _heat(axes[0, col], data[f"{name}_rates"], names, CONDITIONS, f"{name}: raw rates")
            _heat(axes[1, col], data[f"{name}_activity"], names, CONDITIONS, f"{name}: normalized")
        _save(fig, output, "encoding_activity.png")

        # Same output for all L; choose real L=1 traces, not inferred labels.
        fig, axes = plt.subplots(2, 3, figsize=(13, 7), layout="constrained")
        for rank in range(3):
            _heat(axes[0, rank], data["displacement_activity"][:4, rank], PATHS, CONDITIONS,
                  f"Transition {rank + 1}: displacement readout")
            _heat(axes[1, rank], data["gate_i_rates"][:4, rank], PATHS, CONDITIONS,
                  f"Transition {rank + 1}: inhibitory gate rates")
        _save(fig, output, "rank_readout.png")

        fig, axes = plt.subplots(3, 3, figsize=(13, 8), layout="constrained")
        time = data["example_time"]
        for rank in range(3):
            axes[0, rank].plot(time, data["example_e"][rank])
            axes[0, rank].set_title(f"Rank {rank + 1} -> {rank + 2}: E1..E6")
            axes[1, rank].plot(time, data["example_i"][rank], color="black", label="I_global")
            axes[1, rank].legend(fontsize=8)
            for path, name in enumerate(PATHS):
                axes[2, rank].plot(time, data["example_relays"][rank, :, path].sum(axis=1), label=name)
            axes[2, rank].legend(fontsize=8, ncol=2)
            axes[2, rank].set_xlabel("seconds within transition")
        axes[0, 0].set_ylabel("E rate (model units)")
        axes[1, 0].set_ylabel("global I rate")
        axes[2, 0].set_ylabel("relay rate sum")
        decoded = " -> ".join(str(int(site)) for site in data["positions"][1])
        fig.suptitle(f"Actual dynamics: L=1, D=+1, S=2; decoded {decoded}")
        _save(fig, output, "ei_dynamics.png")

    from .sequence_plotting import plot_sequence_artifacts
    plot_sequence_artifacts(output)
