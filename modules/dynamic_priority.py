"""
modules/dynamic_priority.py
============================
Dynamic Priority Adjustment (our proposed extension).

Static priority (PRR-style) never changes, so a low-priority VM can starve
under sustained contention. This module computes an *effective* priority
that starts from the VM's static priority and is boosted by:

  1. Waiting time    -- the longer a VM has waited, the more urgent it becomes
                         (classic aging, prevents starvation).
  2. Deadline urgency -- the closer the deadline, the bigger the boost.
  3. Task period      -- shorter-period (more frequent/urgent) tasks get a
                         small standing boost, echoing rate-monotonic
                         reasoning inside the hybrid scheduler.

Everything here is a plain, inspectable linear formula on purpose -- the
whole point of "explainable" scheduling is that you can print the formula
and the numbers that went into it during the viva.

    effective_priority(vm, t) =
          base_priority
        + PRIORITY_WAIT_COEFF     * waiting_time
        + PRIORITY_DEADLINE_COEFF * urgency(vm, t)
        + PRIORITY_PERIOD_COEFF   * (1 / period)  [scaled]

    urgency(vm, t) = clamp(1 - time_to_deadline / deadline_relative, 0, 1)
        -> 0 when the deadline is far away, -> 1 as the deadline arrives,
           and can exceed 1 (we clamp it) once the deadline has passed.
"""

from config import PRIORITY_WAIT_COEFF, PRIORITY_DEADLINE_COEFF, PRIORITY_PERIOD_COEFF
from models.vm import VM


def deadline_urgency(vm: VM, current_time: float) -> float:
    if vm.deadline_relative <= 0:
        return 0.0
    ttd = vm.time_to_deadline(current_time)
    urgency = 1.0 - (ttd / vm.deadline_relative)
    return max(0.0, min(urgency, 1.5))  # allow a little over-1 boost if already late


def effective_priority(vm: VM, current_time: float, explain: bool = False):
    wait_term = PRIORITY_WAIT_COEFF * vm.waiting_time
    urgency = deadline_urgency(vm, current_time)
    deadline_term = PRIORITY_DEADLINE_COEFF * urgency
    period_term = PRIORITY_PERIOD_COEFF * (100.0 / max(vm.period, 1.0))  # shorter period -> bigger term

    score = vm.priority + wait_term + deadline_term + period_term

    if explain:
        breakdown = {
            "base_priority": vm.priority,
            "wait_term": round(wait_term, 3),
            "deadline_urgency": round(urgency, 3),
            "deadline_term": round(deadline_term, 3),
            "period_term": round(period_term, 3),
            "effective_priority": round(score, 3),
        }
        return score, breakdown
    return score
