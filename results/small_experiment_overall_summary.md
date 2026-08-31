# Overall Scheduler Summary

All values are calculated from simulator output. Energy and scheduling overhead are estimated proxies, not physical measurements.

| scheduler | avg_waiting_time | avg_turnaround_time | avg_response_time | cpu_utilization | throughput | deadline_miss_rate | fairness_jain_index | estimated_energy | context_switches | estimated_scheduling_overhead |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Contextual Bandit RL | 43.2096 | 63.2468 | 10.4617 | 0.8569 | 0.0606 | 0.552 | 0.7296 | 206.8498 | 14.84 | 0.742 |
| PRM | 30.9634 | 51.0006 | 23.6233 | 0.8569 | 0.0606 | 0.384 | 0.5039 | 206.8498 | 4.8 | 0.24 |
| PRR | 31.1183 | 51.1555 | 19.2139 | 0.8569 | 0.0606 | 0.408 | 0.5399 | 206.8498 | 8.6 | 0.43 |
| Proposed Hybrid | 36.2558 | 56.293 | 11.9063 | 0.8569 | 0.0606 | 0.488 | 0.6659 | 206.8498 | 13.52 | 0.676 |

