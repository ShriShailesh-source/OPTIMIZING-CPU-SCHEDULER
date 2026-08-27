"""
evaluation/metrics.py
======================
All performance metrics, with their exact formulas documented inline.
Computed strictly from the completed VMs / SimulationResult -- nothing is
hard-coded or estimated by hand.

Given a SimulationResult `res` with `res.vms` = list of completed VMs:

1. Average waiting time
       AWT = (1/n) * sum(vm.waiting_time for vm in vms)

2. Average turnaround time
       ATT = (1/n) * sum(vm.turnaround_time for vm in vms)
       where turnaround_time = completion_time - arrival_time

3. Average response time
       ART = (1/n) * sum(vm.response_time for vm in vms)
       where response_time = (time of first dispatch) - arrival_time

4. CPU utilization (system-level)
       U = total_busy_time / total_time
       (total_time = makespan of the whole run, from t=0 to last completion)

5. Throughput
       T = n / total_time      (completed VMs per unit time)

6. Deadline misses
       M = count(vm.deadline_missed() is True)

7. Deadline miss rate
       MR = M / n

8. Fairness (Jain's Fairness Index)
       We apply Jain's index to x_i = 1 / (1 + waiting_time_i), i.e. a
       VM that waited 0 ticks scores x=1 (perfectly served), a VM that
       waited a long time scores x -> 0. This keeps the index in the
       classic Jain's range and makes "closer to 1 is fairer" intuitive
       (equivalent to asking "how equally was low-waiting-time service
       distributed"):

           J = (sum(x_i))^2 / (n * sum(x_i^2))     in (0, 1], 1 = perfectly fair

9. Estimated energy consumption
       E = sum(vm.energy_consumed for vm in vms)
       (ESTIMATED, see modules/energy_model.py -- NOT real hardware power)

10. Scheduling overhead (ESTIMATED)
       O = context_switches * CONTEXT_SWITCH_OVERHEAD
       (a fixed per-switch cost constant, see config.py; this is a common,
       explicitly-labelled simplification since we are not modeling actual
       hypervisor trap/VM-exit latency)
"""

from config import CONTEXT_SWITCH_OVERHEAD


def compute_metrics(res) -> dict:
    vms = res.vms
    n = len(vms)
    if n == 0:
        return {}

    total_wait = sum(v.waiting_time for v in vms)
    total_turnaround = sum(v.turnaround_time for v in vms)
    total_response = sum(v.response_time for v in vms)

    avg_waiting = total_wait / n
    avg_turnaround = total_turnaround / n
    avg_response = total_response / n

    cpu_utilization = (res.total_busy_time / res.total_time) if res.total_time > 0 else 0.0
    throughput = n / res.total_time if res.total_time > 0 else 0.0

    misses = sum(1 for v in vms if v.deadline_missed())
    miss_rate = misses / n

    x = [1.0 / (1.0 + v.waiting_time) for v in vms]
    sum_x = sum(x)
    sum_x2 = sum(xi ** 2 for xi in x)
    fairness = (sum_x ** 2) / (n * sum_x2) if sum_x2 > 0 else 1.0

    total_energy = sum(v.energy_consumed for v in vms)
    scheduling_overhead = res.context_switches * CONTEXT_SWITCH_OVERHEAD

    return {
        "scheduler": res.scheduler_name,
        "num_vms": n,
        "avg_waiting_time": round(avg_waiting, 4),
        "avg_turnaround_time": round(avg_turnaround, 4),
        "avg_response_time": round(avg_response, 4),
        "cpu_utilization": round(cpu_utilization, 4),
        "throughput": round(throughput, 5),
        "deadline_misses": misses,
        "deadline_miss_rate": round(miss_rate, 4),
        "fairness_jain_index": round(fairness, 4),
        "estimated_energy": round(total_energy, 3),
        "context_switches": res.context_switches,
        "estimated_scheduling_overhead": round(scheduling_overhead, 4),
        "total_time": round(res.total_time, 3),
    }
