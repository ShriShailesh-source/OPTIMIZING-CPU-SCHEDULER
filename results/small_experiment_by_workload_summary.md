# Scheduler Summary by Workload and VM Count

All values are calculated from simulator output. Energy and scheduling overhead are estimated proxies, not physical measurements.

| workload_type | num_vms | scheduler | avg_waiting_time | avg_turnaround_time | avg_response_time | cpu_utilization | throughput | deadline_miss_rate | fairness_jain_index | estimated_energy | context_switches | estimated_scheduling_overhead |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bursty | 5 | Contextual Bandit RL | 67.0572 | 94.8628 | 15.1416 | 0.966 | 0.0361 | 0.76 | 0.7362 | 278.056 | 20.2 | 1.01 |
| bursty | 5 | PRM | 44.6368 | 72.4424 | 34.6576 | 0.966 | 0.0361 | 0.48 | 0.3248 | 278.056 | 5.0 | 0.25 |
| bursty | 5 | PRR | 45.4432 | 73.2488 | 26.8268 | 0.966 | 0.0361 | 0.56 | 0.4309 | 278.056 | 10.8 | 0.54 |
| bursty | 5 | Proposed Hybrid | 51.6628 | 79.4684 | 18.3784 | 0.966 | 0.0361 | 0.6 | 0.6346 | 278.056 | 19.0 | 0.95 |
| cpu_heavy | 5 | Contextual Bandit RL | 110.4836 | 151.9884 | 22.1312 | 0.9857 | 0.024 | 0.84 | 0.7214 | 518.81 | 30.4 | 1.52 |
| cpu_heavy | 5 | PRM | 75.6248 | 117.1296 | 57.2304 | 0.9857 | 0.024 | 0.52 | 0.2486 | 518.81 | 5.0 | 0.25 |
| cpu_heavy | 5 | PRR | 77.3972 | 118.902 | 47.3452 | 0.9857 | 0.024 | 0.64 | 0.3351 | 518.81 | 15.0 | 0.75 |
| cpu_heavy | 5 | Proposed Hybrid | 97.612 | 139.1168 | 23.8016 | 0.9857 | 0.024 | 0.76 | 0.6086 | 518.81 | 28.6 | 1.43 |
| light | 5 | Contextual Bandit RL | 0.0748 | 5.3 | 0.0748 | 0.4922 | 0.0941 | 0.0 | 0.9846 | 26.126 | 4.0 | 0.2 |
| light | 5 | PRM | 0.0748 | 5.3 | 0.0748 | 0.4922 | 0.0941 | 0.0 | 0.9846 | 26.126 | 4.0 | 0.2 |
| light | 5 | PRR | 0.0748 | 5.3 | 0.0748 | 0.4922 | 0.0941 | 0.0 | 0.9846 | 26.126 | 4.0 | 0.2 |
| light | 5 | Proposed Hybrid | 0.0748 | 5.3 | 0.0748 | 0.4922 | 0.0941 | 0.0 | 0.9846 | 26.126 | 4.0 | 0.2 |
| mixed | 5 | Contextual Bandit RL | 13.9108 | 26.4968 | 8.2008 | 0.9119 | 0.0763 | 0.4 | 0.6139 | 113.274 | 7.4 | 0.37 |
| mixed | 5 | PRM | 15.7964 | 28.3824 | 13.1668 | 0.9119 | 0.0763 | 0.44 | 0.4802 | 113.274 | 4.8 | 0.24 |
| mixed | 5 | PRR | 12.4252 | 25.0112 | 10.73 | 0.9119 | 0.0763 | 0.32 | 0.5046 | 113.274 | 5.6 | 0.28 |
| mixed | 5 | Proposed Hybrid | 10.4532 | 23.0392 | 7.1972 | 0.9119 | 0.0763 | 0.44 | 0.5552 | 113.274 | 5.8 | 0.29 |
| normal | 5 | Contextual Bandit RL | 24.5216 | 37.586 | 6.76 | 0.9289 | 0.0723 | 0.76 | 0.592 | 97.983 | 12.2 | 0.61 |
| normal | 5 | PRM | 18.6844 | 31.7488 | 12.9868 | 0.9289 | 0.0723 | 0.48 | 0.481 | 97.983 | 5.2 | 0.26 |
| normal | 5 | PRR | 20.2512 | 33.3156 | 11.0928 | 0.9289 | 0.0723 | 0.52 | 0.4445 | 97.983 | 7.6 | 0.38 |
| normal | 5 | Proposed Hybrid | 21.4764 | 34.5408 | 10.0796 | 0.9289 | 0.0723 | 0.64 | 0.5464 | 97.983 | 10.2 | 0.51 |

