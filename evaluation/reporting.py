"""Human-readable summaries generated from actual experiment result frames."""

import os


DISPLAY_COLUMNS = [
    "scheduler", "avg_waiting_time", "avg_turnaround_time", "avg_response_time",
    "cpu_utilization", "throughput", "deadline_miss_rate",
    "fairness_jain_index", "estimated_energy", "context_switches",
    "estimated_scheduling_overhead",
]


def _write_markdown_table(frame, path, title):
    columns = list(frame.columns)
    rows = frame.astype(object).where(frame.notna(), "").values.tolist()
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"# {title}\n\n")
        handle.write("All values are calculated from simulator output. Energy and scheduling overhead are estimated proxies, not physical measurements.\n\n")
        handle.write("| " + " | ".join(columns) + " |\n")
        handle.write("| " + " | ".join("---" for _ in columns) + " |\n")
        for row in rows:
            values = [str(value).replace("|", "\\|") for value in row]
            handle.write("| " + " | ".join(values) + " |\n")
        handle.write("\n")


def save_human_readable_summaries(avg_df, outdir="results", prefix="full_experiment"):
    """Save overall and workload-level scheduler summaries as CSV and Markdown."""
    os.makedirs(outdir, exist_ok=True)
    metric_cols = [column for column in DISPLAY_COLUMNS if column != "scheduler"]

    overall = avg_df.groupby("scheduler", as_index=False)[metric_cols].mean()
    overall = overall[DISPLAY_COLUMNS].sort_values("scheduler")
    by_workload = avg_df[["workload_type", "num_vms", *DISPLAY_COLUMNS]].sort_values(
        ["workload_type", "num_vms", "scheduler"]
    )

    outputs = {
        "overall_csv": os.path.join(outdir, f"{prefix}_overall_summary.csv"),
        "overall_md": os.path.join(outdir, f"{prefix}_overall_summary.md"),
        "by_workload_csv": os.path.join(outdir, f"{prefix}_by_workload_summary.csv"),
        "by_workload_md": os.path.join(outdir, f"{prefix}_by_workload_summary.md"),
    }
    overall.to_csv(outputs["overall_csv"], index=False, float_format="%.4f")
    by_workload.to_csv(outputs["by_workload_csv"], index=False, float_format="%.4f")
    _write_markdown_table(overall.round(4), outputs["overall_md"], "Overall Scheduler Summary")
    _write_markdown_table(by_workload.round(4), outputs["by_workload_md"], "Scheduler Summary by Workload and VM Count")
    return outputs
