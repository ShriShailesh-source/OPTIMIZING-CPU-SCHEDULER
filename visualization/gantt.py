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
from html import escape

try:
    from matplotlib import colormaps
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - used when a plotting backend is unavailable
    colormaps = None
    plt = None


def plot_gantt(sim_result, title, outdir="results", filename="gantt.png"):
    log = sim_result.decision_log
    if not log:
        raise ValueError("SimulationResult has no decision_log -- rerun Simulator with debug=True")

    if plt is None:
        return _plot_gantt_svg(sim_result, title, outdir, filename)

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


def _plot_gantt_svg(sim_result, title, outdir, filename):
    """Dependency-free Gantt export that uses the engine's real decision log."""
    vm_ids = sorted({entry["vm_id"] for entry in sim_result.decision_log})
    width, row_h, left, right, top, bottom = 1200, 42, 110, 40, 75, 70
    height = top + bottom + row_h * len(vm_ids)
    plot_w = width - left - right
    colors = ["#4a7fb5", "#e0a13c", "#c0392b", "#6a9c5b", "#7b61a8", "#777777"]
    y_pos = {vm_id: top + index * row_h for index, vm_id in enumerate(vm_ids)}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="35" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold">{escape(title)}</text>',
        f'<line x1="{left}" y1="{top + row_h * len(vm_ids)}" x2="{left + plot_w}" y2="{top + row_h * len(vm_ids)}" stroke="black"/>',
    ]
    for vm_id in vm_ids:
        y = y_pos[vm_id]
        parts.append(f'<text x="{left - 10}" y="{y + 25}" text-anchor="end" font-family="Arial" font-size="13">VM {vm_id}</text>')
        parts.append(f'<line x1="{left}" y1="{y + row_h}" x2="{left + plot_w}" y2="{y + row_h}" stroke="#dddddd"/>')
    for entry in sim_result.decision_log:
        x = left + plot_w * entry["start_time"] / sim_result.total_time
        bar_w = plot_w * entry["duration"] / sim_result.total_time
        y = y_pos[entry["vm_id"]] + 7
        color = colors[vm_ids.index(entry["vm_id"]) % len(colors)]
        parts.append(f'<rect x="{x:.2f}" y="{y}" width="{bar_w:.2f}" height="{row_h - 14}" fill="{color}"/>')
    parts.append(f'<text x="{left + plot_w / 2}" y="{height - 18}" text-anchor="middle" font-family="Arial" font-size="14">Time (ticks)</text>')
    parts.append('</svg>')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, filename.replace(".png", ".svg"))
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(parts))
    return path
