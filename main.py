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

from config import DEFAULT_TIME_QUANTUM, DEFAULT_SEED, WORKLOAD_TYPES
from simulation.workload_generator import generate_workload, fresh_copy
from simulation.simulator import Simulator
from evaluation.metrics import compute_metrics
from evaluation.experiments import run_single_comparison, run_full_experiment, build_schedulers
from visualization.plots import generate_all_summary_plots
from visualization.gantt import plot_gantt

RESULTS_DIR = "results"


def ask_int(prompt, default):
    raw = input(f"{prompt} [{default}]: ").strip()
    return int(raw) if raw else default


def ask_choice(prompt, choices, default):
    print(f"{prompt} ({'/'.join(choices)}) [{default}]: ", end="")
    raw = input().strip()
    return raw if raw in choices else default


def menu_single_comparison():
    num_vms = ask_int("Number of VMs", 10)
    workload = ask_choice("Workload type", WORKLOAD_TYPES, "normal")
    seed = ask_int("Random seed", DEFAULT_SEED)
    quantum = ask_int("Time quantum", DEFAULT_TIME_QUANTUM)

    df, _ = run_single_comparison(num_vms, workload, seed, quantum=quantum)
    print("\n=== Single Comparison Results ===")
    print(df.to_string(index=False))
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out = os.path.join(RESULTS_DIR, "single_comparison.csv")
    df.to_csv(out, index=False)
    print(f"\nSaved -> {out}")


def menu_full_experiment():
    print("Running full experiment sweep (this runs many simulations, may take a bit)...")
    vm_counts_raw = input("VM counts, comma separated [5,10,20,50]: ").strip()
    vm_counts = [int(x) for x in vm_counts_raw.split(",")] if vm_counts_raw else [5, 10, 20, 50]

    wl_raw = input("Workload types, comma separated [light,normal,cpu_heavy,bursty]: ").strip()
    workload_types = [w.strip() for w in wl_raw.split(",")] if wl_raw else \
        ["light", "normal", "cpu_heavy", "bursty"]

    seeds_raw = input("Number of trial seeds [5]: ").strip()
    n_seeds = int(seeds_raw) if seeds_raw else 5
    seeds = list(range(1, n_seeds + 1))

    long_df, avg_df = run_full_experiment(vm_counts, workload_types, seeds=seeds)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    long_df.to_csv(os.path.join(RESULTS_DIR, "full_experiment_raw.csv"), index=False)
    avg_df.to_csv(os.path.join(RESULTS_DIR, "full_experiment_avg.csv"), index=False)
    print(f"\nSaved raw + averaged results into {RESULTS_DIR}/")
    print("\n=== Averaged results (head) ===")
    print(avg_df.head(20).to_string(index=False))


def menu_view_rl_decisions():
    num_vms = ask_int("Number of VMs", 8)
    workload = ask_choice("Workload type", WORKLOAD_TYPES, "normal")
    seed = ask_int("Random seed", DEFAULT_SEED)
    which = ask_choice("Which scheduler", ["rl", "hybrid"], "hybrid")

    workload_vms = generate_workload(num_vms, workload, seed)
    schedulers = build_schedulers(debug=True)
    sched = schedulers["Contextual Bandit RL"] if which == "rl" else schedulers["Proposed Hybrid"]

    sim = Simulator(quantum=DEFAULT_TIME_QUANTUM, debug=True)
    print(f"\n--- Live decision trace: {sched.name} ---\n")
    sim.run(fresh_copy(workload_vms), sched, scheduler_name=sched.name)


def menu_generate_graphs():
    csv_path = os.path.join(RESULTS_DIR, "full_experiment_avg.csv")
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
    schedulers = build_schedulers(debug=False)

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
2. Run full experiment (sweep VM counts x workloads x seeds)
3. View RL / Hybrid decisions (live debug trace)
4. Generate summary graphs (from last full experiment)
5. Generate Gantt charts (all 4 schedulers, one workload)
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
        elif choice == "0":
            sys.exit(0)
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
