"""Scientific figures from exported actual arrays; no model execution or smoothing."""

import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Patch
import numpy as np

E_COLORS = ("#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9")
PATH_COLORS = ("#0072B2", "#E69F00", "#009E73", "#CC79A7")


def _save_pair(fig, base):
    fig.savefig(base.with_suffix(".png"), dpi=160)
    fig.savefig(base.with_suffix(".pdf"))


def _title(data, index):
    l, d, s = (int(x) for x in data["conditions"][index])
    seq = " -> ".join(f"E{x}" for x in data["positions"][index])
    return f"L={l}, D={d:+d}, S={s} | {seq}"


def _all_unit_figure(data, index, vmax):
    fig, ax = plt.subplots(figsize=(15, 10.8))
    fig.subplots_adjust(left=.15, right=.79, top=.86, bottom=.115)
    values = data["rates"][index]
    im = ax.pcolormesh(data["time"], np.arange(29), values.T, shading="nearest",
                       cmap="viridis", vmin=0, vmax=vmax, rasterized=True)
    ax.set_yticks(range(29), data["labels"], fontsize=9)
    ax.invert_yaxis()
    starts = np.r_[0, np.flatnonzero(data["groups"][1:] != data["groups"][:-1]) + 1]
    ends = np.r_[starts[1:], 29]
    for a, b in zip(starts, ends):
        color = "#ad5b17" if data["modes"][a] == "held" else "#156a76"
        for tick in ax.get_yticklabels()[a:b]:
            tick.set_color(color)
        if a:
            ax.axhline(a - .5, color="white", lw=1)
        ax.text(1.015, (a + b - 1) / 2, data["groups"][a],
                transform=ax.get_yaxis_transform(), va="center", fontsize=10, color=color)
    for t in data["rank_times"][1:-1]:
        ax.axvline(t, color="white", ls="--", lw=1, alpha=.9)
    ax.set_xlim(0, data["time"][-1])
    ax.set_xticks(np.arange(0, data["time"][-1] + 1e-6, .2))
    ax.set_xlabel("Retrieval time after position initialization (s)", fontsize=11)
    ax.set_ylabel("Every rate variable (29 rows; no row rescaling)", fontsize=11)
    top = ax.secondary_xaxis("top")
    top.set_xticks(data["rank_times"],
                  [f"R{k + 1}: E{int(x)}" for k, x in enumerate(data["positions"][index])])
    top.tick_params(pad=8, labelsize=11)
    cax = fig.add_axes([.925, .32, .012, .34])
    fig.colorbar(im, cax=cax, label="Raw rate (model units)")
    fig.suptitle("All 29 rate variables | " + _title(data, index), fontsize=16, weight="bold", y=.969)
    fig.legend(handles=[Patch(color="#156a76", label="21 synchronously integrated rates"),
                        Patch(color="#ad5b17", label="8 held encoding rates")],
               loc="upper center", bbox_to_anchor=(.5, .943), ncol=2, frameon=False, fontsize=11)
    fig.text(.15, .025,
             "V/G/E/I carry across rank boundaries; shared M resets. All conditions use this same raw-rate color scale.\n"
             "D/S/J are actual held rates. M is an effective shared drive; branch rectifications are not extra plotted neurons.",
             fontsize=10, color="#475569")
    return fig


def _boundaries(ax, data):
    for t in data["rank_times"][1:-1]:
        ax.axvline(t, color="#64748b", ls="--", lw=.8)
    ax.set_xlim(0, data["time"][-1])
    ax.grid(axis="y", alpha=.15)
    ax.spines[["top", "right"]].set_visible(False)


def _line_group(ax, data, index, group, colors):
    columns = np.flatnonzero(data["groups"] == group)
    for col, color in zip(columns, colors):
        ax.plot(data["time"], data["rates"][index, :, col], color=color,
                label=data["labels"][col], lw=1.4)
    ax.legend(loc="upper right", ncol=min(len(columns), 6), fontsize=8, framealpha=.9)
    _boundaries(ax, data)


