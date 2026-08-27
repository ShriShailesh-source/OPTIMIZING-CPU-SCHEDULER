"""
models/vm.py
============
Data model for a single VM / vCPU task competing for the (single, shared)
physical CPU. This is the unit the scheduling engine operates on.

NOTE ON REALISM: this models the hypervisor scheduling problem described in
the base paper (multiple vCPUs contending for pCPU time) but abstracted to a
single-core scheduling problem, which is the standard simplification used in
OS-course scheduling simulators. Multi-core extension is noted as future work
in the README.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VM:
    vm_id: int
    arrival_time: float
    burst_time: float                 # total CPU time required
    priority: int                     # base (static) priority, higher = more important
    period: float                     # task period, used by PRM (rate-monotonic)
    workload_type: str                # light / normal / cpu_heavy / bursty / mixed
    deadline_relative: float          # deadline is arrival_time + deadline_relative

    # ---- mutable simulation state -----------------------------------
    remaining_time: float = field(init=False)
    waiting_time: float = 0.0
    response_time: Optional[float] = None      # time of FIRST dispatch - arrival
    start_time: Optional[float] = None          # time of first dispatch
    completion_time: Optional[float] = None
    turnaround_time: Optional[float] = None
    last_run_time: Optional[float] = None       # time this vm last ran (for RR bookkeeping)
    energy_consumed: float = 0.0
    context_switches: int = 0                    # times this vm was preempted/resumed
    finished: bool = False

    def __post_init__(self):
        self.remaining_time = self.burst_time

    # ---- convenience / derived properties ----------------------------
    @property
    def deadline_absolute(self) -> float:
        return self.arrival_time + self.deadline_relative

    def deadline_missed(self) -> bool:
        if self.completion_time is None:
            return False
        return self.completion_time > self.deadline_absolute

    def time_to_deadline(self, current_time: float) -> float:
        """Positive = time remaining before deadline, negative = already late."""
        return self.deadline_absolute - current_time

    def cpu_utilization_share(self) -> float:
        """Fraction of its own turnaround time actually spent executing."""
        if not self.turnaround_time or self.turnaround_time <= 0:
            return 0.0
        return self.burst_time / self.turnaround_time

    def __repr__(self):
        return (f"VM(id={self.vm_id}, arr={self.arrival_time:.1f}, "
                f"burst={self.burst_time:.1f}, rem={self.remaining_time:.1f}, "
                f"prio={self.priority}, period={self.period:.1f}, "
                f"type={self.workload_type})")
