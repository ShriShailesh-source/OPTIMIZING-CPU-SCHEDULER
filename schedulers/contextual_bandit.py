"""
schedulers/contextual_bandit.py
================================
Algorithm 3: Contextual Bandit Reinforcement Learning scheduler.

Deliberately lightweight -- NO deep neural network. This is a linear
contextual bandit with epsilon-greedy exploration, which is the standard
"simple and explainable" choice for this kind of problem:

    Q(vm) = w . features(vm, t)          (a single dot product -- fully
                                           inspectable, print `w` any time)

THE LOOP (exactly as required):
    1. Observe state   -> featurize() below, one feature vector per
                           candidate VM in the ready queue
    2. Select action   -> epsilon-greedy over Q(vm) for each candidate
    3. Execute          -> handled by the simulation engine
    4. Calculate reward -> reward() below, called by the engine via
                           on_decision_result()
    5. Update policy    -> online gradient step on `w` (Widrow-Hoff /
                           LMS rule): w += lr * (reward - Q) * features
    6. Repeat            -> engine's main loop

STATE / CONTEXT (per candidate VM), all normalized to roughly [0, 1]:
    - cpu utilization proxy (system-level: ready_queue_len / vm_count-ish)
    - vm priority (normalized)
    - waiting time (normalized by quantum)
    - remaining execution time (normalized by its own burst time)
    - deadline urgency (0 = far away, 1 = at/after deadline)
    - task period (normalized, inverted so "urgent/short period" -> big)
    - workload type (numeric code / 4, just to give the model a hint)

ACTIONS: pick exactly one VM (out of however many are ready) to run next.
Because the candidate set changes size every decision, this is implemented
as a *contextual* bandit over (state, vm) pairs rather than a fixed
discrete action space -- score every candidate with the same shared weight
vector and argmax (epsilon-greedy).

REWARD: see reward() docstring below.
"""

import random

import numpy as np

from config import RL_LEARNING_RATE, RL_EPSILON_START, RL_EPSILON_MIN, RL_EPSILON_DECAY

WORKLOAD_CODE = {"light": 0, "normal": 1, "cpu_heavy": 2, "bursty": 3, "mixed": 4}


def featurize(vm, current_time, ready_queue_len) -> np.ndarray:
    norm_wait = min(vm.waiting_time / 20.0, 3.0)
    norm_priority = vm.priority / 10.0
    norm_remaining = vm.remaining_time / max(vm.burst_time, 1e-6)
    ttd = vm.time_to_deadline(current_time)
    urgency = 0.0 if vm.deadline_relative <= 0 else max(0.0, min(1.5, 1.0 - ttd / vm.deadline_relative))
    norm_period = 1.0 / max(vm.period / 20.0, 0.1)   # shorter period -> larger value
    workload_code = WORKLOAD_CODE.get(vm.workload_type, 1) / 4.0
    congestion = min(ready_queue_len / 10.0, 1.0)

    return np.array([
        norm_wait, norm_priority, norm_remaining,
        urgency, norm_period, workload_code, congestion,
    ], dtype=float)


class ContextualBanditScheduler:
    name = "Contextual Bandit RL"

    def __init__(self, lr=RL_LEARNING_RATE, epsilon=RL_EPSILON_START, debug=False, n_features=7):
        self.lr = lr
        self.epsilon = epsilon
        self.debug = debug
        self.weights = np.zeros(n_features, dtype=float)
        self._last_features = None
        self._last_vm_id = None
        self.decision_trace = []   # for "View RL decisions" CLI option

    def q_value(self, features: np.ndarray) -> float:
        return float(np.dot(self.weights, features))

    def select(self, ready_queue, current_time, quantum, sim):
        feats = {v.vm_id: featurize(v, current_time, len(ready_queue)) for v in ready_queue}
        q_values = {vid: self.q_value(f) for vid, f in feats.items()}

        if random.random() < self.epsilon:
            chosen_id = random.choice(list(q_values.keys()))
            mode = "explore"
        else:
            chosen_id = max(q_values, key=q_values.get)
            mode = "exploit"

        chosen = next(v for v in ready_queue if v.vm_id == chosen_id)
        self._last_features = feats[chosen_id]
        self._last_vm_id = chosen_id

        if self.debug:
            trace = {
                "time": round(current_time, 2),
                "mode": mode,
                "epsilon": round(self.epsilon, 3),
                "q_values": {vid: round(q, 3) for vid, q in q_values.items()},
                "selected_vm": chosen_id,
            }
            self.decision_trace.append(trace)
            print(f"[RL t={trace['time']:>7}] mode={mode:<7} eps={trace['epsilon']:.3f} "
                  f"Q={trace['q_values']} -> selected VM{chosen_id}")

        # epsilon decay happens once per decision
        self.epsilon = max(RL_EPSILON_MIN, self.epsilon * RL_EPSILON_DECAY)
        return chosen

    def reward(self, vm, run_time, finished, reward_info) -> float:
        """
        Reward shaping (all effects explicitly named, per spec):

          + up to +1.0  for low waiting time this slice (inverse of wait)
          + up to +1.0  for good "system" CPU utilization (others not
                         starved: fewer other VMs waiting is rewarded less
                         directly -- captured via the `others_waiting` term
                         being penalized instead, see below)
          - proportional penalty for how many OTHER ready VMs had to wait
                         behind this decision (keeps waiting/turnaround low
                         system-wide, not just for the chosen VM)
          + +3.0        bonus if this decision COMPLETES the VM before its
                         deadline (rewards good turnaround + meeting deadlines)
          - -3.0        penalty if this decision completes the VM AFTER its
                         deadline (deadline miss)
          - small penalty proportional to `run_time` if the VM's own
                         waiting_time was already large (discourages
                         starving already-waiting tasks further)
        """
        wait_penalty = -0.05 * min(vm.waiting_time, 40.0) / 40.0
        others_penalty = -0.03 * reward_info.get("others_waiting", 0)
        r = wait_penalty + others_penalty + 0.2  # small constant reward for making progress

        if finished:
            if reward_info.get("deadline_missed"):
                r -= 3.0
            else:
                r += 3.0
            # reward shorter realized turnaround (bounded)
            if vm.turnaround_time:
                r += max(0.0, 2.0 - vm.turnaround_time / max(vm.burst_time, 1.0))
        return r

    def on_decision_result(self, vm, run_time, finished, reward_info, sim):
        r = self.reward(vm, run_time, finished, reward_info)
        if self._last_features is not None:
            q = self.q_value(self._last_features)
            # Widrow-Hoff / LMS online update
            error = r - q
            self.weights += self.lr * error * self._last_features
        if self.debug:
            print(f"           reward={r:.3f}  updated_weights={np.round(self.weights, 3)}")
