# Viva Quick-Reference

**One-line pitch:** "A Python CPU scheduling simulator that runs the same
VM workload through four schedulers -- Priority Round Robin, Rate
Monotonic, a lightweight contextual-bandit RL scheduler, and our own
Hybrid scheduler that adds workload prediction, dynamic priority, and
estimated energy-awareness on top of the bandit -- using one shared
simulation engine so the comparison is fair."

**If asked "did you modify Xvisor / use the PhytiumPi board?"**
No. This is a simulation inspired by the paper's scheduling *idea*, built
for the course project scope. Say this plainly and move on -- don't
overclaim.

**If asked "is the energy number real?"**
No, it's an explicitly labelled estimated proxy: `power[workload_type] *
execution_time`. Point to `modules/energy_model.py`'s docstring.

**If asked "how is this different from a normal priority scheduler?"**
Walk through the three proposed modules one at a time:
1. Dynamic priority = static priority + aging (waiting time) + deadline
   urgency + period-based urgency, recomputed every decision.
2. Workload prediction = moving average of recent ready-queue size ->
   predicted near-future load -> SRTF-flavoured nudge when load is high.
3. Energy = same estimated proxy, subtracted as a penalty in the hybrid
   score so the scheduler is discouraged from picking VMs with a high
   power-rate label if it's not needed.
Then show the combined formula in `schedulers/proposed_hybrid.py::select`.

**If asked "prove the RL scheduler actually learns"**
Run `python main.py` option 3, or run
`tests_manual_validation.py`-style code with `debug=True` and point at the
printed `updated_weights=[...]` line after every decision -- the weight
vector visibly changes based on reward, and epsilon decays over time so
the scheduler exploits its learned values more as the run progresses.

**If asked "prove your metrics are correct, not made up"**
Run `python tests_manual_validation.py`. It works a 3-VM, quantum=4
example completely by hand in the docstring, then asserts the engine
produces exactly those numbers.

**If asked "why Jain's index for fairness?"**
Fairness has many valid definitions; we picked Jain's index applied to
`1/(1+waiting_time)` per VM so "1.0 = perfectly fair" and lower values
mean waiting time was unevenly distributed across VMs. This is stated
explicitly in `evaluation/metrics.py`.

**If asked "what would you improve given more time?"**
Multi-core scheduling / load balancing across pCPUs, a proper Liu &
Layland schedulability-bound check for PRM, and replacing the linear
bandit with a small neural contextual bandit once you have enough
simulated trajectories to justify it.
