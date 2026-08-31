# CPU Scheduling Simulator with Reinforcement Learning
### An OS-course final project inspired by *"Optimizing CPU Scheduling and Inter-VM Communication for Lightweight Virtualization using Reinforcement Learning"*

## 1. Project Motivation

Hypervisors that run many lightweight VMs (containers, unikernels, microVMs)
on a shared physical CPU face a scheduling problem that classic OS
schedulers weren't designed for: workloads are heterogeneous, arrive
dynamically, and have mixed real-time/best-effort requirements at once.
The base paper explores using reinforcement learning inside a real
hypervisor (Xvisor, on PhytiumPi hardware) to make better vCPU-to-pCPU
scheduling decisions than static priority schemes.

## 2. Research Gap

Static priority schedulers (Round Robin with priorities, Rate-Monotonic)
are simple and predictable but:
- don't adapt to changing contention,
- can starve low-priority tasks under load,
- don't reason about upcoming demand, and
- don't consider energy cost of decisions.

The base paper's RL approach begins to close this gap but is demonstrated
inside a full hypervisor stack, which is out of scope for a course project.

## 3. What This Project Is (and Isn't)

This is a **Python simulation/prototype**, not a modification of Xvisor and
not a deployment on PhytiumPi or any physical hardware. It models the same
*scheduling decision problem* (many contending VMs, one shared CPU) at a
level of abstraction appropriate for an OS course:

| Feature | Status |
|---|---|
| Xvisor hypervisor modification | **NOT done** - out of scope |
| PhytiumPi / physical hardware | **NOT done** - simulated only |
| Real hardware power measurement | **NOT done** - energy is an ESTIMATED proxy model, clearly labelled everywhere |
| CPU scheduling concepts from the paper (RL-based vCPU scheduling) | **Implemented**, simplified to a lightweight linear contextual bandit |
| Comparison against classic schedulers (priority RR, rate-monotonic) | **Implemented** |
| Our own proposed extensions (workload prediction, dynamic priority, energy-awareness) | **Implemented**, original to this project |

### Features taken / inspired from the base paper
- The core idea of using a **reinforcement-learning agent to choose which
  VM/vCPU runs next**, instead of a fixed static rule.
- Using **state features like waiting time, priority, and utilization** to
  drive the RL decision.
- Comparing the RL scheduler against conventional priority-based schedulers.

### Features proposed by our project (not in the base paper)
- The **Proposed Hybrid Intelligent Scheduler**, combining the bandit with:
  - Workload Prediction (moving-average load forecasting)
  - Dynamic Priority Adjustment (aging + deadline urgency + period)
  - An estimated Energy-Aware penalty term
- A **unified single simulation engine** shared by all four schedulers so
  comparisons are guaranteed fair (see `simulation/simulator.py`).
- The full **experiment sweep + plotting + Gantt chart pipeline**.

## 4. Architecture

```
project/
│
├── main.py                      # CLI entry point (menu-driven)
├── config.py                    # every tunable constant, single source of truth
│
├── models/
│   └── vm.py                    # VM/vCPU data model
│
├── schedulers/
│   ├── prr.py                   # Algorithm 1: Priority Round Robin
│   ├── prm.py                   # Algorithm 2: Priority Monotonic (Rate Monotonic)
│   ├── contextual_bandit.py     # Algorithm 3: linear contextual bandit RL
│   └── proposed_hybrid.py       # Our proposed extension of the bandit
│
├── modules/
│   ├── workload_prediction.py   # moving-average load forecaster
│   ├── dynamic_priority.py      # aging + deadline-urgency priority formula
│   └── energy_model.py          # ESTIMATED energy/power proxy
│
├── simulation/
│   ├── simulator.py             # the ONE shared execution engine
│   └── workload_generator.py    # deterministic, seedable workload generation
│
├── evaluation/
│   ├── metrics.py                # all metric formulas
│   └── experiments.py            # experiment sweep runner
│
├── visualization/
│   ├── plots.py                  # comparison charts, including Jain fairness
│   └── gantt.py                  # Gantt chart of an actual run
│
├── results/                      # generated CSVs and PNGs land here
├── tests_manual_validation.py    # hand-worked-example validation script
├── requirements.txt
└── README.md
```

### Why one shared simulation engine?

Every scheduler only has to answer: *"given the current ready queue and
time, which VM should run for the next quantum?"* The engine
(`Simulator.run`) handles arrivals, quantum slicing, requeueing, waiting
time accrual, deadline checks and energy accounting identically no matter
which scheduler answered. This is what guarantees PRR, PRM, the bandit, and
the hybrid scheduler are compared on decision quality alone, not on
different simulation mechanics -- and it's why every experiment regenerates
the workload once and feeds an independent deep copy to each scheduler
(`workload_generator.fresh_copy`).

## 5. Data Model (`models/vm.py`)

Each `VM` carries: `vm_id`, `arrival_time`, `burst_time`, `remaining_time`,
`priority`, `period`, `deadline_relative` (-> `deadline_absolute` property),
`workload_type`, plus simulation-filled fields: `waiting_time`,
`response_time`, `start_time`, `completion_time`, `turnaround_time`,
`energy_consumed`, `context_switches`, `finished`.

## 6. Metric Formulas (`evaluation/metrics.py`)

| Metric | Formula |
|---|---|
| Avg waiting time | mean(`completion - arrival - burst`) |
| Avg turnaround time | mean(`completion - arrival`) |
| Avg response time | mean(`first_dispatch - arrival`) |
| CPU utilization | `total_busy_time / total_time` |
| Throughput | `num_completed / total_time` |
| Deadline misses | count(`completion > arrival + deadline_relative`) |
| Deadline miss rate | `misses / n` |
| Fairness | Jain's index on `x_i = 1/(1+waiting_time_i)` |
| Estimated energy | sum of per-slice `power[workload_type] * run_time` (labelled ESTIMATED) |
| Scheduling overhead | `context_switches * CONTEXT_SWITCH_OVERHEAD` (labelled ESTIMATED) |

