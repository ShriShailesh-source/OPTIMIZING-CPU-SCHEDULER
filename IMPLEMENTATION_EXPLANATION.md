# Implementation Explanation

Use this file as a presentation guide for the implementation. It focuses on
the important code path and avoids explaining every supporting file.

## 1. One-line project explanation

This project simulates several CPU schedulers competing to run virtual
machines (VMs) on one shared CPU. Every scheduler uses the same simulation
engine, so the comparison measures scheduling decisions rather than
differences in simulation logic.

## 2. Overall execution flow

```text
main.py
  -> generate_workload()
  -> build_schedulers()
  -> Simulator.run() for each scheduler
  -> compute_metrics()
  -> save CSV summaries and plots
```

The main implementation files are:

- `models/vm.py` - stores one VM's input data and changing runtime state.
- `simulation/workload_generator.py` - creates repeatable VM workloads.
- `simulation/simulator.py` - shared CPU execution loop.
- `schedulers/` - four alternative scheduling decisions.
- `modules/` - prediction, dynamic priority, and estimated energy logic.
- `evaluation/metrics.py` - calculates the performance results.
- `evaluation/experiments.py` - runs fair comparisons and averages trials.

## 3. VM data model

The `VM` dataclass in `models/vm.py` represents one vCPU/task. Important input
values are:

- `arrival_time`: when the VM becomes ready.
- `burst_time`: total CPU time required.
- `priority`: static importance from 1 to 10.
- `period`: used by rate-monotonic scheduling.
- `deadline_relative`: deadline offset from arrival.
- `workload_type`: light, normal, CPU-heavy, bursty, or mixed.

The simulator fills in runtime values such as `remaining_time`,
`waiting_time`, `response_time`, `completion_time`, `turnaround_time`,
`energy_consumed`, and `context_switches`.

`remaining_time` is initialized to `burst_time`. Each CPU quantum decreases it
until it reaches zero, which marks the VM as finished.

## 4. Shared simulation engine: the most important part

The `Simulator.run()` method in `simulation/simulator.py` is shared by all
four schedulers. This guarantees a fair experiment.

At each iteration it:

1. Admits all VMs whose arrival time has been reached.
2. Fast-forwards time if the ready queue is empty.
3. Calls `scheduler.select(...)` to choose one ready VM.
4. Records first-dispatch response time and context switches.
5. Runs the VM for one quantum, or until it finishes.
6. Updates remaining time, waiting time, completion time, and energy.
7. Requeues unfinished VMs at the back of the ready queue.
8. Sends the result to the RL scheduler for learning.
9. Records the decision in the debug/Gantt-chart log.

The key design decision is that a scheduler only answers:

```text
"Which VM should run next?"
```

The scheduler does not implement its own timing, waiting-time calculation, or
completion logic. Those rules remain identical for every algorithm.

### Quantum execution

```python
work_time = min(quantum, chosen.remaining_time)
elapsed_time = work_time / cpu_config.execution_speed_factor
chosen.remaining_time -= work_time
time += elapsed_time
```

This models preemption after a fixed quantum while allowing different
simulated CPU configurations to execute at different speeds.

## 5. The four scheduling algorithms

### A. Priority Round Robin (`schedulers/prr.py`)

1. Find the highest static priority currently in the ready queue.
2. Select the first VM with that priority.
3. After a quantum, the simulator moves unfinished VMs to the back.

This gives round-robin behavior among equal-priority VMs. It is simple and
predictable, but it does not adapt to waiting time, deadlines, workload, or
energy.

### B. Priority Monotonic / Rate Monotonic (`schedulers/prm.py`)

This algorithm ignores the manually assigned priority and selects the VM with
the shortest period:

```text
shorter period -> higher frequency/urgency -> selected first
```

It is appropriate for periodic tasks, but it does not learn from previous
decisions and does not directly account for energy or starvation.

### C. Contextual Bandit RL (`schedulers/contextual_bandit.py`)

This is a lightweight, explainable reinforcement-learning scheduler. It is a
linear contextual bandit, not a deep neural network.

#### State/features

For every ready VM, `featurize()` creates seven normalized features:

1. Waiting time.
2. Static priority.
3. Remaining time divided by burst time.
4. Deadline urgency.
5. Inverse period.
6. Workload type code.
7. Ready-queue congestion.

