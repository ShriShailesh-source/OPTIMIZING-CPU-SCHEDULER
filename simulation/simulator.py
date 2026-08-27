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
    decision_log: list = field(default_factory=list)   # for debug / viva demo


class Simulator:
    def __init__(self, quantum: float = DEFAULT_TIME_QUANTUM, debug: bool = False):
        self.quantum = quantum
        self.debug = debug

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
            run_time = min(self.quantum, chosen.remaining_time)
            chosen.remaining_time -= run_time
            time += run_time
            total_busy += run_time
            chosen.last_run_time = time

            # ESTIMATED energy accounting for the slice just executed
            chosen.energy_consumed += estimate_energy(chosen, run_time)

            finished = chosen.remaining_time <= 1e-9
            reward_info = {}

            if finished:
                chosen.remaining_time = 0.0
                chosen.completion_time = time
                chosen.turnaround_time = chosen.completion_time - chosen.arrival_time
                chosen.waiting_time = chosen.turnaround_time - chosen.burst_time
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
                    v.waiting_time += run_time

            reward_info["run_time"] = run_time
            reward_info["others_waiting"] = len(ready)

            # 6. let learning schedulers observe the outcome
            if hasattr(scheduler, "on_decision_result"):
                scheduler.on_decision_result(chosen, run_time, finished, reward_info, self)

            if self.debug:
                log_entry = {
                    "time": round(time, 2),
                    "selected_vm": chosen.vm_id,
                    "run_time": run_time,
                    "finished": finished,
                    "ready_count": len(ready) + (1 if finished else 0),
                }
                decision_log.append(log_entry)

            last_run_vm_id = chosen.vm_id

        total_idle = max(0.0, time - total_busy)
        return SimulationResult(
            vms=completed,
            total_time=time,
            total_busy_time=total_busy,
            total_idle_time=total_idle,
            context_switches=context_switches,
            scheduler_name=scheduler_name,
            decision_log=decision_log,
        )
