"""
visualization/plots.py
========================
Publication-style comparison plots (matplotlib), saved as high-res PNGs.
All figures are generated from real DataFrames produced by
evaluation/experiments.py -- nothing is hand-drawn or hard-coded.
"""

import os
from html import escape

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - used when a plotting backend is unavailable
    plt = None

SCHEDULER_ORDER = ["PRR", "PRM", "Contextual Bandit RL", "Proposed Hybrid"]
COLORS = {
    "PRR": "#8c8c8c",
    "PRM": "#4a7fb5",
    "Contextual Bandit RL": "#e0a13c",
    "Proposed Hybrid": "#c0392b",
}


def _ordered(df, col="scheduler"):
    present = [s for s in SCHEDULER_ORDER if s in df[col].unique()]
    return present


def save_fig(fig, outdir, filename):
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, filename)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def bar_comparison(df, metric, title, ylabel, outdir, filename):
    """Bar chart of `metric` averaged per scheduler (across whatever rows
    are in `df` -- caller decides the slice, e.g. one workload/vm-count)."""
    order = _ordered(df)
    means = df.groupby("scheduler")[metric].mean().reindex(order)

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(order, means.values, color=[COLORS.get(s, "#333") for s in order])
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(order, rotation=15, ha="right")
    for b, v in zip(bars, means.values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}",
                ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    return save_fig(fig, outdir, filename)


def line_vs_vms(avg_df, metric, ylabel, title, outdir, filename, workload_type=None):
    """Line plot of `metric` vs num_vms, one line per scheduler, optionally
    filtered to a single workload_type (else averaged across all present)."""
    df = avg_df.copy()
    if workload_type:
        df = df[df["workload_type"] == workload_type]

    fig, ax = plt.subplots(figsize=(7.5, 5))
    for sched in _ordered(df):
        sub = df[df["scheduler"] == sched].groupby("num_vms")[metric].mean().sort_index()
        ax.plot(sub.index, sub.values, marker="o", label=sched, color=COLORS.get(sched))
    ax.set_xlabel("Number of VMs")
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return save_fig(fig, outdir, filename)


def line_vs_workload(avg_df, metric, ylabel, title, outdir, filename, num_vms=None):
    """Line/point plot of `metric` vs workload_type, one series per scheduler."""
    df = avg_df.copy()
    if num_vms:
        df = df[df["num_vms"] == num_vms]

    workload_order = [w for w in ["light", "normal", "cpu_heavy", "bursty", "mixed"]
                       if w in df["workload_type"].unique()]

    fig, ax = plt.subplots(figsize=(7.5, 5))
    for sched in _ordered(df):
        sub = df[df["scheduler"] == sched].groupby("workload_type")[metric].mean()
        sub = sub.reindex(workload_order)
        ax.plot(workload_order, sub.values, marker="s", label=sched, color=COLORS.get(sched))
    ax.set_xlabel("Workload intensity")
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return save_fig(fig, outdir, filename)


def line_vs_cpu(avg_df, metric, ylabel, title, outdir, filename):
    """Compare a metric across the explicitly simulated CPU configurations."""
    cpu_order = [name for name in ["ARM-like", "x86-like", "RISC-V-like"]
                 if name in avg_df["cpu_config"].unique()]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for sched in _ordered(avg_df):
        sub = avg_df[avg_df["scheduler"] == sched].groupby("cpu_config")[metric].mean()
        sub = sub.reindex(cpu_order)
        ax.plot(cpu_order, sub.values, marker="o", label=sched, color=COLORS.get(sched))
    ax.set_xlabel("Simulated CPU configuration")
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return save_fig(fig, outdir, filename)


def generate_all_summary_plots(avg_df, outdir="results"):
    """Generates the full required set of comparison graphs from an averaged
    experiment DataFrame (as returned by run_full_experiment)."""
    paths = []

    metric_specs = [
        ("avg_waiting_time", "Average Waiting Time", "Ticks", "avg_waiting_time.png"),
        ("avg_turnaround_time", "Average Turnaround Time", "Ticks", "avg_turnaround_time.png"),
        ("avg_response_time", "Average Response Time", "Ticks", "avg_response_time.png"),
        ("cpu_utilization", "CPU Utilization", "Fraction", "cpu_utilization.png"),
        ("throughput", "Throughput", "VMs / tick", "throughput.png"),
        ("deadline_misses", "Deadline Misses", "Count", "deadline_misses.png"),
        ("deadline_miss_rate", "Deadline Miss Rate", "Fraction", "deadline_miss_rate.png"),
        ("fairness_jain_index", "Jain Fairness Index", "Fraction (1 = fairest)", "fairness_jain_index.png"),
        ("estimated_energy", "Estimated Energy Consumption", "Energy units (est.)", "estimated_energy.png"),
        ("context_switches", "Context Switches", "Count", "context_switches.png"),
        ("estimated_scheduling_overhead", "Estimated Scheduling Overhead", "Ticks (est.)", "estimated_scheduling_overhead.png"),
    ]

    if plt is None:
        return _generate_svg_summary_plots(avg_df, metric_specs, outdir)

    for metric, title, ylabel, fname in metric_specs:
        paths.append(bar_comparison(avg_df, metric, f"{title} (overall average)", ylabel, outdir, fname))
        paths.append(line_vs_vms(avg_df, metric, ylabel, f"{title} vs. Number of VMs", outdir,
                                  fname.replace(".png", "_vs_vms.png")))
        paths.append(line_vs_workload(avg_df, metric, ylabel, f"{title} vs. Workload Intensity", outdir,
                                       fname.replace(".png", "_vs_workload.png")))
        if "cpu_config" in avg_df.columns:
            paths.append(line_vs_cpu(avg_df, metric, ylabel, f"{title} vs. Simulated CPU", outdir,
                                     fname.replace(".png", "_vs_cpu.png")))

    return paths


