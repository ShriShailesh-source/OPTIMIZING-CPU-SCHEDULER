"""
simulation/workload_generator.py
=================================
Generates a reproducible set of VMs for a given (num_vms, workload_type, seed).

CRITICAL FOR FAIR COMPARISON: given the same (num_vms, workload_type, seed),
this always produces an identical list of VMs (same arrival times, burst
times, priorities, periods, deadlines). The experiment runner regenerates
the workload once per trial and feeds a *fresh copy* of it to every scheduler,
so no scheduler ever sees an easier or harder instance than another.
"""

import copy
import numpy as np

from config import (
    BURST_RANGES, ARRIVAL_GAP_RANGES, PRIORITY_RANGE, PERIOD_RANGE,
    DEADLINE_SLACK_RANGE, WORKLOAD_TYPES,
)
from models.vm import VM


def _sample_burst(workload_type: str, rng: np.random.Generator) -> float:
    if workload_type == "mixed":
        # mixture: 40% light, 30% normal, 20% cpu_heavy, 10% bursty
        choice = rng.choice(
            ["light", "normal", "cpu_heavy", "bursty"],
            p=[0.4, 0.3, 0.2, 0.1],
        )
        lo, hi = BURST_RANGES[choice]
    else:
        lo, hi = BURST_RANGES[workload_type]
    return float(rng.uniform(lo, hi))


def generate_workload(num_vms: int, workload_type: str, seed: int) -> list[VM]:
    """Deterministically generate `num_vms` VMs for `workload_type` using `seed`."""
    if workload_type not in WORKLOAD_TYPES:
        raise ValueError(f"Unknown workload_type '{workload_type}', must be one of {WORKLOAD_TYPES}")

    rng = np.random.default_rng(seed)
    gap_lo, gap_hi = ARRIVAL_GAP_RANGES[workload_type]

    vms = []
    t = 0.0
    for i in range(num_vms):
        gap = float(rng.uniform(gap_lo, gap_hi))
        t += gap
        burst = _sample_burst(workload_type, rng)
        priority = int(rng.integers(PRIORITY_RANGE[0], PRIORITY_RANGE[1] + 1))
        period = float(rng.uniform(*PERIOD_RANGE))
        slack = float(rng.uniform(*DEADLINE_SLACK_RANGE))
        deadline_relative = slack * burst

        vms.append(VM(
            vm_id=i,
            arrival_time=round(t, 2),
            burst_time=round(burst, 2),
            priority=priority,
            period=round(period, 2),
            workload_type=workload_type,
            deadline_relative=round(deadline_relative, 2),
        ))
    return vms


def fresh_copy(vms: list[VM]) -> list[VM]:
    """Deep-copy a workload so a scheduler run never mutates the shared original."""
    return copy.deepcopy(vms)
