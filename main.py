#!/usr/bin/env python3
"""
main.py
=======
Command-line interface for the CPU Scheduling Simulator.

    python main.py

then follow the on-screen menu, or call the underlying functions directly
from a script / notebook -- see README.md for examples.
"""

import os
import sys

from config import (
    DEFAULT_TIME_QUANTUM,
    DEFAULT_SEED,
    FINAL_EXPERIMENT_SEEDS,
    VM_COUNT_PRESETS,
    WORKLOAD_TYPES,
)
from models.cpu_config import CPU_CONFIG_NAMES, DEFAULT_CPU_CONFIG
from simulation.workload_generator import generate_workload, fresh_copy
from simulation.simulator import Simulator
from evaluation.metrics import compute_metrics
from evaluation.experiments import run_single_comparison, run_full_experiment, build_schedulers
from evaluation.reporting import save_human_readable_summaries
from visualization.plots import generate_all_summary_plots
from visualization.gantt import plot_gantt

RESULTS_DIR = "results"
SUMMARY_COLUMNS = [
    "cpu_config", "scheduler", "num_vms", "workload_type", "avg_waiting_time",
    "avg_turnaround_time", "avg_response_time", "cpu_utilization",
    "throughput", "deadline_misses", "deadline_miss_rate",
    "fairness_jain_index", "estimated_energy", "context_switches",
    "estimated_scheduling_overhead",
]
SUMMARY_LABELS = {
    "num_vms": "VM Count",
    "workload_type": "Workload",
    "avg_waiting_time": "Average Waiting Time",
    "avg_turnaround_time": "Average Turnaround Time",
    "avg_response_time": "Average Response Time",
    "cpu_utilization": "CPU Utilization",
    "throughput": "Throughput",
    "deadline_misses": "Deadline Misses",
    "deadline_miss_rate": "Deadline Miss Rate",
    "fairness_jain_index": "Fairness",
    "estimated_energy": "Estimated Energy",
    "context_switches": "Context Switches",
    "estimated_scheduling_overhead": "Scheduling Overhead",
}


def ask_int(prompt, default):
    raw = input(f"{prompt} [{default}]: ").strip()
    return int(raw) if raw else default


def ask_choice(prompt, choices, default):
    print(f"{prompt} ({'/'.join(choices)}) [{default}]: ", end="")
    raw = input().strip()
    return raw if raw in choices else default


def print_experiment_config(vm_counts, workload_types, seeds, cpu_configs=CPU_CONFIG_NAMES):
    print("\n=== Experiment Configuration ===")
    print(f"VM counts: {', '.join(map(str, vm_counts))}")
    print(f"Workloads: {', '.join(workload_types)}")
    print(f"Seeds: {', '.join(map(str, seeds))}")
    print(f"CPU configurations: {', '.join(cpu_configs)} (simulated)")
    print("Schedulers: PRR, PRM, Contextual Bandit RL, Proposed Hybrid")


def save_experiment_results(long_df, avg_df, prefix):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    raw_path = os.path.join(RESULTS_DIR, f"{prefix}_raw.csv")
    summary_path = os.path.join(RESULTS_DIR, f"{prefix}_avg.csv")
    long_df.to_csv(raw_path, index=False)
    avg_df.to_csv(summary_path, index=False)
    reports = save_human_readable_summaries(avg_df, RESULTS_DIR, prefix)

    display_df = avg_df[SUMMARY_COLUMNS].rename(columns=SUMMARY_LABELS)
    print("\n=== Averaged Summary ===")
    print(display_df.to_string(index=False))
    print(f"\nRaw results saved -> {raw_path}")
    print(f"Summary results saved -> {summary_path}")
    print(f"Human-readable overall summary -> {reports['overall_md']}")


def run_configured_experiment(vm_counts, workload_types, seeds, prefix, cpu_configs=CPU_CONFIG_NAMES):
    print_experiment_config(vm_counts, workload_types, seeds, cpu_configs)
    long_df, avg_df = run_full_experiment(
        vm_counts=vm_counts,
        workload_types=workload_types,
        seeds=seeds,
        cpu_configs=cpu_configs,
    )
    save_experiment_results(long_df, avg_df, prefix)


def menu_small_experiment():
    run_configured_experiment(
        vm_counts=[5],
        workload_types=list(WORKLOAD_TYPES),
        seeds=list(FINAL_EXPERIMENT_SEEDS),
        prefix="cpu_comparison_small_experiment",
    )


def menu_single_comparison():
    num_vms = ask_int("Number of VMs", 10)
    workload = ask_choice("Workload type", WORKLOAD_TYPES, "normal")
    seed = ask_int("Random seed", DEFAULT_SEED)
    quantum = ask_int("Time quantum", DEFAULT_TIME_QUANTUM)

    df, _ = run_single_comparison(num_vms, workload, seed, quantum=quantum,
                                  cpu_config=DEFAULT_CPU_CONFIG)
    print("\n=== Single Comparison Results ===")
    print(df.to_string(index=False))
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out = os.path.join(RESULTS_DIR, "single_comparison.csv")
    df.to_csv(out, index=False)
    print(f"\nSaved -> {out}")


