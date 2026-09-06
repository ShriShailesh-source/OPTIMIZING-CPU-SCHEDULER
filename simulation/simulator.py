"""
simulation/simulator.py
========================
A single, shared discrete-time-quantum execution engine used by ALL FOUR
schedulers. This is what makes the comparison fair: every scheduler only
gets to answer one question at each decision point --

    "which VM in the ready queue should run for the next quantum?"

--- and the engine (arrivals, quantum execution, requeueing, stats
bookkeeping, deadline checking, energy accounting) is identical no matter
which scheduler answered the question. This guarantees PRR, PRM, the RL
scheduler and the Proposed Hybrid scheduler are compared strictly on the
quality of their *decisions*, not on different simulation mechanics.

A scheduler plugs in by implementing:

    select(ready_queue, current_time, quantum, sim) -> VM

and, optionally:

    on_decision_result(vm, run_time, finished, reward_info, sim)

which is called after the engine executes the decision, so RL-style
schedulers can learn from the outcome.
"""

from dataclasses import dataclass, field
from typing import Optional

from config import DEFAULT_TIME_QUANTUM, CONTEXT_SWITCH_OVERHEAD
from models.cpu_config import CPUConfig, get_cpu_config
from models.vm import VM
from modules.energy_model import estimate_energy


@dataclass
class SimulationResult:
    vms: list          # completed VMs, with all stats filled in
    total_time: float
    total_busy_time: float
    total_idle_time: float
    context_switches: int
    scheduler_name: str
    cpu_config: str
    decision_log: list = field(default_factory=list)   # for debug / viva demo


class Simulator:
    def __init__(self, quantum: float = DEFAULT_TIME_QUANTUM, debug: bool = False,
                 cpu_config: CPUConfig = None):
        if quantum <= 0:
            raise ValueError("quantum must be greater than zero")
        self.quantum = quantum
        self.debug = debug
        self.cpu_config = get_cpu_config(cpu_config)

    def run(self, vms: list[VM], scheduler, scheduler_name: str = "") -> SimulationResult:
        """
        Execute `vms` (a workload, see simulation/workload_generator.py) under
        `scheduler`. `scheduler` must implement `select(...)`.
        """
        pending = sorted(vms, key=lambda v: v.arrival_time)
        ready: list[VM] = []
        completed: list[VM] = []

        time = 0.0
        total_busy = 0.0
        context_switches = 0
        last_run_vm_id = None
        decision_log = []

        # simple recent-history buffer the prediction module can read from
        self.recent_ready_counts: list[int] = []

        while len(completed) < len(vms):
            # 1. admit all VMs that have arrived by `time`
            while pending and pending[0].arrival_time <= time:
                ready.append(pending.pop(0))

            # 2. if nothing is ready, fast-forward to next arrival (CPU idle)
            if not ready:
                if pending:
                    time = pending[0].arrival_time
                    continue
                else:
                    break  # nothing left at all (shouldn't happen)

            self.recent_ready_counts.append(len(ready))

            # 3. ask the scheduler which VM to run next
            chosen = scheduler.select(ready, time, self.quantum, self)
            if chosen not in ready:
                raise RuntimeError(f"Scheduler {scheduler_name} chose a VM not in ready queue")

            # 4. bookkeeping: first dispatch => response time
            if chosen.response_time is None:
                chosen.response_time = time - chosen.arrival_time
                chosen.start_time = time

            if last_run_vm_id is not None and last_run_vm_id != chosen.vm_id:
                context_switches += 1
                chosen.context_switches += 1

            # 5. execute for one quantum slice (or until completion)
            start_time = time
            work_time = min(self.quantum, chosen.remaining_time)
            elapsed_time = work_time / self.cpu_config.execution_speed_factor
            chosen.remaining_time -= work_time
            time += elapsed_time
            end_time = time
            total_busy += elapsed_time
            chosen.last_run_time = time

            # ESTIMATED energy accounting for the slice just executed
            chosen.energy_consumed += estimate_energy(chosen, elapsed_time, self.cpu_config)

            finished = chosen.remaining_time <= 1e-9
            reward_info = {}

            if finished:
                chosen.remaining_time = 0.0
                chosen.completion_time = time
                chosen.turnaround_time = chosen.completion_time - chosen.arrival_time
                service_time = chosen.burst_time / self.cpu_config.execution_speed_factor
                chosen.waiting_time = chosen.turnaround_time - service_time
                chosen.finished = True
                ready.remove(chosen)
                completed.append(chosen)
                reward_info["finished"] = True
                reward_info["deadline_missed"] = chosen.deadline_missed()
            else:
                # move to back of ready queue (fairness for equal-priority ties)
                ready.remove(chosen)
                ready.append(chosen)
                reward_info["finished"] = False

            # update *waiting* time for everyone else still waiting this slice
            for v in ready:
                if v.vm_id != chosen.vm_id:
                    v.waiting_time += elapsed_time

                reward_info["run_time"] = work_time
                reward_info["elapsed_time"] = elapsed_time
            reward_info["others_waiting"] = len(ready)

            # 6. let learning schedulers observe the outcome
            if hasattr(scheduler, "on_decision_result"):
                scheduler.on_decision_result(chosen, work_time, finished, reward_info, self)

            decision_log.append({
                "order": len(decision_log) + 1,
                "vm_id": chosen.vm_id,
                "selected_vm": chosen.vm_id,
                "start_time": round(start_time, 2),
                "end_time": round(end_time, 2),
                "duration": round(elapsed_time, 2),
                "time": round(end_time, 2),
                "run_time": work_time,
                "finished": finished,
                "ready_count": len(ready) + (1 if finished else 0),
            })

            last_run_vm_id = chosen.vm_id

        total_idle = max(0.0, time - total_busy)
        return SimulationResult(
            vms=completed,
            total_time=time,
            total_busy_time=total_busy,
            total_idle_time=total_idle,
            context_switches=context_switches,
            scheduler_name=scheduler_name,
            cpu_config=self.cpu_config.name,
            decision_log=decision_log,
        )
