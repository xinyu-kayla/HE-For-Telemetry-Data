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
        # Only include RSA and ElGamal; BGV/BFV/CKKS/GSW require additional libs or are unstable
        self.multiplicative_schemes = ['RSA', 'ElGamal']
    
    def _generate_router_operations(self) -> List[List[RoutingOperation]]:
        """Generate only multiplication operations (no addition)."""
        ops_per_router = []
        for router_idx in range(self.num_routers):
            # Only use multiplication by constant or ciphertext multiplication
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
                    # Multiply by secondary value (approximate as current * itself)
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
            secondary = initial_value * 1.5  # second field for multiplication
            initial_plaintexts = [initial_value, secondary] + [1.0] * (self.num_fields - 2)
            
            # Hop-by-hop analysis
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
                metrics.record_hop(hop_idx, computed, expected, latency=hop_latency)
            
            # Final packet
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
    
    def run_suite(self, num_runs_per_scheme: int, initial_value: float,
                  secondary_value: float = None, show_progress: bool = True) -> MetricsCollector:
        """Run multiplicative experiment suite using predefined multiplicative schemes."""
        return super().run_suite(num_runs_per_scheme, initial_value,
                                 self.multiplicative_schemes, show_progress)