All formulas are re-derived and asserted against a hand-worked 3-VM example
in `tests_manual_validation.py`.

## 7. RL State / Actions / Reward (`schedulers/contextual_bandit.py`)

- **State** (per candidate VM, normalized): waiting time, priority,
  remaining/burst ratio, deadline urgency, inverse period, workload-type
  code, ready-queue congestion.
- **Actions**: choose exactly one ready VM to dispatch next.
- **Policy**: `Q(vm) = w . features(vm)`, epsilon-greedy selection,
  epsilon decays over time (more exploitation as the run progresses).
- **Reward**: small progress reward, penalty proportional to how many
  other VMs were kept waiting, +3/-3 for meeting/missing a deadline on
  completion, plus a bounded bonus for short realized turnaround.
- **Update**: online Widrow-Hoff (LMS) gradient step on `w`.
- Run `python main.py` -> option 3 to print a live `t=... mode=... Q=...
  -> selected VM...` trace, which is exactly what's logged during the run.

## 8. Proposed Extensions

**Workload Prediction** (`modules/workload_prediction.py`): moving average
of recent ready-queue size predicts near-future contention; under
predicted heavy load it adds a bounded bonus favoring VMs with less
remaining work (an SRTF-flavoured nudge, not a hard rule).

**Dynamic Priority** (`modules/dynamic_priority.py`):
`effective_priority = base_priority + wait_coeff*waiting_time + deadline_coeff*urgency + period_coeff*(1/period)`,
fully printable per decision.

**Energy Model** (`modules/energy_model.py`): `energy = power[workload_type] * run_time`,
an explicitly ESTIMATED proxy, never claimed to be measured from hardware.

**Hybrid decision**: `score(vm) = w_rl*norm(Q) + w_priority*norm(effective_priority) + w_prediction*srtf_bias - w_energy*norm(power)`,
argmax with epsilon-greedy exploration (see `schedulers/proposed_hybrid.py`).
Weights live in `config.HYBRID_WEIGHTS` for easy tuning.

## 9. Experimental Methodology

`evaluation/experiments.py::run_full_experiment` sweeps VM counts
(5/10/20/50/100 by default) x workload types
(light/normal/cpu_heavy/bursty/mixed by default) x five random seeds (1-5), runs all four schedulers on an
*independent copy* of the same generated workload each time, and averages
metrics over seeds. Nothing is hard-coded: every number in `results/*.csv`
comes from an actual `Simulator.run()` call.

## 10. How to Run

```bash
pip install -r requirements.txt
python main.py
```

Menu options:
1. Single comparison (all 4 schedulers on one workload) -> prints + saves CSV
2. Full experiment sweep -> saves `results/full_experiment_raw.csv` and `_avg.csv`
3. Live RL/Hybrid decision trace (for viva demo)
4. Generate all summary graphs from the last full experiment
5. Generate Gantt charts (all 4 schedulers, one workload)
6. Run the small experiment (5 VMs x 5 workloads x 5 seeds)
7. Run one workload across all configured VM counts and seeds

Every experiment saves a raw CSV, a seed-averaged CSV, and human-readable
overall and workload/VM-count summary tables in `results/`. The final full
sweep therefore executes 5 VM counts x 5 workloads x 5 seeds x 4 schedulers
= 500 scheduler runs.

The plotting pipeline covers waiting, turnaround, response, utilization,
throughput, deadline misses and miss rate, Jain fairness, estimated energy,
context switches, and estimated scheduling overhead. It writes PNG charts
when Matplotlib is available and uses equivalent data-backed SVG exports in
restricted environments where that plotting backend cannot be loaded.

Or from a script:
```python
from evaluation.experiments import run_single_comparison
df, sim_results = run_single_comparison(num_vms=20, workload_type="bursty", seed=1)
print(df)
```

Validate the engine against hand-worked numbers any time:
```bash
python tests_manual_validation.py
```

## 11. How to Interpret Results

- Lower is better for waiting/turnaround/response time, deadline misses,
  miss rate, energy, and overhead.
- Higher is better for CPU utilization (up to 1.0), throughput, and
  fairness (up to 1.0).
- The Proposed Hybrid scheduler is expected to show the best *balance*
  across metrics, particularly fairness and deadline-miss rate under
  heavier/bursty workloads, rather than winning on every single metric --
  a scheduler that only chases one metric will typically lose on another
  (e.g. an SRTF-heavy bias reduces average waiting time but hurts fairness
  to long jobs). Discuss trade-offs, don't just report "hybrid wins".
- The bandit and hybrid schedulers **learn within a run** (`w` starts at
  zero); the plots based on `run_full_experiment` reflect that in-run
  learning, not a separately pre-trained model, since a fresh
  scheduler instance is built per trial (see `build_schedulers` in
  `experiments.py`) to avoid leaking learning across trials/workloads.

## 12. Known Simplifications (be upfront about these in the viva)

- Single shared CPU core (matches a single pCPU being time-shared by
  multiple vCPUs -- the paper's core setting -- but doesn't model
  multi-core load balancing).
- Energy and scheduling-overhead are simple, clearly labelled ESTIMATED
  proxies, not measurements.
- Rate-monotonic priority here is computed directly from `period`, not
  formally derived via Liu & Layland utilization-bound schedulability
  analysis (that analysis could be added as an extension).
- The contextual bandit learns only within each simulated run; it is not
  pre-trained and no deep-learning model is used.
