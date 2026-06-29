"""Multiplicative homomorphic experiment (constant multiplication only)."""

import time
import numpy as np
from typing import List

from core.base import HEScheme
from core.operations import RoutingOperation, OperationType
from core.network import NetworkSimulator
from metrics.experiment_metrics import ExperimentMetrics
from metrics.collector import MetricsCollector
from experiments.base_experiment import BaseExperiment
import config


class MultiplicativeExperiment(BaseExperiment):
    """Runs multiplicative homomorphic experiments."""

    def __init__(self, num_routers: int = 8, num_fields: int = 2):
        super().__init__(num_routers, num_fields)
        self.multiplicative_schemes = ['RSA', 'ElGamal', 'BGV', 'BFV', 'CKKS', 'GSW']

    def _generate_multiplicative_factor(self, scheme: HEScheme) -> float:
        """
        Generate a multiplication factor based on the scheme's type,
        using config.OP_VALUE_RANGES['multiplicative'].
        """
        stype = self._get_scheme_type(scheme)
        ranges = config.OP_VALUE_RANGES['multiplicative']
        low, high = ranges.get(stype, (0.95, 1.05))  # fallback to float default
        if stype == 'integer':
            return float(np.random.randint(int(low), int(high) + 1))  # inclusive upper bound
        elif stype == 'boolean':
            return float(np.random.randint(int(low), int(high) + 1))  # 0 or 1
        else:  # float
            return np.random.uniform(low, high)

    def _generate_router_operations(self) -> List[List[RoutingOperation]]:
        ops_per_router = []
        for _ in range(self.num_routers):
            factor = np.random.uniform(0.95, 1.05)
            ops = [RoutingOperation(OperationType.MULTIPLY_CONSTANT, factor)]
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
            expected.append(current)
        return expected

    def run_single_experiment(self, scheme: HEScheme,
                              initial_value: float,
                              router_operations: List[List[RoutingOperation]],
                              run_id: int = 0) -> ExperimentMetrics:
        metrics = ExperimentMetrics(scheme_name=scheme.name,
                                    num_hops=self.num_routers,
                                    operations_per_hop=1)

        if scheme.name == "GSW":
            return self._run_gsw(scheme, router_operations, run_id)

        try:
            sim = NetworkSimulator(scheme)
            sim.initialize(self.num_routers)

            adapted_ops = []
            for hop_idx in range(self.num_routers):
                factor = self._generate_multiplicative_factor(scheme)
                adapted_val = self._adapt_value_for_scheme(factor, scheme)
                adapted_ops.append([RoutingOperation(OperationType.MULTIPLY_CONSTANT, adapted_val)])

            initial_plaintexts = [initial_value] + [1.0] * (self.num_fields - 1)
            temp_ct = scheme.encrypt(initial_value, sim.keypair)
            expected_values = self._compute_expected_values(initial_value, adapted_ops)

            for hop_idx, ops in enumerate(adapted_ops):
                hop_start = time.perf_counter()
                for op in ops:
                    if op.op_type == OperationType.MULTIPLY_CONSTANT:
                        if scheme.supports_multiplicative():
                            temp_ct = scheme.multiply_constant(temp_ct, op.value, sim.keypair)
                hop_latency = time.perf_counter() - hop_start

                computed = scheme.decrypt(temp_ct, sim.keypair)
                expected = expected_values[hop_idx + 1]
                noise = scheme.get_noise_budget(temp_ct)
                metrics.record_hop(hop_idx, computed, expected, noise=noise, latency=hop_latency)

            packet = sim.send_packet(initial_plaintexts, adapted_ops)  
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

    def _run_gsw(self, scheme, router_operations, run_id=0):
        """Boolean multiplicative circuit for GSW."""
        metrics = ExperimentMetrics(scheme_name=scheme.name,
                                    num_hops=self.num_routers,
                                    operations_per_hop=1)
        try:
            sim = NetworkSimulator(scheme)
            sim.initialize(self.num_routers)

            m1, m2 = 1, 0
            ct1 = scheme.encrypt(m1, sim.keypair)
            ct2 = scheme.encrypt(m2, sim.keypair)
            expected = m1
            correct_hops = 0
            total_hops = 0

            for hop_idx, ops in enumerate(router_operations):
                for op in ops:
                    if op.op_type == OperationType.MULTIPLY_CONSTANT:
                        const_val = int(op.value) % 2
                        const_ct = scheme.encrypt(const_val, sim.keypair)
                        ct1 = scheme.multiply(ct1, const_ct, sim.keypair)
                        expected = (expected * const_val) % 2
                computed = scheme.decrypt(ct1, sim.keypair)
                noise = scheme.get_noise_budget(ct1)
                bit_match = (int(computed) == expected)
                if bit_match:
                    correct_hops += 1
                total_hops += 1
                metrics.record_hop(hop_idx, computed, expected,
                                   noise=noise, latency=0.001)

            packet = sim.send_packet([m1, m2] + [0.0]*(self.num_fields-2),
                                     router_operations)
            final_computed = sim.get_final_value(packet)
            metrics.final_computed = final_computed
            metrics.final_expected = expected
            metrics.final_error = abs(final_computed - expected)
            metrics.final_relative_error = metrics.final_error / (abs(expected) + 1e-10)
            metrics.success = True
            metrics.gsw_bit_accuracy = correct_hops / total_hops if total_hops > 0 else 0.0
        except Exception as e:
            metrics.success = False
            metrics.failure_reason = str(e)
            print(f"Error in GSW: {e}")
        metrics.finalize()
        return metrics

    def run_suite(self, num_runs_per_scheme: int, initial_value: float,
                  show_progress: bool = True, **kwargs) -> MetricsCollector:
        collector = super().run_suite(num_runs_per_scheme, initial_value,
                                      self.multiplicative_schemes, show_progress, **kwargs)
        if 'GSW' in collector.results:
            gsw_runs = collector.results['GSW']
            if gsw_runs:
                acc = getattr(gsw_runs[0], 'gsw_bit_accuracy', None)
                if acc is not None:
                    print(f"\nGSW Multiplicative Bit Accuracy: {acc:.2%}")
        return collector

    def _generate_single_hop_operation(self, step: int) -> List[RoutingOperation]:
        return [RoutingOperation(OperationType.MULTIPLY_CONSTANT, 1.0)]

    def run_stress_suite(
        self,
        num_runs_per_scheme: int,
        initial_value: float,
        max_steps: int = 100,
        error_threshold: float = 0.5,
        show_progress: bool = True
    ) -> MetricsCollector:
        from tqdm import tqdm
        from core.registry import get_scheme
        from core.network import NetworkSimulator

        self.collector = MetricsCollector()

        schemes_to_run = {}
        for name in self.multiplicative_schemes:
            try:
                schemes_to_run[name] = get_scheme(name)
            except Exception as e:
                print(f"Warning: Could not initialize {name}: {e}")

        total = len(schemes_to_run) * num_runs_per_scheme
        iterator = tqdm(range(total), desc="Multiplicative Stress Test") if show_progress else range(total)
        run_idx = 0

        for name, scheme in schemes_to_run.items():
            adapted_initial = self._adapt_value_for_scheme(initial_value, scheme)
            for _ in range(num_runs_per_scheme):
                run_initial = adapted_initial + self._adapt_value_for_scheme(
                    np.random.uniform(-10, 10), scheme
                )

                metrics = ExperimentMetrics(scheme_name=scheme.name)
                sim = NetworkSimulator(scheme)
                sim.initialize(self.num_routers)

                try:
                    ciphertext = scheme.encrypt(run_initial, sim.keypair)
                except Exception as e:
                    metrics.success = False
                    metrics.failure_reason = f"Initial encryption failed: {e}"
                    metrics.finalize()
                    self.collector.add_result(name, metrics)
                    run_idx += 1
                    if show_progress:
                        iterator.update(1)
                    continue

                expected = run_initial

                for step in range(1, max_steps + 1):
                    factor = self._generate_multiplicative_factor(scheme)
                    adapted_val = self._adapt_value_for_scheme(factor, scheme)

                    hop_start = time.perf_counter()
                    try:
                        if scheme.supports_multiplicative():
                            ciphertext = scheme.multiply_constant(ciphertext, adapted_val, sim.keypair)
                            expected *= adapted_val
                        else:
                            raise RuntimeError(f"Scheme {scheme.name} does not support multiplication")
                        hop_latency = time.perf_counter() - hop_start

                        computed = scheme.decrypt(ciphertext, sim.keypair)
                        abs_err = abs(computed - expected)
                        rel_err = abs_err / (abs(expected) + 1e-10)

                        if rel_err > error_threshold:
                            metrics.failure_step = step
                            metrics.success = False
                            metrics.failure_reason = f"Relative error {rel_err:.4f} exceeded threshold"
                            metrics.record_hop(step, computed, expected,
                                               noise=scheme.get_noise_budget(ciphertext),
                                               latency=hop_latency)
                            break

                        metrics.record_hop(step, computed, expected,
                                           noise=scheme.get_noise_budget(ciphertext),
                                           latency=hop_latency)
                        metrics.max_sustainable_ops = step

                    except Exception as e:
                        metrics.failure_step = step
                        metrics.success = False
                        metrics.failure_reason = f"Error at step {step}: {e}"
                        break

                if metrics.failure_step == -1:
                    metrics.success = True

                metrics.num_hops = len(metrics.hop_numbers)
                metrics.finalize()
                self.collector.add_result(name, metrics)

                if show_progress:
                    iterator.update(1)
                run_idx += 1

        return self.collector