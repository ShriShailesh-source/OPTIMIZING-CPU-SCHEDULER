# Overall Scheduler Summary

All values are calculated from simulator output. Energy and scheduling overhead are estimated proxies, not physical measurements.

| scheduler | avg_waiting_time | avg_turnaround_time | avg_response_time | cpu_utilization | throughput | deadline_miss_rate | fairness_jain_index | estimated_energy | context_switches | estimated_scheduling_overhead |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Contextual Bandit RL | 423.3025 | 443.8372 | 117.6098 | 0.8833 | 0.0595 | 0.6403 | 0.433 | 1565.3269 | 165.424 | 8.2712 |
| PRM | 284.0644 | 304.5991 | 272.3429 | 0.8833 | 0.0595 | 0.5621 | 0.3828 | 1565.3269 | 41.432 | 2.0716 |
| PRR | 295.2117 | 315.7463 | 243.8021 | 0.8833 | 0.0595 | 0.5873 | 0.4002 | 1565.3269 | 169.792 | 8.4896 |
| Proposed Hybrid | 340.0672 | 360.6019 | 156.8568 | 0.8833 | 0.0595 | 0.645 | 0.4156 | 1565.3269 | 167.28 | 8.364 |

