"""Visualization utilities for experiment results."""

import os
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class ExperimentPlotter:
    """Generates and saves plots for experiment metrics."""

    def __init__(self):
        plt.rcParams['figure.dpi'] = 150
        plt.rcParams['savefig.bbox'] = 'tight'
        plt.rcParams['savefig.pad_inches'] = 0.1

    def plot_error_accumulation(self, collector, group_name, output_path):
        """Plot error accumulation over hops for each scheme."""
        plt.figure(figsize=(8, 5))
        for scheme_name, runs in collector.results.items():
            if not runs:
                continue
            run = runs[0]  # use first run
            # Use existing absolute_errors list
            if not run.absolute_errors:
                continue
            hops = list(range(len(run.absolute_errors)))
            errors = run.absolute_errors
            plt.plot(hops, errors, marker='o', markersize=4, label=scheme_name)
        plt.xlabel('Hop')
        plt.ylabel('Absolute Error')
        plt.title(f'{group_name}Error Accumulation')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()

    def plot_latency_comparison(self, collector, group_name, output_path):
        """Plot average per-hop latency for each scheme."""
        plt.figure(figsize=(8, 5))
        names = []
        latencies = []
        for scheme_name, runs in collector.results.items():
            if not runs:
                continue
            # Compute average latency from the latencies list
            avg_lat = np.mean([np.mean(r.latencies) for r in runs if r.latencies]) * 1000  # ms
            names.append(scheme_name)
            latencies.append(avg_lat)
        if not names:
            plt.close()
            return
        bars = plt.bar(names, latencies, color='skyblue')
        plt.ylabel('Average Latency (ms)')
        plt.title(f'{group_name}Per-Hop Latency')
        for bar, val in zip(bars, latencies):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                     f'{val:.2f}', ha='center', va='bottom', fontsize=8)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()

    def save_error_table(self, collector, group_name, output_dir):
        """Save per-hop expected, computed, and error values to CSV."""
        for scheme_name, runs in collector.results.items():
            if not runs:
                continue
            run = runs[0]
            if not run.absolute_errors:
                continue
            filepath = os.path.join(output_dir, f"{group_name}_{scheme_name}_errors.csv")
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Hop', 'Expected', 'Computed', 'Absolute Error'])
                for hop_idx, (exp, comp, err) in enumerate(zip(
                    run.expected_values, run.computed_values, run.absolute_errors)):
                    writer.writerow([hop_idx, exp, comp, err])
            print(f"Error table saved: {filepath}")

    def plot_gsw_bit_accuracy(self, collectors, group_names, output_path):
        """Plot GSW bit accuracy for multiple experiment groups."""
        accuracies = []
        labels = []
        for collector, gname in zip(collectors, group_names):
            if 'GSW' in collector.results:
                gsw_runs = collector.results['GSW']
                if gsw_runs:
                    acc = getattr(gsw_runs[0], 'gsw_bit_accuracy', None)
                    if acc is not None:
                        accuracies.append(acc * 100)
                        labels.append(gname)
        if not accuracies:
            return
        plt.figure(figsize=(6, 4))
        bars = plt.bar(labels, accuracies, color='lightgreen')
        plt.ylim(0, 105)
        plt.ylabel('Bit Accuracy (%)')
        plt.title('GSW Boolean Circuit Accuracy')
        for bar, acc in zip(bars, accuracies):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                     f'{acc:.1f}%', ha='center', va='bottom')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()