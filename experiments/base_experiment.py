"""Base class for homomorphic encryption experiments."""

import time
import numpy as np
from typing import List
from abc import ABC, abstractmethod

from core.base import HEScheme
from core.operations import RoutingOperation, OperationType
from metrics.collector import MetricsCollector
from metrics.experiment_metrics import ExperimentMetrics
import config


class BaseExperiment(ABC):
    """Base class for additive/multiplicative/stress experiments."""

    def __init__(self, num_routers: int, num_fields: int):
        self.num_routers = num_routers
        self.num_fields = num_fields
        self.collector = MetricsCollector()

    @abstractmethod
    def _generate_router_operations(self) -> List[List[RoutingOperation]]:
        """Generate a fixed sequence of operations for all hops (used in standard runs)."""
        pass

    @abstractmethod
    def _compute_expected_values(self, initial_value: float,
                                 router_operations: List[List[RoutingOperation]]) -> List[float]:
        """Compute expected plaintext values after each hop."""
        pass

    @abstractmethod
    def run_single_experiment(self, scheme: HEScheme, initial_value: float,
                              router_operations: List[List[RoutingOperation]], run_id: int = 0):
        """Run a single experiment with a fixed number of hops (standard)."""
        pass

    @abstractmethod
    def _generate_single_hop_operation(self, step: int) -> List[RoutingOperation]:
        """
        Generate the operation(s) for the *step*-th hop (1-indexed).
        Must be overridden by subclasses to define the per-step operation logic.
        """
        pass

    def _get_scheme_type(self, scheme: HEScheme) -> str:
        """Return 'integer', 'float', or 'boolean' for a given scheme."""
        return config.SCHEME_TYPES.get(scheme.name, 'float')

    def _adapt_value_for_scheme(self, value: float, scheme: HEScheme) -> float:
        """Adapt a generic float value to the scheme's native type."""
        stype = self._get_scheme_type(scheme)
        if stype == 'integer':
            return float(int(value))          
        elif stype == 'boolean':
            return float(int(value) % 2)      # boolean
        else:
            return value                      # float, keep as is

    def run_stress_test(
        self,
        scheme: HEScheme,
        initial_value: float,
        max_steps: int = 100,
        error_threshold: float = 0.5,
        run_id: int = 0
    ) -> ExperimentMetrics:
        """
        Run a stress test that increments operations until failure or max_steps.
        Records the maximum sustainable number of operations.
        """
        metrics = ExperimentMetrics(
            scheme_name=scheme.name,
            num_hops=0,                     
            operations_per_hop=1            
        )

        # Adapt initial value for this scheme
        adapted_initial = self._adapt_value_for_scheme(initial_value, scheme)

        # Initialize network simulator
        from core.network import NetworkSimulator
        sim = NetworkSimulator(scheme)
        sim.initialize(self.num_routers)   

        try:
            ciphertext = scheme.encrypt(adapted_initial, sim.keypair)
        except Exception as e:
            metrics.success = False
            metrics.failure_reason = f"Initial encryption failed: {e}"
            metrics.finalize()
            return metrics

        expected = adapted_initial
        current_step = 0

        for step in range(1, max_steps + 1):
            # Generate operations for this hop
            try:
                ops = self._generate_single_hop_operation(step)
            except Exception as e:
                metrics.failure_step = step
                metrics.success = False
                metrics.failure_reason = f"Operation generation failed at step {step}: {e}"
                break

            hop_start = time.perf_counter()
            try:
                for op in ops:
                    adapted_value = self._adapt_value_for_scheme(op.value, scheme)

                    if op.op_type == OperationType.ADD_CONSTANT:
                        ciphertext = scheme.add_constant(ciphertext, adapted_value, sim.keypair)
                        expected += adapted_value
                    elif op.op_type == OperationType.MULTIPLY_CONSTANT:
                        if scheme.supports_multiplicative():
                            ciphertext = scheme.multiply_constant(ciphertext, adapted_value, sim.keypair)
                            expected *= adapted_value
                        else:
                            raise RuntimeError(f"Scheme {scheme.name} does not support multiplication")
                    else:
                        raise ValueError(f"Unsupported operation type: {op.op_type}")

                hop_latency = time.perf_counter() - hop_start

                # Decrypt and compute error
                computed = scheme.decrypt(ciphertext, sim.keypair)
                abs_err = abs(computed - expected)
                rel_err = abs_err / (abs(expected) + 1e-10)

                # Check if error exceeds threshold (consider as failure)
                if rel_err > error_threshold:
                    metrics.failure_step = step
                    metrics.success = False
                    metrics.failure_reason = f"Relative error {rel_err:.4f} exceeded threshold {error_threshold}"
                    # Record the failing step (still record to show where it broke)
                    metrics.record_hop(step, computed, expected,
                                       noise=scheme.get_noise_budget(ciphertext),
                                       latency=hop_latency)
                    break

                # Record successful step
                metrics.record_hop(step, computed, expected,
                                   noise=scheme.get_noise_budget(ciphertext),
                                   latency=hop_latency)
                metrics.max_sustainable_ops = step   # update maximum

            except Exception as e:
                # Catch any runtime error
                metrics.failure_step = step
                metrics.success = False
                metrics.failure_reason = f"Error at step {step}: {e}"
                break

        # If we completed all steps without failure
        if metrics.failure_step == -1 and metrics.success:   # success remains True if no failure
            metrics.success = True
            # max_sustainable_ops already set to max_steps

        # Finalize metrics
        metrics.num_hops = len(metrics.hop_numbers)
        metrics.finalize()
        return metrics

    def run_suite(self, num_runs_per_scheme: int, initial_value: float,
                  schemes: List[str], show_progress: bool = True) -> MetricsCollector:
        np.random.seed(42)
        from core.registry import get_scheme
        from tqdm import tqdm

        schemes_to_run = {}
        for name in schemes:
            try:
                schemes_to_run[name] = get_scheme(name)
            except Exception as e:
                print(f"Warning: Could not initialize {name}: {e}")

        total = len(schemes_to_run) * num_runs_per_scheme
        desc = f"{self.__class__.__name__}"
        iterator = tqdm(range(total), desc=desc) if show_progress else range(total)
        run_idx = 0
        for name, scheme in schemes_to_run.items():
            adapted_initial = self._adapt_value_for_scheme(initial_value, scheme)
            for _ in range(num_runs_per_scheme):
                run_initial = adapted_initial + self._adapt_value_for_scheme(
                    np.random.uniform(-10, 10), scheme
                )
                router_ops = self._generate_router_operations()
                metrics = self.run_single_experiment(scheme, run_initial, router_ops, run_idx)
                self.collector.add_result(name, metrics)
                if show_progress:
                    iterator.update(1)
                run_idx += 1
        return self.collector