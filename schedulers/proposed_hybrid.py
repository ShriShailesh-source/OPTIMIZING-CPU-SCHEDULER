"""
schedulers/proposed_hybrid.py
==============================
OUR PROPOSED SYSTEM: Context-Aware Hybrid Reinforcement Learning Scheduler
                     — HYPER-OPTIMIZED V5 (Density-Aware SRTF) —

Combines:
    1. Linear Contextual Bandit RL exploration (Q-learning)
    2. Dynamic Priority with Aging & Deadline Urgency
    3. Contention-Aware Absolute SRTF Workload Prediction
    4. Power-Rate Regularization
    5. Prioritized Run-to-Completion Hysteresis (Sticky completion to suppress context switching)
    6. Dual-Tier Fast Path with Single-Shot Run-to-Finish Quantum Allocation
    7. Anti-Chatter Affinity: prevents ping-pong switches between short tasks
    8. Vectorized/Cached Scoring: batch dot-product scoring
    9. Density-aware completion hysteresis, first-touch dispatch, and
       nonlinear anti-starvation aging
"""

import math
import numpy as np

from config import HYBRID_WEIGHTS, DEFAULT_TIME_QUANTUM
from schedulers.contextual_bandit import ContextualBanditScheduler, featurize
from modules.dynamic_priority import effective_priority
from modules.workload_prediction import WorkloadPredictor
from modules.energy_model import estimate_power_rate

# Fast-path threshold: tasks shorter than this qualify for fast-track dispatch
_FAST_PATH_THRESHOLD = 6.0

# Adaptive quantum bounds (ticks)
_Q_MIN = 4      # baseline floor prevents slicing fragmentation
_Q_MAX = 8      # compute-heavy / low-contention regime
_Q_BASE = DEFAULT_TIME_QUANTUM

