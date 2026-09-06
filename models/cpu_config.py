"""Explicit, simulated CPU execution environments.

These values are illustrative simulation parameters. They are not hardware
benchmarks and do not represent measured ARM, x86, or RISC-V processors.
"""

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class CPUConfig:
    name: str
    execution_speed_factor: float
    estimated_energy_factor: float

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("CPU configuration name must not be empty")
        if self.execution_speed_factor <= 0:
            raise ValueError("execution_speed_factor must be greater than zero")
        if self.estimated_energy_factor <= 0:
            raise ValueError("estimated_energy_factor must be greater than zero")


# Deliberately modest, illustrative factors so CPU configuration is a visible
# experimental factor without pretending to model physical processor results.
CPU_CONFIGS = {
    "ARM-like": CPUConfig("ARM-like", 0.85, 0.95),
    "x86-like": CPUConfig("x86-like", 1.00, 1.00),
    "RISC-V-like": CPUConfig("RISC-V-like", 0.92, 1.00),
}
CPU_CONFIG_NAMES = tuple(CPU_CONFIGS)
DEFAULT_CPU_CONFIG = "x86-like"


def get_cpu_config(config: Union[str, CPUConfig, None] = None) -> CPUConfig:
    """Resolve a registered name or validate an explicit CPUConfig."""
    if config is None:
        config = DEFAULT_CPU_CONFIG
    if isinstance(config, CPUConfig):
        return config
    try:
        return CPU_CONFIGS[config]
    except (KeyError, TypeError) as exc:
        valid = ", ".join(CPU_CONFIG_NAMES)
        raise ValueError(f"unknown CPU configuration {config!r}; choose one of {valid}") from exc