#!/usr/bin/env python3
"""
run_full_sweep.py
=================
Executes the full CPU scheduler experiment sweeps without interactive prompts:
1. Baseline 500-run experiment sweep (5 VM counts x 5 workloads x 5 seeds x 4 schedulers)
2. Multi-CPU 1500-run experiment sweep (3 CPU configs x 5 VM counts x 5 workloads x 5 seeds x 4 schedulers)
3. Generates all summary CSVs, Markdown reports, plots, and Gantt charts.
"""

import os
import sys

from config import DEFAULT_TIME_QUANTUM, FINAL_EXPERIMENT_SEEDS, VM_COUNT_PRESETS, WORKLOAD_TYPES, DEFAULT_SEED
from models.cpu_config import DEFAULT_CPU_CONFIG, CPU_CONFIG_NAMES
from simulation.workload_generator import generate_workload, fresh_copy
from simulation.simulator import Simulator
from evaluation.experiments import run_full_experiment, build_schedulers
from evaluation.reporting import save_human_readable_summaries
from visualization.plots import generate_all_summary_plots
from visualization.gantt import plot_gantt

RESULTS_DIR = "results"


def run_sweep():
    print("=" * 60)
    print("      STARTING FULL CPU SCHEDULER EXPERIMENT SWEEP")
    print("=" * 60)

    vm_counts = list(VM_COUNT_PRESETS)
    workload_types = list(WORKLOAD_TYPES)
    seeds = list(FINAL_EXPERIMENT_SEEDS)

    # 1. Baseline Experiment (Single CPU Config: x86-like -> 500 scheduler runs)
    print("\n--- [Phase 1/3] Running 500-run Baseline Experiment (x86-like) ---")
    long_df_base, avg_df_base = run_full_experiment(
        vm_counts=vm_counts,
        workload_types=workload_types,
        seeds=seeds,
        cpu_configs=[DEFAULT_CPU_CONFIG],
        verbose=True,
    )

    os.makedirs(RESULTS_DIR, exist_ok=True)
    raw_base_path = os.path.join(RESULTS_DIR, "full_experiment_raw.csv")
    avg_base_path = os.path.join(RESULTS_DIR, "full_experiment_avg.csv")
    long_df_base.to_csv(raw_base_path, index=False)
    avg_df_base.to_csv(avg_base_path, index=False)
    reports_base = save_human_readable_summaries(avg_df_base, RESULTS_DIR, "full_experiment")
    print(f"Saved baseline raw results ({len(long_df_base)} rows) -> {raw_base_path}")
    print(f"Saved baseline averaged results -> {avg_base_path}")
    print(f"Saved baseline overall markdown -> {reports_base['overall_md']}")

    # 2. Full Multi-CPU Architecture Sweep (3 CPU configs -> 1500 scheduler runs)
    print("\n--- [Phase 2/3] Running 1500-run Multi-CPU Comparison Experiment ---")
    long_df_cpu, avg_df_cpu = run_full_experiment(
        vm_counts=vm_counts,
        workload_types=workload_types,
        seeds=seeds,
        cpu_configs=list(CPU_CONFIG_NAMES),
        verbose=True,
    )

    raw_cpu_path = os.path.join(RESULTS_DIR, "cpu_comparison_full_experiment_raw.csv")
    avg_cpu_path = os.path.join(RESULTS_DIR, "cpu_comparison_full_experiment_avg.csv")
    long_df_cpu.to_csv(raw_cpu_path, index=False)
    avg_df_cpu.to_csv(avg_cpu_path, index=False)
    reports_cpu = save_human_readable_summaries(avg_df_cpu, RESULTS_DIR, "cpu_comparison_full_experiment")
    print(f"Saved multi-CPU raw results ({len(long_df_cpu)} rows) -> {raw_cpu_path}")
    print(f"Saved multi-CPU averaged results -> {avg_cpu_path}")
    print(f"Saved multi-CPU overall markdown -> {reports_cpu['overall_md']}")

    # 3. Generating Visualization Plots & Gantt Charts
    print("\n--- [Phase 3/3] Generating Visualizations (Plots & Gantt Charts) ---")
    plot_paths = generate_all_summary_plots(avg_df_cpu, outdir=RESULTS_DIR)
    print(f"Generated {len(plot_paths)} summary plots in {RESULTS_DIR}/")

    # Generate Gantt charts for a representative sample (8 VMs, normal workload, seed 42)
    sample_vms = generate_workload(8, "normal", DEFAULT_SEED)
    schedulers = build_schedulers(debug=False, seed=DEFAULT_SEED)
    for name, sched in schedulers.items():
        sim = Simulator(quantum=DEFAULT_TIME_QUANTUM, debug=True)
        result = sim.run(fresh_copy(sample_vms), sched, scheduler_name=name)
        safe_name = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        gantt_path = plot_gantt(result, f"Gantt Chart - {name} (normal, 8 VMs)",
                                outdir=RESULTS_DIR, filename=f"gantt_{safe_name}.png")
        print(f"Generated Gantt chart for {name} -> {gantt_path}")

    print("\n" + "=" * 60)
    print("      ALL SWEEPS AND VISUALIZATIONS COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    run_sweep()
