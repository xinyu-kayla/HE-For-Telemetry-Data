"""Multiplicative homomorphic experiment."""

import time
import numpy as np
from typing import List

from core.base import HEScheme
from core.operations import RoutingOperation, OperationType
from core.network import NetworkSimulator
from metrics.experiment_metrics import ExperimentMetrics
from metrics.collector import MetricsCollector
from experiments.base_experiment import BaseExperiment


class MultiplicativeExperiment(BaseExperiment):
    """Runs multiplicative homomorphic experiments."""

    def __init__(self, num_routers: int = 8, num_fields: int = 2):
        super().__init__(num_routers, num_fields)
        self.multiplicative_schemes = ['RSA', 'ElGamal', 'BGV', 'BFV', 'CKKS', 'GSW']

    def _generate_router_operations(self) -> List[List[RoutingOperation]]:
        ops_per_router = []
        for router_idx in range(self.num_routers):
            mod = router_idx % 3
            if mod == 0:
                factor = np.random.uniform(0.5, 2.0)
                ops = [RoutingOperation(OperationType.MULTIPLY_CONSTANT, factor)]
            elif mod == 1:
                ops = [RoutingOperation(OperationType.MULTIPLY_CIPHERTEXT)]
            else:
                ops = [RoutingOperation(OperationType.MULTIPLY_CONSTANT, np.random.uniform(0.9, 1.1))]
            ops_per_router.append(ops)
        return ops_per_router

    def _compute_expected_values(self, initial_value: float,
                                  router_operations: List[List[RoutingOperation]]) -> List[float]:
        expected = [initial_value]
        current = initial_value
        for ops in router_operations:
            for op in ops:
                if op.op_type == OperationType.MULTIPLY_CONSTANT:
                    current *= op.value
                elif op.op_type == OperationType.MULTIPLY_CIPHERTEXT:
                    current = current * current
            expected.append(current)
        return expected

    def run_single_experiment(self, scheme: HEScheme,
                              initial_value: float,
                              router_operations: List[List[RoutingOperation]],
                              run_id: int = 0) -> ExperimentMetrics:
        metrics = ExperimentMetrics(scheme_name=scheme.name,
                                    num_hops=self.num_routers,
                                    operations_per_hop=1)
        try:
            sim = NetworkSimulator(scheme)
            sim.initialize(self.num_routers)

            if scheme.name == "GSW":
                return self._run_gsw(scheme, router_operations, sim, metrics)

            secondary = initial_value * 1.5
            initial_plaintexts = [initial_value, secondary] + [1.0] * (self.num_fields - 2)

            temp_ct0 = scheme.encrypt(initial_value, sim.keypair)
            temp_ct1 = scheme.encrypt(secondary, sim.keypair)
            expected_values = self._compute_expected_values(initial_value, router_operations)

            for hop_idx, ops in enumerate(router_operations):
                hop_start = time.perf_counter()
                for op in ops:
                    if op.op_type == OperationType.MULTIPLY_CONSTANT:
                        if scheme.supports_multiplicative():
                            temp_ct0 = scheme.multiply_constant(temp_ct0, op.value, sim.keypair)
                    elif op.op_type == OperationType.MULTIPLY_CIPHERTEXT:
                        if scheme.supports_multiplicative():
                            temp_ct0 = scheme.multiply(temp_ct0, temp_ct1, sim.keypair)
                hop_latency = time.perf_counter() - hop_start

                computed = scheme.decrypt(temp_ct0, sim.keypair)
                expected = expected_values[hop_idx + 1]
                noise = scheme.get_noise_budget(temp_ct0)
                metrics.record_hop(hop_idx, computed, expected, noise=noise, latency=hop_latency)

            packet = sim.send_packet(initial_plaintexts, router_operations)
            final_computed = sim.get_final_value(packet)
            final_expected = expected_values[-1]
            metrics.final_computed = final_computed
            metrics.final_expected = final_expected
            metrics.final_error = abs(final_computed - final_expected)
            metrics.final_relative_error = metrics.final_error / (abs(final_expected) + 1e-10)
            metrics.success = True

        except Exception as e:
            metrics.success = False
            metrics.failure_reason = str(e)
            print(f"Error in {scheme.name}: {e}")

        metrics.finalize()
        return metrics

    def _run_gsw(self, scheme, router_operations, sim, metrics):
        """Boolean multiplicative circuit for GSW."""
        m1, m2 = 1, 0
        ct1 = scheme.encrypt(m1, sim.keypair)
        ct2 = scheme.encrypt(m2, sim.keypair)
        expected = m1

        for hop_idx, ops in enumerate(router_operations):
            for op in ops:
                if op.op_type == OperationType.MULTIPLY_CONSTANT:
                    const_val = int(op.value) % 2
                    const_ct = scheme.encrypt(const_val, sim.keypair)
                    ct1 = scheme.multiply(ct1, const_ct, sim.keypair)
                    expected = (expected * const_val) % 2
                elif op.op_type == OperationType.MULTIPLY_CIPHERTEXT:
                    ct1 = scheme.multiply(ct1, ct2, sim.keypair)
                    expected = (expected * m2) % 2
            computed = scheme.decrypt(ct1, sim.keypair)
            noise = scheme.get_noise_budget(ct1)
            metrics.record_hop(hop_idx, computed, expected, noise=noise, latency=0.001)

        packet = sim.send_packet([m1, m2] + [0.0] * (self.num_fields - 2), router_operations)
        final_computed = sim.get_final_value(packet)
        metrics.final_computed = final_computed
        metrics.final_expected = expected
        metrics.final_error = abs(final_computed - expected)
        metrics.final_relative_error = metrics.final_error / (abs(expected) + 1e-10)
        metrics.success = True
        metrics.finalize()
        return metrics

    def run_suite(self, num_runs_per_scheme: int, initial_value: float,
                  show_progress: bool = True, **kwargs) -> MetricsCollector:
        return super().run_suite(num_runs_per_scheme, initial_value,
                                 self.multiplicative_schemes, show_progress, **kwargs)