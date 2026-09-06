"""Automated checks for the simulated CPU configuration factor."""

import unittest

from evaluation.experiments import run_full_experiment, run_single_comparison
from models.cpu_config import CPUConfig, CPU_CONFIG_NAMES, get_cpu_config
from simulation.simulator import Simulator
from simulation.workload_generator import generate_workload, fresh_copy
from schedulers.prr import PRRScheduler


class CPUConfigurationTests(unittest.TestCase):
    def test_configuration_validation(self):
        with self.assertRaises(ValueError):
            CPUConfig("bad", 0, 1)
        with self.assertRaises(ValueError):
            CPUConfig("bad", 1, -1)
        with self.assertRaises(ValueError):
            get_cpu_config("not-registered")

    def test_same_configuration_is_reproducible(self):
        first, _ = run_single_comparison(8, "normal", 123, cpu_config="ARM-like")
        second, _ = run_single_comparison(8, "normal", 123, cpu_config="ARM-like")
        self.assertEqual(first.to_dict("records"), second.to_dict("records"))

    def test_configurations_change_simulated_timing(self):
        results = {}
        for name in CPU_CONFIG_NAMES:
            vm = generate_workload(1, "normal", 17)[0]
            result = Simulator(cpu_config=name).run([vm], PRRScheduler())
            results[name] = result.total_time
        self.assertGreater(len(set(results.values())), 1)

    def test_workload_is_reused_fairly_across_configurations(self):
        workload = generate_workload(6, "bursty", 19)
        signatures = []
        for name in CPU_CONFIG_NAMES:
            result = Simulator(cpu_config=name).run(fresh_copy(workload), PRRScheduler())
            signatures.append([(vm.vm_id, vm.arrival_time, vm.burst_time, vm.priority,
                                vm.period, vm.workload_type, vm.deadline_relative)
                               for vm in sorted(result.vms, key=lambda item: item.vm_id)])
        self.assertTrue(all(signature == signatures[0] for signature in signatures))

    def test_all_schedulers_and_expected_small_run_count(self):
        raw, averaged = run_full_experiment(
            vm_counts=[5], workload_types=["normal"], seeds=[1], verbose=False
        )
        self.assertEqual(len(raw), 3 * 1 * 1 * 4)
        self.assertEqual(len(averaged), 3 * 4)
        self.assertEqual(set(raw["cpu_config"]), set(CPU_CONFIG_NAMES))
        self.assertEqual(set(raw["scheduler"]), {
            "PRR", "PRM", "Contextual Bandit RL", "Proposed Hybrid"
        })


if __name__ == "__main__":
    unittest.main()
