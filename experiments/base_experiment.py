"""Base class for homomorphic encryption experiments."""

import numpy as np
from typing import List
from abc import ABC, abstractmethod

from core.base import HEScheme
from core.operations import RoutingOperation, OperationType
from metrics.collector import MetricsCollector
import config


class BaseExperiment(ABC):
    """Base class for additive/multiplicative experiments."""

    def __init__(self, num_routers: int, num_fields: int):
        self.num_routers = num_routers
        self.num_fields = num_fields
        self.collector = MetricsCollector()

    @abstractmethod
    def _generate_router_operations(self) -> List[List[RoutingOperation]]:
        pass

    @abstractmethod
    def _compute_expected_values(self, initial_value: float,
                                 router_operations: List[List[RoutingOperation]]) -> List[float]:
        pass

    @abstractmethod
    def run_single_experiment(self, scheme: HEScheme, initial_value: float,
                              router_operations: List[List[RoutingOperation]], run_id: int = 0):
        pass

    def _get_scheme_type(self, scheme: HEScheme) -> str:
        """Return 'integer', 'float', or 'boolean' for a given scheme."""
        return config.SCHEME_TYPES.get(scheme.name, 'float')

    def _adapt_value_for_scheme(self, value: float, scheme: HEScheme) -> float:
        """Adapt a generic float value to the scheme's native type."""
        stype = self._get_scheme_type(scheme)
        if stype == 'integer':
            return float(int(value))          # remove fractional part
        elif stype == 'boolean':
            return float(int(value) % 2)      # boolean
        else:
            return value                      # float, keep as is

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
            # Adapt initial value for this scheme
            adapted_initial = self._adapt_value_for_scheme(initial_value, scheme)
            for _ in range(num_runs_per_scheme):
                run_initial = adapted_initial + self._adapt_value_for_scheme(
                    np.random.uniform(-10, 10), scheme
                )
                router_ops = self._generate_router_operations()
                # Adapt operation values on the fly inside run_single_experiment
                metrics = self.run_single_experiment(scheme, run_initial, router_ops, run_idx)
                self.collector.add_result(name, metrics)
                if show_progress:
                    iterator.update(1)
                run_idx += 1
        return self.collector