# Overall Scheduler Summary

All values are calculated from simulator output. Energy and scheduling overhead are estimated proxies, not physical measurements.

| cpu_config | scheduler | avg_waiting_time | avg_turnaround_time | avg_response_time | cpu_utilization | throughput | deadline_miss_rate | fairness_jain_index | estimated_energy | context_switches | estimated_scheduling_overhead |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| x86-like | Contextual Bandit RL | 423.3025 | 443.8372 | 117.6098 | 0.8833 | 0.0595 | 0.6403 | 0.433 | 1565.3269 | 165.424 | 8.2712 |
| x86-like | PRM | 284.0644 | 304.5991 | 272.3429 | 0.8833 | 0.0595 | 0.5621 | 0.3828 | 1565.3269 | 41.432 | 2.0716 |
| x86-like | PRR | 295.2117 | 315.7463 | 243.8021 | 0.8833 | 0.0595 | 0.5873 | 0.4002 | 1565.3269 | 169.792 | 8.4896 |
| x86-like | Proposed Hybrid | 228.5515 | 249.0862 | 132.4587 | 0.8833 | 0.0595 | 0.5561 | 0.4171 | 1565.3269 | 71.56 | 3.578 |

