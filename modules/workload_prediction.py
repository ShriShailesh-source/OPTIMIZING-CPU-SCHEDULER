"""
modules/workload_prediction.py
===============================
Simple, explainable Workload Prediction (our proposed extension).

We do NOT claim any advanced ML model here. This is deliberately a
lightweight moving average over the recent number of ready (contending)
VMs, used as a proxy for "how loaded is the system about to be".

    historical_load  = [ready_count(t-k), ..., ready_count(t-1)]
    predicted_load   = mean(historical_load)          (moving average)

The predicted load is turned into a scheduling *bias*:

  - predicted load HIGH (system about to be congested)
      -> bias the hybrid scheduler towards SHORTEST-REMAINING-TIME-like
         behaviour, since draining short jobs first reduces mean waiting
         time under heavy contention (classic SRTF result).
  - predicted load LOW (system about to be idle/light)
      -> bias towards respecting priority/deadlines as given, since there
         is little contention to optimize away.

This keeps the "prediction -> decision" chain fully transparent:

    Current workload -> Historical window -> Predicted load -> Scheduling bias
"""

from collections import deque
from config import PREDICTION_WINDOW


class WorkloadPredictor:
    def __init__(self, window: int = PREDICTION_WINDOW):
        self.window = window
        self.history = deque(maxlen=window)

    def observe(self, ready_count: int):
        self.history.append(ready_count)

    def predicted_load(self) -> float:
        """Moving-average predicted number of contending VMs in the near future."""
        if not self.history:
            return 0.0
        return sum(self.history) / len(self.history)

    def load_level(self) -> str:
        """Bucket the predicted load into a human-readable level (for debug prints)."""
        p = self.predicted_load()
        if p <= 1.5:
            return "light"
        elif p <= 4:
            return "normal"
        else:
            return "heavy"

    def srtf_bias(self, vm, current_time: float) -> float:
        """
        A small, bounded bias favouring VMs with less remaining work, scaled by
        how loaded the (predicted) near future is. Returns a value that is
        ADDED to a priority/score -- i.e. this is a bonus, not a hard rule,
        so it never overrides a hard deadline/priority by itself.
        """
        predicted = self.predicted_load()
        if predicted <= 0:
            return 0.0
        # normalize remaining time bonus: less remaining work -> bigger bonus
        # scaled by how heavily loaded we predict the system to be.
        load_factor = min(predicted / 5.0, 1.0)   # saturate at "5 contending VMs"
        remaining_penalty = vm.remaining_time / max(vm.burst_time, 1.0)
        bonus = load_factor * (1.0 - remaining_penalty)
        return round(bonus, 4)

    def explain(self, vm, current_time: float) -> dict:
        return {
            "history_window": list(self.history),
            "predicted_load": round(self.predicted_load(), 3),
            "load_level": self.load_level(),
            "srtf_bias_for_this_vm": self.srtf_bias(vm, current_time),
        }
