"""
schedulers/proposed_hybrid.py
==============================
OUR PROPOSED SYSTEM: Hybrid Intelligent Scheduler.

Extends the Contextual Bandit RL scheduler (schedulers/contextual_bandit.py)
with three additional, explainable modules:

    A. Workload Prediction   (modules/workload_prediction.py)
    B. Dynamic Priority      (modules/dynamic_priority.py)
    C. Estimated Energy      (modules/energy_model.py)

FINAL DECISION (per candidate VM v, at time t):

    score(v) = W_rl         * normalized_Q_rl(v)
             + W_priority   * normalized_effective_priority(v, t)
             + W_prediction * srtf_bias(v, t)            [workload-prediction term]
             - W_energy     * normalized_estimated_power(v)

    selected = argmax_v score(v)      (epsilon-greedy, same as the bandit,
                                        so the hybrid scheduler keeps learning)

All four terms and their weights are printed in debug mode in the exact
layout requested for the viva demo (see `select(..., debug=True)`).

The RL sub-component (weights `w`) is STILL updated every step using the
same reward function as the plain bandit scheduler, so "does the RL part
still learn" can be verified independently of the extra modules.
"""

import numpy as np

from config import HYBRID_WEIGHTS
from schedulers.contextual_bandit import ContextualBanditScheduler, featurize
from modules.dynamic_priority import effective_priority
from modules.workload_prediction import WorkloadPredictor
from modules.energy_model import estimate_power_rate


def _normalize(values: dict) -> dict:
    """Min-max normalize a dict of {id: value} to [0, 1]; flat input -> all 0.5."""
    if not values:
        return {}
    lo, hi = min(values.values()), max(values.values())
    if hi - lo < 1e-9:
        return {k: 0.5 for k in values}
    return {k: (v - lo) / (hi - lo) for k, v in values.items()}


class ProposedHybridScheduler(ContextualBanditScheduler):
    name = "Proposed Hybrid Intelligent Scheduler"

    def __init__(self, weights=None, debug=False, **kwargs):
        super().__init__(debug=debug, **kwargs)
        self.weights_hybrid = dict(weights or HYBRID_WEIGHTS)
        self.predictor = WorkloadPredictor()

    def select(self, ready_queue, current_time, quantum, sim):
        self.predictor.observe(len(ready_queue))

        rl_q = {}
        eff_prio = {}
        pred_bias = {}
        power_rate = {}
        feats_by_id = {}

        for v in ready_queue:
            feats = featurize(v, current_time, len(ready_queue))
            feats_by_id[v.vm_id] = feats
            rl_q[v.vm_id] = self.q_value(feats)
            eff_prio[v.vm_id], _ = effective_priority(v, current_time, explain=True)
            pred_bias[v.vm_id] = self.predictor.srtf_bias(v, current_time)
            power_rate[v.vm_id] = estimate_power_rate(v)

        norm_rl = _normalize(rl_q)
        norm_prio = _normalize(eff_prio)
        norm_power = _normalize(power_rate)
        # pred_bias is already ~[0,1] by construction, no need to renormalize

        w = self.weights_hybrid
        scores = {}
        for v in ready_queue:
            vid = v.vm_id
            scores[vid] = (
                w["rl"] * norm_rl[vid]
                + w["priority"] * norm_prio[vid]
                + w["prediction"] * pred_bias.get(vid, 0.0)
                - w["energy"] * norm_power[vid]
            )

        if self.rng.random() < self.epsilon:
            chosen_id = self.rng.choice(list(scores.keys()))
            mode = "explore"
        else:
            chosen_id = max(scores, key=scores.get)
            mode = "exploit"

        chosen = next(v for v in ready_queue if v.vm_id == chosen_id)
        self._last_features = feats_by_id[chosen_id]
        self._last_vm_id = chosen_id
        self.epsilon = max(self.epsilon * 0.995, 0.02)

        if self.debug:
            print(f"\n--- Hybrid decision @ t={current_time:.2f} (mode={mode}) ---")
            print(f"Predicted load: {self.predictor.predicted_load():.2f} "
                  f"({self.predictor.load_level()})")
            print("Effective Priorities:", {k: round(v_, 2) for k, v_ in eff_prio.items()})
            print("RL scores (raw Q):   ", {k: round(v_, 3) for k, v_ in rl_q.items()})
            print("Prediction bias:     ", {k: round(v_, 3) for k, v_ in pred_bias.items()})
            print("Estimated power rate:", {k: round(v_, 2) for k, v_ in power_rate.items()})
            print("Combined scores:     ", {k: round(v_, 3) for k, v_ in scores.items()})
            print(f"Selected VM = VM{chosen_id}")

        return chosen
