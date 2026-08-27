"""
config.py
=========
Central configuration for the CPU scheduling simulator.
Every tunable knob used anywhere in the project lives here so experiments
are reproducible and so the same workload/config can be replayed across
all four schedulers for a fair comparison.
"""

import numpy as np

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
DEFAULT_SEED = 42

# ---------------------------------------------------------------------------
# Workload generation
# ---------------------------------------------------------------------------
WORKLOAD_TYPES = ["light", "normal", "cpu_heavy", "bursty", "mixed"]

# Burst time ranges (in simulation time units / ticks) per workload type.
BURST_RANGES = {
    "light":     (2, 8),
    "normal":    (5, 20),
    "cpu_heavy": (20, 60),
    "bursty":    (2, 50),      # high variance -> "bursty/dynamic"
    "mixed":     (2, 60),      # sampled from a mixture, see workload_generator.py
}

# Inter-arrival time ranges per workload type (controls how "busy" the
# system is -- smaller inter-arrival => more contention).
ARRIVAL_GAP_RANGES = {
    "light":     (5, 15),
    "normal":    (2, 8),
    "cpu_heavy": (1, 5),
    "bursty":    (0, 10),      # can arrive in bursts (0 gap) or spread out
    "mixed":     (0, 12),
}

PRIORITY_RANGE = (1, 10)        # 1 = lowest, 10 = highest (base priority)
PERIOD_RANGE = (10, 100)        # used by PRM (rate-monotonic) and deadlines
DEADLINE_SLACK_RANGE = (1.2, 3.0)  # deadline = arrival + slack * burst_time

VM_COUNT_PRESETS = [5, 10, 20, 50, 100]

# ---------------------------------------------------------------------------
# Scheduler engine
# ---------------------------------------------------------------------------
DEFAULT_TIME_QUANTUM = 4
CONTEXT_SWITCH_OVERHEAD = 0.05   # ESTIMATED cost per context switch (ticks)

# ---------------------------------------------------------------------------
# Contextual Bandit RL scheduler
# ---------------------------------------------------------------------------
RL_LEARNING_RATE = 0.05
RL_EPSILON_START = 0.30
RL_EPSILON_MIN = 0.02
RL_EPSILON_DECAY = 0.995
RL_FEATURE_COUNT = 7   # keep in sync with schedulers/contextual_bandit.py::featurize

# ---------------------------------------------------------------------------
# Proposed Hybrid Scheduler weights (all explainable, all tunable)
# ---------------------------------------------------------------------------
HYBRID_WEIGHTS = {
    "rl": 1.0,          # weight on learned contextual-bandit score
    "priority": 1.0,    # weight on dynamic effective priority
    "energy": 0.5,      # weight (penalty) on estimated energy/power
    "prediction": 0.5,  # weight on workload-prediction adjustment
}

# Dynamic priority adjustment coefficients (modules/dynamic_priority.py)
PRIORITY_WAIT_COEFF = 0.15        # boost per unit of normalized waiting time
PRIORITY_DEADLINE_COEFF = 3.0     # boost as deadline approaches
PRIORITY_PERIOD_COEFF = 0.5       # boost for short-period (urgent) tasks

# Workload prediction (modules/workload_prediction.py)
PREDICTION_WINDOW = 5              # moving-average window (in scheduling ticks)

# ESTIMATED energy model (modules/energy_model.py) -- NOT real hardware power.
# Power draw (arbitrary energy units per tick) as a function of workload type.
ESTIMATED_POWER_PER_TICK = {
    "light":     1.0,
    "normal":    1.5,
    "cpu_heavy": 2.5,
    "bursty":    2.0,
    "mixed":     1.8,
}
IDLE_POWER_PER_TICK = 0.2

RNG = np.random.default_rng(DEFAULT_SEED)
