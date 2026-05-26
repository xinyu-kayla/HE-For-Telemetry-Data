"""Additive homomorphic experiment."""

import time
import numpy as np
from typing import List

from core.base import HEScheme
from core.operations import RoutingOperation, OperationType
from core.network import NetworkSimulator
from metrics.experiment_metrics import ExperimentMetrics
from metrics.collector import MetricsCollector
from experiments.base_experiment import BaseExperiment


class AdditiveExperiment(BaseExperiment):
    """Runs additive homomorphic experiments."""
    
    def __init__(self, num_routers: int = 10, num_fields: int = 2):
        super().__init__(num_routers, num_fields)
        self.additive_schemes = ['Paillier', 'BGN', 'BGV', 'BFV', 'CKKS', 'GSW']
    
    def _generate_router_operations(self) -> List[List[RoutingOperation]]:
        ops_per_router = []
        for router_idx in range(self.num_routers):
            measurement = np.random.uniform(1, 10)
            ops = [RoutingOperation(OperationType.ADD_CONSTANT, measurement)]
            if router_idx % 3 == 2:
                ops.append(RoutingOperation(OperationType.AGGREGATE))
            ops_per_router.append(ops)
        return ops_per_router
    
    def _compute_expected_values(self, initial_value: float,
                                  router_operations: List[List[RoutingOperation]]) -> List[float]:
        expected = [initial_value]
        current = initial_value
        for ops in router_operations:
            for op in ops:
                if op.op_type == OperationType.ADD_CONSTANT:
                    current += op.value
                # AGGREGATE does not change sum
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
            initial_plaintexts = [initial_value] + [0.0] * (self.num_fields - 1)
            
            # For hop-by-hop analysis (decrypt each step for measurement)
            temp_ct = scheme.encrypt(initial_value, sim.keypair)
            expected_values = self._compute_expected_values(initial_value, router_operations)
            
            for hop_idx, ops in enumerate(router_operations):
                hop_start = time.perf_counter()
                for op in ops:
                    if op.op_type == OperationType.ADD_CONSTANT:
                        temp_ct = scheme.add_constant(temp_ct, op.value, sim.keypair)
                hop_latency = time.perf_counter() - hop_start
                
                computed = scheme.decrypt(temp_ct, sim.keypair)
                expected = expected_values[hop_idx + 1]
                metrics.record_hop(hop_idx, computed, expected, latency=hop_latency)
            
            # Final full packet (simulate real network)
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
                  show_progress: bool = True) -> MetricsCollector:
        """Run additive experiment suite using predefined additive schemes."""
        return super().run_suite(num_runs_per_scheme, initial_value,
                                 self.additive_schemes, show_progress)