def _sequence_figure(data, output):
    index = 1
    fig, axes = plt.subplots(7, 1, figsize=(15, 16), sharex=True,
                             gridspec_kw={"height_ratios": [2.2, 1.3, 1.3, 1.3, 1.3, 1, 1.3]})
    fig.subplots_adjust(left=.10, right=.97, top=.92, bottom=.075, hspace=.32)
    fig.suptitle("Continuous competitive retrieval | " + _title(data, index),
                 fontsize=16, weight="bold", y=.975)
    _line_group(axes[0], data, index, "Position E", E_COLORS)
    axes[0].legend(loc="lower right", bbox_to_anchor=(1, 1.015),
                   ncol=6, fontsize=8, frameon=False)
    peak = data["rates"][index, :, data["groups"] == "Position E"].max()
    axes[0].set_ylim(-.02, peak * 1.3)
    for k, (t, site) in enumerate(zip(data["rank_times"], data["positions"][index])):
        axes[0].text(t, peak * 1.14, f"R{k + 1}: E{int(site)}", fontsize=11, weight="bold",
                     ha="left" if k == 0 else "right" if k == 3 else "center")
    axes[0].set_ylabel("Position E\nraw rate")
    axes[0].set_title("A  Six position rates", loc="left", fontsize=11)
    position = data["rates"][index][:, data["groups"] == "Position E"]
    axes[1].pcolormesh(data["time"], np.arange(1, 7), position.T,
                       shading="nearest", cmap="viridis", vmin=0, vmax=peak, rasterized=True)
    axes[1].set_yticks(range(1, 7), [f"E{k}" for k in range(1, 7)])
    axes[1].invert_yaxis()
    axes[1].set_ylabel("Position E")
    axes[1].set_title("B  Same unnormalized position rates", loc="left", fontsize=10)
    for t in data["rank_times"][1:-1]:
        axes[1].axvline(t, color="white", ls="--", lw=.8)
    _line_group(axes[2], data, index, "Readout V", PATH_COLORS)
    axes[2].set_ylabel("Readout V")
    axes[2].set_title("C  Readout competition (integrated)", loc="left", fontsize=10)
    _line_group(axes[3], data, index, "Gate G", PATH_COLORS)
    axes[3].set_ylabel("Gate G")
    axes[3].set_title("D  Inhibitory gates (integrated)", loc="left", fontsize=10)
    _line_group(axes[4], data, index, "Shared M", E_COLORS)
    axes[4].set_ylabel("Shared M")
    axes[4].set_title("E  Six effective relay rates", loc="left", fontsize=10)
    _line_group(axes[5], data, index, "Global I", ("#334155",))
    axes[5].set_ylabel("Global I")
    axes[5].set_title("F  Total-activity inhibitory feedback", loc="left", fontsize=10)
    # Right-continuous joining matches the raw-rate timeline exactly.
    targets = data["branch_target"][index].sum(axis=3)
    targets = np.concatenate([targets[0, :-1], targets[1, :-1], targets[2]])
    for k, color in enumerate(PATH_COLORS):
        axes[6].plot(data["time"], targets[:, k], color=color,
                     label=("CW1", "CW2", "CCW1", "CCW2")[k], lw=1.4)
    axes[6].legend(loc="upper right", ncol=4, fontsize=8)
    _boundaries(axes[6], data)
    axes[6].set_ylabel("Branch drive\nsum (derived)")
    axes[6].set_title("G  Rectified pathway drives, including transient leakage", loc="left", fontsize=10)
    axes[6].set_xticks(np.arange(0, data["time"][-1] + 1e-6, .2))
    axes[6].set_xlabel("Retrieval time after position initialization (s)")
    fig.text(.10, .018,
             "Raw, unsmoothed model rates. E/I/V/G continue; only M resets at dashed rank boundaries.\n"
             "Panel G shows algebraic branch drives, not additional rate neurons. Initialization and held-encoding setup are excluded.",
             fontsize=10, color="#475569")
    _save_pair(fig, output / "sequence_dynamics")
    plt.close(fig)


def _encoding_figures(data, output):
    conditions = ["D=+1, S=1", "D=+1, S=2", "D=-1, S=1", "D=-1, S=2"]
    names = ["CW1", "CW2", "CCW1", "CCW2"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), constrained_layout=True)
    for ax, key, title in zip(axes, ("joint_rates", "joint_activity"),
                              ("Actual joint raw rates", "Joint activity (sum-normalized diagnostic)")):
        im = ax.imshow(data[key][:4], vmin=0, vmax=1, cmap="viridis", aspect="auto", interpolation="nearest")
        ax.set_xticks(range(4), names)
        ax.set_yticks(range(4), conditions)
        ax.set_title(title, fontsize=11)
        fig.colorbar(im, ax=ax, fraction=.046)
    fig.suptitle("Four D/S joint tuning conditions (encoding snapshots)", fontsize=14)
    _save_pair(fig, output / "joint_tuning")
    plt.close(fig)
    fig, axes = plt.subplots(2, 3, figsize=(14, 7), constrained_layout=True)
    for col, (group, labels) in enumerate((("direction", ["CW", "CCW"]),
                                           ("step", ["S1", "S2"]), ("joint", names))):
        for row, key in enumerate(("rates", "activity")):
            im = axes[row, col].imshow(data[f"{group}_{key}"][:4], vmin=0, vmax=1,
                                       cmap="viridis", aspect="auto", interpolation="nearest")
            axes[row, col].set_xticks(range(len(labels)), labels)
            axes[row, col].set_yticks(range(4), conditions)
            axes[row, col].set_title(f"{group.title()}: {'raw rate' if row == 0 else 'normalized activity'}")
    fig.colorbar(im, ax=axes.ravel().tolist(), fraction=.018, label="Value")
    fig.suptitle("Encoding rates and explicitly normalized diagnostics", fontsize=14)
    _save_pair(fig, output / "encoding_activity")
    plt.close(fig)


def plot_artifacts(output):
    output = Path(output)
    with np.load(output / "activities.npz", allow_pickle=False) as stored:
        data = dict(stored)
    folder = output / "all_conditions"
    folder.mkdir(exist_ok=True)
    vmax = float(data["rates"].max())
    index_lines = ["# 全部24条件的29率变量原始活动", "", "各图共用原始率色标，不逐行归一化。", ""]
    with PdfPages(output / "all_conditions_rates.pdf") as pdf:
        for index, (l, d, s) in enumerate(data["conditions"]):
            name = f"L{l}_D{'CW' if d == 1 else 'CCW'}_S{s}.png"
            fig = _all_unit_figure(data, index, vmax)
            fig.savefig(folder / name, dpi=150)
            pdf.savefig(fig)
            if index == 1:
                _save_pair(fig, output / "all_units_timeline")
            plt.close(fig)
            index_lines.append(f"- [{_title(data, index)}]({name})")
    (folder / "INDEX.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    _sequence_figure(data, output)
    _encoding_figures(data, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "artifacts")
    args = parser.parse_args()
    plot_artifacts(args.output)


if __name__ == "__main__":
    main()
