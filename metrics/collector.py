"""Collects and aggregates metrics across runs."""

from typing import Dict, List, Any
from collections import defaultdict
import numpy as np
import pandas as pd

from metrics.experiment_metrics import ExperimentMetrics


class MetricsCollector:
    """Collects and aggregates metrics across multiple experiment runs."""
    
    def __init__(self):
        self.results: Dict[str, List[ExperimentMetrics]] = defaultdict(list)
    
    def add_result(self, scheme_name: str, metrics: ExperimentMetrics):
        self.results[scheme_name].append(metrics)
    
    def get_aggregated(self, scheme_name: str) -> Dict[str, Any]:
        if scheme_name not in self.results:
            return {}
        runs = self.results[scheme_name]
        max_hops = max(len(r.hop_numbers) for r in runs)
        hop_errors = [[] for _ in range(max_hops)]
        hop_rel_errors = [[] for _ in range(max_hops)]
        for run in runs:
            for hop, err, rel in zip(run.hop_numbers, run.absolute_errors, run.relative_errors):
                if hop < max_hops:
                    hop_errors[hop].append(err)
                    hop_rel_errors[hop].append(rel)
        mean_errors = [np.mean(e) if e else 0 for e in hop_errors]
        std_errors = [np.std(e) if e else 0 for e in hop_errors]
        mean_rel_errors = [np.mean(e) if e else 0 for e in hop_rel_errors]
        return {
            'scheme_name': scheme_name,
            'num_runs': len(runs),
            'hop_counts': list(range(max_hops)),
            'mean_errors': mean_errors,
            'std_errors': std_errors,
            'mean_rel_errors': mean_rel_errors,
            'mean_final_error': np.mean([r.final_error for r in runs]),
            'mean_success_rate': np.mean([1.0 if r.success else 0.0 for r in runs])
        }
    
    def generate_summary_table(self) -> pd.DataFrame:
        data = []
        for scheme_name, runs in self.results.items():
            success_count = sum(1 for r in runs if r.success)
            mean_final_error = np.mean([r.final_error for r in runs])
            mean_final_rel_error = np.mean([r.final_relative_error for r in runs])
            mean_total_time = np.mean([sum(r.latencies) for r in runs if r.latencies])
            data.append({
                'Scheme': scheme_name,
                'Runs': len(runs),
                'Success Rate': f"{success_count}/{len(runs)}",
                'Mean Final Error': f"{mean_final_error:.6e}",
                'Mean Final Rel. Error': f"{mean_final_rel_error:.2e}",
                'Mean Total Time (ms)': f"{mean_total_time * 1000:.2f}"
            })
        return pd.DataFrame(data)