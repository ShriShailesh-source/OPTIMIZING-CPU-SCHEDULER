"""
visualization/gantt.py
========================
Generates a Gantt chart showing scheduling order/execution slices for one
representative workload run under a given scheduler.

We reuse Simulator's debug decision_log (populated when Simulator(debug=True)
is used), which records (time, selected_vm, run_time) for every quantum
slice actually executed -- so the chart reflects the real run, not a
reconstruction.
"""

import os
from matplotlib import colormaps
import matplotlib.pyplot as plt


def plot_gantt(sim_result, title, outdir="results", filename="gantt.png"):
    log = sim_result.decision_log
    if not log:
        raise ValueError("SimulationResult has no decision_log -- rerun Simulator with debug=True")

    vm_ids = sorted({entry["vm_id"] for entry in log})
    cmap = colormaps["tab20"].resampled(max(len(vm_ids), 1))
    color_map = {vid: cmap(i) for i, vid in enumerate(vm_ids)}

    fig, ax = plt.subplots(figsize=(12, max(3, len(vm_ids) * 0.35)))
    y_pos = {vid: i for i, vid in enumerate(vm_ids)}

    for entry in log:
        start = entry["start_time"]
        dur = entry["duration"]
        vid = entry["vm_id"]
        ax.barh(y_pos[vid], dur, left=start, height=0.6,
                color=color_map[vid], edgecolor="black", linewidth=0.4)

    ax.set_yticks(list(y_pos.values()))
    ax.set_yticklabels([f"VM {vid}" for vid in y_pos.keys()])
    ax.set_xlabel("Time (ticks)")
    ax.set_xlim(0, sim_result.total_time)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()

    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, filename)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path
