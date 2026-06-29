"""Data container for experiment metrics."""

from typing import List, Dict, Any
from dataclasses import dataclass, field
import numpy as np


@dataclass
class ExperimentMetrics:
    """Container for all metrics collected during an experiment run."""
    hop_numbers: List[int] = field(default_factory=list)
    computed_values: List[float] = field(default_factory=list)
    expected_values: List[float] = field(default_factory=list)
    absolute_errors: List[float] = field(default_factory=list)
    relative_errors: List[float] = field(default_factory=list)
    noise_budgets: List[float] = field(default_factory=list)
    latencies: List[float] = field(default_factory=list)
    cumulative_computed: List[float] = field(default_factory=list)
    cumulative_expected: List[float] = field(default_factory=list)
    final_computed: float = 0.0
    final_expected: float = 0.0
    final_error: float = 0.0
    final_relative_error: float = 0.0
    scheme_name: str = ""
    num_hops: int = 0
    operations_per_hop: int = 0
    success: bool = True
    failure_reason: str = ""

    
    max_sustainable_ops: int = 0      
    failure_step: int = -1           
    # ---------------------------------

    def record_hop(self, hop_idx: int, computed: float, expected: float,
                   noise: float = -1.0, latency: float = 0.0):
        self.hop_numbers.append(hop_idx)
        self.computed_values.append(computed)
        self.expected_values.append(expected)
        abs_err = abs(computed - expected)
        rel_err = abs_err / (abs(expected) + 1e-10)
        self.absolute_errors.append(abs_err)
        self.relative_errors.append(rel_err)
        if noise >= 0:
            self.noise_budgets.append(noise)
        self.latencies.append(latency)  # Always record latency
        if not self.cumulative_computed:
            self.cumulative_computed.append(computed)
            self.cumulative_expected.append(expected)
        else:
            self.cumulative_computed.append(self.cumulative_computed[-1] + computed)
            self.cumulative_expected.append(self.cumulative_expected[-1] + expected)

    def finalize(self):
        if self.computed_values:
            self.final_computed = self.computed_values[-1]
            self.final_expected = self.expected_values[-1]
            self.final_error = self.absolute_errors[-1] if self.absolute_errors else 0.0
            self.final_relative_error = self.relative_errors[-1] if self.relative_errors else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'scheme_name': self.scheme_name,
            'num_hops': self.num_hops,
            'operations_per_hop': self.operations_per_hop,
            'success': self.success,
            'failure_reason': self.failure_reason,
            'final_computed': self.final_computed,
            'final_expected': self.final_expected,
            'final_error': self.final_error,
            'final_relative_error': self.final_relative_error,
            'mean_absolute_error': np.mean(self.absolute_errors) if self.absolute_errors else 0,
            'max_absolute_error': np.max(self.absolute_errors) if self.absolute_errors else 0,
            'mean_latency': np.mean(self.latencies) if self.latencies else 0,
            'total_latency': np.sum(self.latencies) if self.latencies else 0,
            'max_sustainable_ops': self.max_sustainable_ops,
            'failure_step': self.failure_step,
        }