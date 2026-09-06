# Overall Scheduler Summary

All values are calculated from simulator output. Energy and scheduling overhead are estimated proxies, not physical measurements.

| cpu_config | scheduler | avg_waiting_time | avg_turnaround_time | avg_response_time | cpu_utilization | throughput | deadline_miss_rate | fairness_jain_index | estimated_energy | context_switches | estimated_scheduling_overhead |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ARM-like | Contextual Bandit RL | 520.6003 | 544.7587 | 143.3919 | 0.9024 | 0.0535 | 0.6828 | 0.4004 | 1749.483 | 170.224 | 8.5112 |
| RISC-V-like | Contextual Bandit RL | 479.001 | 501.3213 | 132.5693 | 0.8929 | 0.0563 | 0.6749 | 0.413 | 1701.4423 | 168.984 | 8.4492 |
| x86-like | Contextual Bandit RL | 423.3025 | 443.8372 | 117.6098 | 0.8833 | 0.0595 | 0.6403 | 0.433 | 1565.3269 | 165.424 | 8.2712 |
| ARM-like | PRM | 346.551 | 370.7094 | 331.1572 | 0.9024 | 0.0535 | 0.6062 | 0.354 | 1749.483 | 41.32 | 2.066 |
| RISC-V-like | PRM | 315.1529 | 337.4732 | 301.3956 | 0.8929 | 0.0563 | 0.5866 | 0.3626 | 1701.4423 | 41.448 | 2.0724 |
| x86-like | PRM | 284.0644 | 304.5991 | 272.3429 | 0.8833 | 0.0595 | 0.5621 | 0.3828 | 1565.3269 | 41.432 | 2.0716 |
| ARM-like | PRR | 359.4871 | 383.6455 | 297.3768 | 0.9024 | 0.0535 | 0.6397 | 0.3964 | 1749.483 | 172.544 | 8.6272 |
| RISC-V-like | PRR | 327.3162 | 349.6364 | 269.5882 | 0.8929 | 0.0563 | 0.6248 | 0.3988 | 1701.4423 | 171.216 | 8.5608 |
| x86-like | PRR | 295.2117 | 315.7463 | 243.8021 | 0.8833 | 0.0595 | 0.5873 | 0.4002 | 1565.3269 | 169.792 | 8.4896 |
| ARM-like | Proposed Hybrid | 419.6086 | 443.767 | 190.9404 | 0.9024 | 0.0535 | 0.707 | 0.4249 | 1749.483 | 173.384 | 8.6692 |
| RISC-V-like | Proposed Hybrid | 378.5796 | 400.8999 | 173.9298 | 0.8929 | 0.0563 | 0.6681 | 0.427 | 1701.4423 | 170.096 | 8.5048 |
| x86-like | Proposed Hybrid | 340.0672 | 360.6019 | 156.8568 | 0.8833 | 0.0595 | 0.645 | 0.4156 | 1565.3269 | 167.28 | 8.364 |

