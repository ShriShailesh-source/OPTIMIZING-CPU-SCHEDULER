"""
tests_manual_validation.py
============================
Manual validation script (not pytest -- deliberately simple, printable
output you can walk through during the viva to prove the formulas are
correct on a hand-checkable example).

Run: python tests_manual_validation.py
"""

from models.vm import VM
from simulation.simulator import Simulator
from schedulers.prr import PRRScheduler
from evaluation.metrics import compute_metrics


def hand_worked_example():
    """
    3 VMs, all arrive at t=0, priorities tied (so pure Round Robin),
    quantum=4:

        VM0: burst=6
        VM1: burst=4
        VM2: burst=2

    Hand trace (quantum=4, RR order 0,1,2,0,1,2,...):
        t=0  run VM0 for 4  -> VM0 remaining=2   (t=4)
        t=4  run VM1 for 4  -> VM1 DONE          (t=8)  completion=8
        t=8  run VM2 for 2  -> VM2 DONE          (t=10) completion=10
        t=10 run VM0 for 2  -> VM0 DONE          (t=12) completion=12

    Expected:
        VM0: completion=12, turnaround=12, waiting=12-6=6,  response=0
        VM1: completion=8,  turnaround=8,  waiting=8-4=4,   response=4
        VM2: completion=10, turnaround=10, waiting=10-2=8,  response=8

        avg waiting    = (6+4+8)/3 = 6.0
        avg turnaround = (12+8+10)/3 = 10.0
        avg response   = (0+4+8)/3 = 4.0
        total busy time = 12 (never idle) -> CPU utilization = 12/12 = 1.0
        throughput = 3/12 = 0.25
    """
    vms = [
        VM(vm_id=0, arrival_time=0, burst_time=6, priority=5, period=50,
           workload_type="normal", deadline_relative=100),
        VM(vm_id=1, arrival_time=0, burst_time=4, priority=5, period=50,
           workload_type="normal", deadline_relative=100),
        VM(vm_id=2, arrival_time=0, burst_time=2, priority=5, period=50,
           workload_type="normal", deadline_relative=100),
    ]

    sim = Simulator(quantum=4, debug=False)
    result = sim.run(vms, PRRScheduler(), scheduler_name="PRR (validation)")

    print("Per-VM results:")
    for v in sorted(result.vms, key=lambda x: x.vm_id):
        print(f"  VM{v.vm_id}: completion={v.completion_time}, "
              f"turnaround={v.turnaround_time}, waiting={v.waiting_time}, "
              f"response={v.response_time}")

    metrics = compute_metrics(result)
    print("\nAggregate metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    print("\nExpected (hand-worked): avg_waiting=6.0, avg_turnaround=10.0, "
          "avg_response=4.0, cpu_utilization=1.0, throughput=0.25")

    assert metrics["avg_waiting_time"] == 6.0, "waiting time mismatch!"
    assert metrics["avg_turnaround_time"] == 10.0, "turnaround time mismatch!"
    assert metrics["avg_response_time"] == 4.0, "response time mismatch!"
    assert metrics["cpu_utilization"] == 1.0, "utilization mismatch!"
    assert metrics["throughput"] == 0.25, "throughput mismatch!"
    print("\nALL ASSERTIONS PASSED - core engine + metrics verified against hand trace.")


def deadline_detection_check():
    """A VM with an impossibly tight deadline must be flagged as missed;
    one with a generous deadline must not be."""
    vms = [
        VM(vm_id=0, arrival_time=0, burst_time=10, priority=5, period=50,
           workload_type="normal", deadline_relative=2),   # impossible: burst alone is 10
        VM(vm_id=1, arrival_time=0, burst_time=2, priority=5, period=50,
           workload_type="normal", deadline_relative=100),  # trivially met
    ]
    sim = Simulator(quantum=4, debug=False)
    result = sim.run(vms, PRRScheduler(), scheduler_name="deadline-check")
    by_id = {v.vm_id: v for v in result.vms}
    assert by_id[0].deadline_missed() is True, "expected VM0 to miss its deadline"
    assert by_id[1].deadline_missed() is False, "expected VM1 to meet its deadline"
    print("Deadline detection check PASSED.")


def identical_workload_check():
    """The same generated workload (by seed) must be identical in content
    every time it's requested, and mutating one copy must not affect another."""
    from simulation.workload_generator import generate_workload, fresh_copy
    w1 = generate_workload(10, "normal", seed=7)
    w2 = generate_workload(10, "normal", seed=7)
    for a, b in zip(w1, w2):
        assert a.arrival_time == b.arrival_time
        assert a.burst_time == b.burst_time
        assert a.priority == b.priority

    copy_a = fresh_copy(w1)
    copy_a[0].remaining_time = -999
    assert w1[0].remaining_time != -999, "fresh_copy must be a deep copy, not aliasing!"
    print("Identical-workload / deep-copy isolation check PASSED.")


if __name__ == "__main__":
    print("=" * 60)
    print("1) Hand-worked waiting/turnaround/response/utilization check")
    print("=" * 60)
    hand_worked_example()

    print("\n" + "=" * 60)
    print("2) Deadline detection check")
    print("=" * 60)
    deadline_detection_check()

    print("\n" + "=" * 60)
    print("3) Identical-workload-across-schedulers check")
    print("=" * 60)
    identical_workload_check()