def _svg_path(outdir, filename):
    os.makedirs(outdir, exist_ok=True)
    return os.path.join(outdir, filename.replace(".png", ".svg"))


def _write_svg_chart(path, title, ylabel, categories, series, chart_type):
    """Dependency-free SVG fallback for final-review charts.

    It exports the same actual DataFrame values when matplotlib cannot load in
    a restricted runtime; no values are invented or altered.
    """
    width, height = 1000, 620
    left, right, top, bottom = 100, 40, 70, 130
    plot_w, plot_h = width - left - right, height - top - bottom
    values = [value for points in series.values() for value in points]
    y_max = max(values) if values else 1.0
    y_max = y_max * 1.1 if y_max > 0 else 1.0
    colors = ["#555555", "#4a7fb5", "#e0a13c", "#c0392b"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="35" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold">{escape(title)}</text>',
        f'<text x="25" y="{top + plot_h / 2}" transform="rotate(-90 25 {top + plot_h / 2})" text-anchor="middle" font-family="Arial" font-size="14">{escape(ylabel)}</text>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="black"/>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="black"/>',
    ]
    for tick in range(6):
        value = y_max * tick / 5
        y = top + plot_h - plot_h * tick / 5
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#dddddd"/>')
        parts.append(f'<text x="{left - 10}" y="{y + 5:.1f}" text-anchor="end" font-family="Arial" font-size="12">{value:.3g}</text>')
    n_categories = max(len(categories), 1)
    n_series = max(len(series), 1)
    for index, category in enumerate(categories):
        x = left + plot_w * (index + 0.5) / n_categories
        parts.append(f'<text x="{x:.1f}" y="{top + plot_h + 25}" text-anchor="middle" font-family="Arial" font-size="12">{escape(str(category))}</text>')
    for series_index, (name, points) in enumerate(series.items()):
        color = colors[series_index % len(colors)]
        if chart_type == "bar":
            group_width = plot_w / n_categories * 0.72
            bar_width = group_width / n_series
            for index, value in enumerate(points):
                x = left + plot_w * (index + 0.5) / n_categories - group_width / 2 + series_index * bar_width
                bar_h = plot_h * value / y_max
                y = top + plot_h - bar_h
                parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width - 2:.1f}" height="{bar_h:.1f}" fill="{color}"/>')
        else:
            coords = []
            for index, value in enumerate(points):
                x = left + plot_w * (index + 0.5) / n_categories
                y = top + plot_h - plot_h * value / y_max
                coords.append(f'{x:.1f},{y:.1f}')
            parts.append(f'<polyline points="{" ".join(coords)}" fill="none" stroke="{color}" stroke-width="2.5"/>')
            for coord in coords:
                x, y = coord.split(",")
                parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>')
        legend_x = left + series_index * 190
        parts.append(f'<rect x="{legend_x}" y="{height - 55}" width="14" height="14" fill="{color}"/>')
        parts.append(f'<text x="{legend_x + 20}" y="{height - 43}" font-family="Arial" font-size="12">{escape(name)}</text>')
    parts.append('</svg>')
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(parts))


def _generate_svg_summary_plots(avg_df, metric_specs, outdir):
    paths = []
    for metric, title, ylabel, filename in metric_specs:
        overall = avg_df.groupby("scheduler")[metric].mean()
        schedulers = _ordered(avg_df)
        path = _svg_path(outdir, filename)
        _write_svg_chart(path, f"{title} (overall average)", ylabel, schedulers,
                         {"Average": [overall[s] for s in schedulers]}, "bar")
        paths.append(path)

        vm_counts = sorted(avg_df["num_vms"].unique())
        by_vm = {scheduler: [avg_df[(avg_df["scheduler"] == scheduler) & (avg_df["num_vms"] == count)][metric].mean()
                              for count in vm_counts] for scheduler in schedulers}
        path = _svg_path(outdir, filename.replace(".png", "_vs_vms.png"))
        _write_svg_chart(path, f"{title} vs. Number of VMs", ylabel, vm_counts, by_vm, "line")
        paths.append(path)

        workloads = [w for w in ["light", "normal", "cpu_heavy", "bursty", "mixed"]
                     if w in avg_df["workload_type"].unique()]
        by_workload = {scheduler: [avg_df[(avg_df["scheduler"] == scheduler) & (avg_df["workload_type"] == workload)][metric].mean()
                                    for workload in workloads] for scheduler in schedulers}
        path = _svg_path(outdir, filename.replace(".png", "_vs_workload.png"))
        _write_svg_chart(path, f"{title} vs. Workload Intensity", ylabel, workloads, by_workload, "line")
        paths.append(path)
    return paths
