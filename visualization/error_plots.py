"""Error accumulation plots."""

import matplotlib.pyplot as plt
import numpy as np
from typing import Optional

from metrics.collector import MetricsCollector


def plot_error_accumulation(collector: MetricsCollector,
                            title_prefix: str = "",
                            save_path: Optional[str] = None,
                            colors: Optional[list] = None) -> plt.Figure:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    if colors is None:
        colors = plt.cm.tab10.colors
    
    for idx, (scheme_name, runs) in enumerate(collector.results.items()):
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
        mean_rel = [np.mean(e) if e else 0 for e in hop_rel_errors]
        hops = list(range(len(mean_errors)))
        color = colors[idx % len(colors)]
        ax1.plot(hops, mean_errors, 'o-', label=scheme_name, color=color, lw=2)
        ax1.fill_between(hops, [m-s for m,s in zip(mean_errors, std_errors)],
                         [m+s for m,s in zip(mean_errors, std_errors)], alpha=0.2, color=color)
        ax2.semilogy(hops, mean_rel, 'o-', label=scheme_name, color=color, lw=2)
    
    ax1.set_xlabel('Hop Count'); ax1.set_ylabel('Absolute Error')
    ax1.set_title(f'{title_prefix}Absolute Error')
    ax1.legend(); ax1.grid(True, alpha=0.3)
    ax2.set_xlabel('Hop Count'); ax2.set_ylabel('Relative Error (log)')
    ax2.set_title(f'{title_prefix}Relative Error')
    ax2.legend(); ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    return fig