def menu_full_experiment():
    print("Running the complete final experiment sweep (this may take a while)...")
    vm_counts_raw = input("VM counts, comma separated [5,10,20,50,100]: ").strip()
    vm_counts = [int(x) for x in vm_counts_raw.split(",")] if vm_counts_raw else list(VM_COUNT_PRESETS)

    wl_raw = input("Workload types, comma separated [light,normal,cpu_heavy,bursty,mixed]: ").strip()
    workload_types = [w.strip() for w in wl_raw.split(",")] if wl_raw else \
        list(WORKLOAD_TYPES)

    seeds_raw = input("Number of trial seeds [5]: ").strip()
    n_seeds = int(seeds_raw) if seeds_raw else len(FINAL_EXPERIMENT_SEEDS)
    seeds = list(range(1, n_seeds + 1))

    run_configured_experiment(vm_counts, workload_types, seeds, "cpu_comparison_full_experiment")


def menu_individual_workload_experiment():
    workload = ask_choice("Workload type", WORKLOAD_TYPES, "normal")
    run_configured_experiment(
        vm_counts=list(VM_COUNT_PRESETS),
        workload_types=[workload],
        seeds=list(FINAL_EXPERIMENT_SEEDS),
        prefix=f"cpu_comparison_{workload}_experiment",
    )


def menu_view_rl_decisions():
    num_vms = ask_int("Number of VMs", 8)
    workload = ask_choice("Workload type", WORKLOAD_TYPES, "normal")
    seed = ask_int("Random seed", DEFAULT_SEED)
    which = ask_choice("Which scheduler", ["rl", "hybrid"], "hybrid")

    workload_vms = generate_workload(num_vms, workload, seed)
    schedulers = build_schedulers(debug=True, seed=seed)
    sched = schedulers["Contextual Bandit RL"] if which == "rl" else schedulers["Proposed Hybrid"]

    sim = Simulator(quantum=DEFAULT_TIME_QUANTUM, debug=True)
    print(f"\n--- Live decision trace: {sched.name} ---\n")
    sim.run(fresh_copy(workload_vms), sched, scheduler_name=sched.name)


def menu_generate_graphs():
    csv_path = os.path.join(RESULTS_DIR, "cpu_comparison_full_experiment_avg.csv")
    if not os.path.exists(csv_path):
        print(f"No averaged experiment results found at {csv_path}.")
        print("Run option 2 (Run full experiment) first.")
        return
    import pandas as pd
    avg_df = pd.read_csv(csv_path)
    paths = generate_all_summary_plots(avg_df, outdir=RESULTS_DIR)
    print(f"\nGenerated {len(paths)} plots in {RESULTS_DIR}/")
    for p in paths:
        print(" -", p)


def menu_generate_gantt():
    num_vms = ask_int("Number of VMs (keep small, e.g. 6-10, for a readable chart)", 8)
    workload = ask_choice("Workload type", WORKLOAD_TYPES, "normal")
    seed = ask_int("Random seed", DEFAULT_SEED)

    workload_vms = generate_workload(num_vms, workload, seed)
    schedulers = build_schedulers(debug=False, seed=seed)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    for name, sched in schedulers.items():
        sim = Simulator(quantum=DEFAULT_TIME_QUANTUM, debug=True)
        result = sim.run(fresh_copy(workload_vms), sched, scheduler_name=name)
        safe_name = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        path = plot_gantt(result, f"Gantt Chart - {name} ({workload}, {num_vms} VMs)",
                           outdir=RESULTS_DIR, filename=f"gantt_{safe_name}.png")
        print(f"Saved {name} Gantt chart -> {path}")


MENU = """
==================================================
        CPU Scheduling Simulator - Main Menu
==================================================
1. Run single comparison (all 4 schedulers, one workload)
2. Run complete final experiment (5 VM counts x 5 workloads x 5 seeds)
3. View RL / Hybrid decisions (live debug trace)
4. Generate summary graphs (from last full experiment)
5. Generate Gantt charts (all 4 schedulers, one workload)
6. Run small experiment (5 VMs x 5 workloads x 5 seeds)
7. Run individual workload experiment (all VM counts x 5 seeds)
0. Exit
"""


def main():
    while True:
        print(MENU)
        choice = input("Select an option: ").strip()
        if choice == "1":
            menu_single_comparison()
        elif choice == "2":
            menu_full_experiment()
        elif choice == "3":
            menu_view_rl_decisions()
        elif choice == "4":
            menu_generate_graphs()
        elif choice == "5":
            menu_generate_gantt()
        elif choice == "6":
            menu_small_experiment()
        elif choice == "7":
            menu_individual_workload_experiment()
        elif choice == "0":
            sys.exit(0)
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
