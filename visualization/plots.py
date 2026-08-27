"""
visualization/plots.py
========================
Publication-style comparison plots (matplotlib), saved as high-res PNGs.
All figures are generated from real DataFrames produced by
evaluation/experiments.py -- nothing is hand-drawn or hard-coded.
"""

import os
import matplotlib.pyplot as plt

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
        ("estimated_energy", "Estimated Energy Consumption", "Energy units (est.)", "estimated_energy.png"),
    ]

    for metric, title, ylabel, fname in metric_specs:
        paths.append(bar_comparison(avg_df, metric, f"{title} (overall average)", ylabel, outdir, fname))
        paths.append(line_vs_vms(avg_df, metric, ylabel, f"{title} vs. Number of VMs", outdir,
                                  fname.replace(".png", "_vs_vms.png")))
        paths.append(line_vs_workload(avg_df, metric, ylabel, f"{title} vs. Workload Intensity", outdir,
                                       fname.replace(".png", "_vs_workload.png")))

    return paths
