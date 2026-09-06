"""
modules/energy_model.py
========================
ESTIMATED energy model.

IMPORTANT (academic honesty): this does NOT measure real hardware power.
There is no physical measurement involved anywhere in this project. This
module produces a synthetic, explainable proxy for "energy" so that the
Proposed Hybrid Scheduler has something concrete to reason about when it
tries to avoid unnecessary CPU usage. All energy figures reported anywhere
in this project (plots, README, viva notes) MUST be labelled "estimated".

Model:
    energy(vm, run_time) = POWER[vm.workload_type] * run_time

which is the simplest possible physically-motivated proxy: energy = power x
time, where "power" is just a per-workload-type constant standing in for
"how CPU-intensive this kind of task typically is" (e.g. a cpu_heavy VM is
assumed to draw more estimated power per tick than a light one).
"""

from config import ESTIMATED_POWER_PER_TICK, IDLE_POWER_PER_TICK
from models.cpu_config import CPUConfig, get_cpu_config
from models.vm import VM


def estimate_energy(vm: VM, run_time: float, cpu_config: CPUConfig = None) -> float:
    """Estimated energy for elapsed simulated runtime, never physical power."""
    power = ESTIMATED_POWER_PER_TICK.get(vm.workload_type, 1.5)
    return power * run_time * get_cpu_config(cpu_config).estimated_energy_factor


def estimate_power_rate(vm: VM) -> float:
    """Estimated instantaneous power draw (units/tick) if `vm` were running now."""
    return ESTIMATED_POWER_PER_TICK.get(vm.workload_type, 1.5)


def idle_energy(duration: float) -> float:
    """Estimated energy consumed while the CPU is idle for `duration` ticks."""
    return IDLE_POWER_PER_TICK * duration
