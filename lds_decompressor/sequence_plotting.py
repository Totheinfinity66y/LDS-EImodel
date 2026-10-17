"""Whole-sequence line plots and an all-unit heatmap from actual saved rates."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

from .core import PATH_NAMES as PATHS
from .timeline import SequenceTimeline


E_COLORS = ("#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9")
PATH_COLORS = ("#0072B2", "#E69F00", "#009E73", "#CC79A7")


def _boundaries(ax, timeline, *, captions=False):
    times = timeline.rank_times
    for rank in range(3):
        ax.axvspan(times[rank], times[rank + 1], color=("#eaf2f8", "#fff3df", "#eaf2f8")[rank],
                   alpha=0.55, zorder=0)
        if captions:
            ax.text((times[rank] + times[rank + 1]) / 2, 0.97,
                    f"R{rank + 1} -> R{rank + 2}", transform=ax.get_xaxis_transform(),
                    ha="center", va="top", fontsize=10, color="#34495e")
    for time in times[1:-1]:
        ax.axvline(time, color="#64748b", ls="--", lw=0.9, alpha=0.8)
    ax.set_xlim(times[0], times[-1])
    ax.grid(axis="y", alpha=0.15)
    ax.spines[["top", "right"]].set_visible(False)


def _lines(ax, timeline, group, colors, *, held=False):
    indices = np.flatnonzero(timeline.groups == group)
    for index, color in zip(indices, colors):
        ax.plot(timeline.time, timeline.rates[:, index], label=timeline.labels[index], color=color,
                lw=1.7, drawstyle="steps-post" if held else "default")
    ax.legend(loc="upper right", ncol=min(len(indices), 6), fontsize=8,
              framealpha=0.95, handlelength=1.7)
    _boundaries(ax, timeline)


def plot_sequence_artifacts(output: Path):
    output = Path(output)
    timeline = SequenceTimeline.load(output / "sequence_timeline.npz")
    location, direction, step = (int(v) for v in timeline.condition)
    decoded = " -> ".join(f"E{int(site)}" for site in timeline.positions)
    heading = f"Full retrieval: L={location}, D={direction:+d}, S={step} | {decoded}"

    fig, axes = plt.subplots(6, 1, figsize=(15, 12), sharex=True,
                             gridspec_kw={"height_ratios": [2.5, 1.4, 1.2, 1.2, 1.2, 0.9]})
    fig.subplots_adjust(left=0.095, right=0.97, top=0.91, bottom=0.105, hspace=0.25)
    _lines(axes[0], timeline, "Position E", E_COLORS)
    axes[0].get_legend().remove()
    axes[0].legend(loc="lower right", bbox_to_anchor=(1, 1.01), ncol=6,
                   fontsize=9, frameon=False, handlelength=1.7)
    peak = float(timeline.columns("Position E").max())
    axes[0].set_ylim(-0.02, peak * 1.30)
    for rank, (time, site) in enumerate(zip(timeline.rank_times, timeline.positions)):
        axes[0].text(time, peak * 1.13, f"R{rank + 1}: E{int(site)}",
                     ha="left" if rank == 0 else "right" if rank == 3 else "center",
                     fontsize=11, weight="bold", color=E_COLORS[int(site) - 1])
    axes[0].set_ylabel("Position E\nrate")
    axes[0].set_title("A  Six position units on one time axis", loc="left", fontsize=11)

    # Nearest-neighbour sample cells; no smoothing or per-row normalization.
    axes[1].pcolormesh(timeline.time, np.arange(1, 7), timeline.columns("Position E").T,
                       shading="nearest", cmap="viridis", vmin=0, vmax=peak, rasterized=True)
    axes[1].set_yticks(range(1, 7), [f"E{k}" for k in range(1, 7)])
    axes[1].invert_yaxis()
    axes[1].set_ylabel("Position E")
    axes[1].set_title("B  Position activity map (same raw rates)", loc="left", fontsize=10)
    for time in timeline.rank_times[1:-1]:
        axes[1].axvline(time, color="white", ls="--", lw=0.9)
    axes[1].set_xlim(timeline.time[0], timeline.time[-1])

    _lines(axes[2], timeline, "Displacement", PATH_COLORS, held=True)
    axes[2].set_ylabel("Readout\n(held)")
    _lines(axes[3], timeline, "Gate I", PATH_COLORS, held=True)
    axes[3].set_ylabel("Gate I\n(held)")
    _lines(axes[4], timeline, "Relay", E_COLORS)
    axes[4].set_ylabel("Relay M1..M6")
    _lines(axes[5], timeline, "Global I", ("#334155",))
    axes[5].set_ylabel("Global I")
    axes[5].set_xticks(np.arange(0, timeline.time[-1] + 1e-8, 0.2))
    axes[5].set_xlabel("Cumulative E/I integration time after initialization (s)")
    fig.suptitle(heading, fontsize=16, weight="bold", y=0.97)
    fig.text(0.095, 0.025,
             "Readout / gate snapshots are held within each transition; relays reset at dashed boundaries.\n"
             "Initialization and control-setup intervals are excluded. Rates are dimensionless model units.",
             fontsize=10, color="#475569")
    fig.savefig(output / "sequence_dynamics.png", dpi=180)
    fig.savefig(output / "sequence_dynamics.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(15, 14))
    fig.subplots_adjust(left=0.18, right=0.82, top=0.90, bottom=0.105)
    unit_count = len(timeline.labels)
    im = ax.pcolormesh(timeline.time, np.arange(unit_count), timeline.rates.T, shading="nearest",
                       cmap="viridis", vmin=0, vmax=float(timeline.rates.max()), rasterized=True)
    ax.set_yticks(range(unit_count), timeline.labels, fontsize=8.5)
    ax.invert_yaxis()
    starts = np.r_[0, np.flatnonzero(timeline.groups[1:] != timeline.groups[:-1]) + 1]
    ends = np.r_[starts[1:], unit_count]
    for start, end in zip(starts, ends):
        held = timeline.modes[start] == "held"
        color = "#ad5b17" if held else "#156a76"
        for tick in ax.get_yticklabels()[start:end]:
            tick.set_color(color)
        if start:
            ax.axhline(start - 0.5, color="white", lw=1.0)
        ax.text(1.015, (start + end - 1) / 2, timeline.groups[start],
                transform=ax.get_yaxis_transform(), va="center", fontsize=9, color=color)
    for time in timeline.rank_times[1:-1]:
        ax.axvline(time, color="white", ls="--", lw=1.0, alpha=0.9)
    ax.set_xlim(timeline.time[0], timeline.time[-1])
    ax.set_xticks(np.arange(0, timeline.time[-1] + 1e-8, 0.2))
    ax.set_xlabel("Cumulative E/I integration time after initialization (s)", fontsize=11)
    ax.set_ylabel(f"Every scalar rate variable ({unit_count} rows; no per-row rescaling)", fontsize=11)
    top = ax.secondary_xaxis("top")
    top.set_xticks(timeline.rank_times,
                  [f"R{r + 1}: E{int(site)}" for r, site in enumerate(timeline.positions)])
    top.tick_params(labelsize=10, pad=8)
    cax = fig.add_axes([0.925, 0.35, 0.012, 0.30])
    fig.colorbar(im, cax=cax, label="raw rate (model units)")
    fig.suptitle(f"All {unit_count} rate variables | " + decoded, y=0.965, fontsize=17, weight="bold")
    fig.legend(handles=[Patch(color="#156a76", label="Integrated E / I / relay activity"),
                        Patch(color="#ad5b17", label="Held encoding / rank-control snapshots")],
               loc="upper center", bbox_to_anchor=(0.5, 0.945), ncol=2, frameon=False, fontsize=10)
    fig.text(0.18, 0.035,
             "Time starts at the initialized E state. Control setup was not jointly sampled with E/I.\n"
             "Held rows show their actual stored rates; no invented onset dynamics. Relays reset at switches.",
             fontsize=10, color="#475569")
    fig.savefig(output / "all_units_timeline.png", dpi=180)
    fig.savefig(output / "all_units_timeline.pdf")
    plt.close(fig)
    return timeline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "artifacts")
    args = parser.parse_args()
    timeline = plot_sequence_artifacts(args.output)
    print(f"Exported {len(timeline.time)} actual time samples x {len(timeline.labels)} rate units")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
