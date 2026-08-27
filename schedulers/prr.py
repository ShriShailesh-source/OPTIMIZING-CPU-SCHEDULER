"""
schedulers/prr.py
==================
Algorithm 1: Priority-Based Round Robin (PRR).

Rule: among the currently ready VMs, run the one with the HIGHEST static
priority. VMs that share the same (highest) priority are served in
Round-Robin order using the shared time quantum.

Because the simulation engine (simulation/simulator.py) always appends a
VM back to the END of the ready list when it is preempted, and this
scheduler always scans the ready list in order, ties at the same priority
level are naturally served FCFS-among-equals each quantum, which IS
round robin: whichever same-priority VM has waited longest since it last
ran gets picked next.

PRR does NOT change priority over time and does NOT look at deadlines,
periods or energy -- that is precisely the gap the Proposed Hybrid
Scheduler is built to close.
"""


class PRRScheduler:
    name = "PRR (Priority Round Robin)"

    def select(self, ready_queue, current_time, quantum, sim):
        best_priority = max(v.priority for v in ready_queue)
        candidates = [v for v in ready_queue if v.priority == best_priority]
        # ready_queue order already encodes "who has waited longest at the
        # back", so the first candidate in list order is the RR choice.
        for v in ready_queue:
            if v in candidates:
                return v
        return candidates[0]  # unreachable, defensive fallback
