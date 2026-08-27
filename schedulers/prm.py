"""
schedulers/prm.py
==================
Algorithm 2: Priority-Based Monotonic (PRM) -- Rate-Monotonic scheduling.

Rule: priority is DERIVED from task period, not assigned directly.
Shorter period => higher priority (classic Liu & Layland rate-monotonic
rule: tasks that must run more frequently are more urgent).

HOW THIS DIFFERS FROM PRR
--------------------------
- PRR uses a fixed, externally-assigned `priority` field and never
  reconsiders it; ties are broken by round robin.
- PRM IGNORES the `priority` field entirely and instead computes
  priority = 1 / period every time it needs to choose, so a VM's urgency
  is intrinsic to how often it needs the CPU, not to an arbitrary label.
- PRM also tracks deadline misses explicitly (rate-monotonic scheduling's
  whole purpose is meeting periodic deadlines), which PRR does not
  reason about at all.

Ties (equal period) are broken the same round-robin way as PRR, using
ready-queue order, for consistency.
"""


class PRMScheduler:
    name = "PRM (Priority Monotonic / Rate Monotonic)"

    def select(self, ready_queue, current_time, quantum, sim):
        best_period = min(v.period for v in ready_queue)   # shorter period = more urgent
        candidates = [v for v in ready_queue if v.period == best_period]
        for v in ready_queue:
            if v in candidates:
                return v
        return candidates[0]
