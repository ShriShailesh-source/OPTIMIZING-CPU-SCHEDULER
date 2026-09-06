"""
evaluation/experiments.py
==========================
Runs the same generated workload through all four schedulers, across
multiple random seeds (trials), and reports averaged results. Nothing here
is invented -- every number comes from an actual Simulator.run() call.
"""

import random

import pandas as pd

from config import DEFAULT_TIME_QUANTUM, FINAL_EXPERIMENT_SEEDS, VM_COUNT_PRESETS, WORKLOAD_TYPES
from models.cpu_config import CPU_CONFIG_NAMES, DEFAULT_CPU_CONFIG, get_cpu_config
from simulation.workload_generator import generate_workload, fresh_copy
from simulation.simulator import Simulator
from evaluation.metrics import compute_metrics

from schedulers.prr import PRRScheduler
from schedulers.prm import PRMScheduler
from schedulers.contextual_bandit import ContextualBanditScheduler
from schedulers.proposed_hybrid import ProposedHybridScheduler


def build_schedulers(debug=False, seed=None):
    """Fresh scheduler instances -- RL/Hybrid schedulers carry learned state
    across the run, so ALWAYS build new ones per trial to avoid leaking
    learning from one trial/workload into another."""
    rl_rng = random.Random(seed)
    hybrid_rng = random.Random(None if seed is None else seed + 1)
    return {
        "PRR": PRRScheduler(),
        "PRM": PRMScheduler(),
        "Contextual Bandit RL": ContextualBanditScheduler(debug=debug, rng=rl_rng),
        "Proposed Hybrid": ProposedHybridScheduler(debug=debug, rng=hybrid_rng),
    }


def run_single_comparison(num_vms, workload_type, seed, quantum=DEFAULT_TIME_QUANTUM,
                          debug=False, cpu_config=DEFAULT_CPU_CONFIG):
    """Run one workload instance through all four schedulers, return a
    DataFrame of metrics (one row per scheduler)."""
    workload = generate_workload(num_vms, workload_type, seed)
    schedulers = build_schedulers(debug=debug, seed=seed)

    rows = []
    sim_results = {}
    for name, sched in schedulers.items():
        sim = Simulator(quantum=quantum, debug=debug, cpu_config=cpu_config)
        result = sim.run(fresh_copy(workload), sched, scheduler_name=name)
        sim_results[name] = result
        rows.append(compute_metrics(result))

    return pd.DataFrame(rows), sim_results


def run_full_experiment(
    vm_counts=None,
    workload_types=None,
    seeds=None,
    quantum=DEFAULT_TIME_QUANTUM,
    cpu_configs=None,
    verbose=True,
):
    """
    Sweep over cpu_configs x vm_counts x workload_types x seeds, run all four schedulers
    on each, and return a long-format DataFrame with one row per
    (num_vms, workload_type, seed, scheduler) plus a second DataFrame
    averaged over seeds (the one used for the summary plots).
    """
    cpu_configs = list(cpu_configs) if cpu_configs is not None else list(CPU_CONFIG_NAMES)
    vm_counts = list(vm_counts) if vm_counts is not None else list(VM_COUNT_PRESETS)
    workload_types = list(workload_types) if workload_types is not None else list(WORKLOAD_TYPES)
    seeds = list(seeds) if seeds is not None else list(FINAL_EXPERIMENT_SEEDS)

    all_rows = []
    total_runs = len(cpu_configs) * len(vm_counts) * len(workload_types) * len(seeds) * 4
    done = 0

    for cpu_config in cpu_configs:
        config_name = get_cpu_config(cpu_config).name
        for num_vms in vm_counts:
            for wtype in workload_types:
                for seed in seeds:
                    df, _ = run_single_comparison(
                        num_vms, wtype, seed, quantum=quantum, debug=False,
                        cpu_config=cpu_config,
                    )
                    df["cpu_config"] = config_name
                    df["num_vms"] = num_vms
                    df["workload_type"] = wtype
                    df["seed"] = seed
                    all_rows.append(df)
                    done += 4
                    if verbose:
                        print(f"  [{done}/{total_runs}] cpu={config_name:<12} "
                              f"num_vms={num_vms:<4} workload={wtype:<10} seed={seed}")

    long_df = pd.concat(all_rows, ignore_index=True)

    group_cols = ["cpu_config", "workload_type", "num_vms", "scheduler"]
    metric_cols = [c for c in long_df.columns if c not in group_cols + ["seed"]]
    avg_df = long_df.groupby(group_cols, as_index=False)[metric_cols].mean(numeric_only=True)

    return long_df, avg_df