# Keep the nonlinear guardrail on the same interpretable scale as the
# existing linear priority-aging coefficient.
_AGING_ALPHA = 0.15


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

        # Pre-built weight vector for vectorized scoring (rl, prio, bias, power)
        w = self.weights_hybrid
        self._w_vec = np.array([w["rl"], w["priority"], 1.8, -0.15], dtype=np.float64)

    # ------------------------------------------------------------------
    # Helper: compute adaptive quantum based on load & task characteristics
    # ------------------------------------------------------------------
    def _adaptive_quantum(self, ready_queue, pred_load):
        """
        Return suggested quantum slice.
        - Heavy compute batches in low contention get expanded slices (_Q_MAX)
        - Otherwise maintains non-fragmenting baseline (_Q_BASE = 4)
        """
        n = len(ready_queue)
        avg_remaining = (sum(v.remaining_time for v in ready_queue) / n) if n else _Q_BASE

        if n <= 3 and avg_remaining >= 10:
            return _Q_MAX
        return _Q_BASE

    @staticmethod
    def _completion_slack(ready_count, quantum):
        """Return density-aware completion allowance in scheduler ticks."""
        if ready_count <= 4:
            return 2.5 * quantum
        if ready_count <= 10:
            return 1.8 * quantum
        return 1.2 * quantum

    @staticmethod
    def _aging_bonus(vm):
        """Nonlinear anti-starvation guardrail for tasks deferred by SRTF."""
        return _AGING_ALPHA * (max(vm.waiting_time, 0.0) / 20.0) ** 1.25

    def _record_choice(self, chosen, current_time, ready_count):
        """Keep RL bookkeeping uniform across fast scheduling paths."""
        self._last_vm_id = chosen.vm_id
        self._last_features = featurize(chosen, current_time, ready_count)
        self.epsilon = max(self.epsilon * 0.995, 0.02)

    # ------------------------------------------------------------------
    # Main scheduling decision
    # ------------------------------------------------------------------
    def select(self, ready_queue, current_time, quantum, sim):
        self.predictor.observe(len(ready_queue))
        pred_load = self.predictor.predicted_load()
        load_factor = min(pred_load / 5.0, 1.0)
        last_id = getattr(self, "_last_vm_id", None)

        suggested_q = self._adaptive_quantum(ready_queue, pred_load)
        self._suggested_quantum = suggested_q

        # ── 1. Priority 1: Density-Aware Run-to-Completion Hysteresis ───────────
        # Retain a near-complete VM, but contract the allowance under contention so
        # the queue drains instead of letting a long tail monopolize the CPU.
        if last_id is not None:
            for v in ready_queue:
                if (v.vm_id == last_id and
                        v.remaining_time <= self._completion_slack(len(ready_queue), quantum)):
                    self._record_choice(v, current_time, len(ready_queue))
                    # A qualifying VM receives one sufficient slice, guaranteeing completion.
                    v._recommended_quantum = max(quantum, math.ceil(v.remaining_time))
                    return v

        # ── 2. Priority 2: Dual-Tier Fast Path with Anti-Chatter Affinity ─────
        # Tasks with remaining work < 6 ticks qualify for fast dispatch.
        fast_candidates = [v for v in ready_queue if v.remaining_time < _FAST_PATH_THRESHOLD]
        if fast_candidates:
            # Affinity check: if the last-run VM is among fast candidates, stick to it
            current_fast = [v for v in fast_candidates if v.vm_id == last_id]
            if current_fast:
                chosen = current_fast[0]
            else:
                chosen = min(fast_candidates, key=lambda v: v.remaining_time)

            self._record_choice(chosen, current_time, len(ready_queue))
            # Run-to-finish: grant enough quantum to finish without mid-execution preemption
            chosen._recommended_quantum = max(quantum, math.ceil(chosen.remaining_time))
            return chosen

        # ── 3. Priority 3: Vectorized / Batch Scoring for General Queue ──────
        n = len(ready_queue)
        ids   = np.empty(n, dtype=np.int64)
        rl_v  = np.empty(n, dtype=np.float64)
        pr_v  = np.empty(n, dtype=np.float64)
        bi_v  = np.empty(n, dtype=np.float64)
        pw_v  = np.empty(n, dtype=np.float64)
        ft_v  = np.empty(n, dtype=np.float64)

        feats_by_id = {}
        for i, v in enumerate(ready_queue):
            ids[i] = v.vm_id
            feats = featurize(v, current_time, n)
            feats_by_id[v.vm_id] = feats
            rl_v[i]  = self.q_value(feats)
            prio, _  = effective_priority(v, current_time, explain=True)
            pr_v[i]  = prio + self._aging_bonus(v)
            # Hyperbolic SRTF: super-linear decay sharply favors 1--4 tick tails.
            bi_v[i]  = load_factor * (32.0 / (1.0 + v.remaining_time ** 1.15))
            pw_v[i]  = estimate_power_rate(v)
            # First-touch is a bounded tie-breaker, not an unconditional
            # preemption.  This preserves low response latency without
            # repeatedly displacing backlog-draining work.
            ft_v[i] = 1.0 if v.response_time is None else 0.0

        def _vnorm(arr):
            lo, hi = arr.min(), arr.max()
            if hi - lo < 1e-9:
                return np.full_like(arr, 0.5)
            return (arr - lo) / (hi - lo)

        feature_matrix = np.stack([_vnorm(rl_v), _vnorm(pr_v),
                                   _vnorm(bi_v), _vnorm(pw_v)], axis=1)
        raw_scores = feature_matrix @ self._w_vec + (0.12 * ft_v)

        # ── 4. Epsilon-Greedy Selection ──────────────────────────────────
        if self.rng.random() < self.epsilon:
            chosen_idx = self.rng.randint(0, n - 1)
            mode = "explore"
        else:
            chosen_idx = int(np.argmax(raw_scores))
            mode = "exploit"

        chosen_id = int(ids[chosen_idx])
        chosen = ready_queue[chosen_idx]

        self._last_features = feats_by_id[chosen_id]
        self._last_vm_id = chosen_id
        self.epsilon = max(self.epsilon * 0.995, 0.02)
        chosen._recommended_quantum = suggested_q

        if self.debug:
            scores_dict = {int(ids[i]): round(float(raw_scores[i]), 3) for i in range(n)}
            print(f"\n--- Hybrid decision @ t={current_time:.2f} (mode={mode}) ---")
            print(f"Predicted load: {pred_load:.2f}  |  Adaptive Q: {suggested_q}")
            print("Combined scores:     ", scores_dict)
            print(f"Selected VM = VM{chosen_id}")

        return chosen
