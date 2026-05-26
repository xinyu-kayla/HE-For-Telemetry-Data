"""Latency comparison bar charts."""

import matplotlib.pyplot as plt
import numpy as np
from typing import Optional

from metrics.collector import MetricsCollector


def plot_latency_comparison(collector: MetricsCollector,
                            title_prefix: str = "",
                            save_path: Optional[str] = None,
                            colors: Optional[list] = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 6))
    scheme_names = []
    mean_latencies = []
    std_latencies = []
    for scheme_name, runs in collector.results.items():
        latencies = [lat for run in runs for lat in run.latencies]
        if latencies:
            scheme_names.append(scheme_name)
            mean_latencies.append(np.mean(latencies) * 1000)
            std_latencies.append(np.std(latencies) * 1000)
    if scheme_names:
        bars = ax.bar(scheme_names, mean_latencies, yerr=std_latencies,
                      capsize=5, color=colors[:len(scheme_names)] if colors else None)
        ax.set_xlabel('Scheme'); ax.set_ylabel('Mean Latency (ms)')
        ax.set_title(f'{title_prefix}Per-Operation Latency')
        ax.tick_params(axis='x', rotation=45)
        for bar, val in zip(bars, mean_latencies):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
                    f'{val:.1f}', ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    return fig