#### Action

Each ready VM is a possible action. The scheduler scores every candidate:

```text
Q(vm) = weights dot features(vm)
```

#### Selection

- With probability `epsilon`, it explores by choosing randomly.
- Otherwise, it exploits by choosing the VM with the highest Q-value.
- `epsilon` decays after each decision, so the scheduler gradually relies
  more on learned behavior.

#### Reward and learning

After the simulator executes the quantum, `on_decision_result()` calculates a
reward. The reward:

- gives a small positive value for making progress,
- penalizes leaving other VMs waiting,
- rewards completing before a deadline,
- penalizes a deadline miss,
- rewards shorter turnaround time.

The weights are updated online using the Widrow-Hoff/LMS rule:

```text
error = reward - predicted_Q
weights = weights + learning_rate * error * features
```

Therefore, the model learns during the same simulation run and remains
inspectable.

### D. Proposed Hybrid Intelligent Scheduler
(`schedulers/proposed_hybrid.py`)

The hybrid scheduler extends the contextual bandit and combines four signals:

```text
score(vm) =
    RL weight         * normalized RL score
  + priority weight   * normalized effective priority
  + prediction weight * workload prediction bias
  - energy weight     * normalized estimated power
```

It chooses the highest combined score, while keeping epsilon-greedy
exploration.

This is the proposed contribution because it combines learning with
explainable OS scheduling rules:

- **Dynamic priority** (`modules/dynamic_priority.py`): boosts a VM for
  waiting longer, approaching its deadline, or having a shorter period.
- **Workload prediction** (`modules/workload_prediction.py`): uses a moving
  average of recent ready-queue sizes. Under predicted heavy load, it gives a
  bounded bonus to VMs with less remaining work.
- **Energy model** (`modules/energy_model.py`): applies an estimated power
  penalty based on workload type. It is a proxy, not a physical measurement.

The hybrid still calls the same RL update method, so the RL component
continues learning rather than becoming a fixed formula.

## 6. Fair experiment design

`evaluation/experiments.py` creates one workload for each configuration and
seed, then sends a fresh copy to every scheduler:

```python
workload = generate_workload(num_vms, workload_type, seed)
result = sim.run(fresh_copy(workload), scheduler)
```

Using `fresh_copy()` is important because one scheduler must not modify the
VM state seen by another scheduler.

The full experiment sweeps over:

- CPU configurations,
- VM counts,
- workload types,
- random seeds,
- all four schedulers.

Results are stored as raw per-run rows and averages across seeds.

## 7. Metrics used to compare schedulers

`evaluation/metrics.py` calculates:

- **Average waiting time**: time spent waiting before completion.
- **Average turnaround time**: completion time minus arrival time.
- **Average response time**: first dispatch time minus arrival time.
- **CPU utilization**: busy CPU time divided by total simulation time.
- **Throughput**: completed VMs divided by total simulation time.
- **Deadline misses**: number of VMs completed after their deadlines.
- **Fairness**: Jain's fairness index using `1 / (1 + waiting_time)`.
- **Estimated energy**: sum of workload power proxy multiplied by runtime.
- **Context switches**: number of times execution changes from one VM to
  another.
- **Estimated scheduling overhead**: context switches multiplied by a fixed
  per-switch estimate.

The energy and scheduling-overhead values are explicitly estimated because
the project is a simulation and does not measure physical hardware.

## 8. How to demonstrate the implementation

Run the menu with:

```text
python main.py
```

For a presentation, the most useful demonstrations are:

1. Run a single comparison to show the metric table for all schedulers.
2. View RL decisions to show exploration, exploitation, Q-values, and
   rewards.
3. Generate a Gantt chart to show how each scheduler orders VM execution.
4. Run the full experiment to generate averaged CSV summaries and plots.

## 9. Short presentation conclusion

The implementation separates **decision-making** from **execution**. The
shared simulator provides identical CPU mechanics, while each scheduler
provides a different policy for selecting the next VM. The project progresses
from fixed rules (PRR and PRM), to learning (contextual bandit), to the
proposed hybrid that combines learning, dynamic priority, workload
prediction, and estimated energy awareness.
