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

    def plot_error_accumulation(self, collector, group_name, output_path, colors=None):
        """
        Plot error accumulation over operations: two subplots (both log scale):
        - Left: Absolute error (log)
        - Right: Relative error (log)
        Uses distinct markers for each scheme. GSW is excluded from plots.
        """
        if colors is None:
            colors = plt.cm.tab10.colors

        marker_list = ['o', 's', '^', 'D', 'v', 'p', '*', 'X', 'P', 'h']
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        for idx, (scheme_name, runs) in enumerate(collector.results.items()):
            # 排除 GSW
            if scheme_name == "GSW":
                continue
            if not runs:
                continue

            max_ops = max(len(r.hop_numbers) for r in runs)
            op_errors = [[] for _ in range(max_ops)]
            op_rel_errors = [[] for _ in range(max_ops)]

            for run in runs:
                for op_idx, err, rel in zip(run.hop_numbers, run.absolute_errors, run.relative_errors):
                    if op_idx < max_ops:
                        op_errors[op_idx].append(err)
                        op_rel_errors[op_idx].append(rel)

            mean_errors = [np.mean(e) if e else 0 for e in op_errors]
            mean_rel = [np.mean(e) if e else 0 for e in op_rel_errors]

            ops = list(range(len(mean_errors)))
            color = colors[idx % len(colors)]
            marker = marker_list[idx % len(marker_list)]

            # 绝对误差（对数坐标），将0替换为1e-12
            mean_errors_plot = [max(1e-12, val) for val in mean_errors]
            ax1.semilogy(ops, mean_errors_plot, marker=marker, linestyle='-',
                         markersize=8, label=scheme_name, color=color, lw=2)

            # 相对误差（对数坐标）
            mean_rel_plot = [max(1e-12, val) for val in mean_rel]
            ax2.semilogy(ops, mean_rel_plot, marker=marker, linestyle='-',
                         markersize=8, label=scheme_name, color=color, lw=2)

        ax1.set_xlabel('Operation Count')
        ax1.set_ylabel('Absolute Error (log)')
        ax1.set_title(f'{group_name}Absolute Error')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2.set_xlabel('Operation Count')
        ax2.set_ylabel('Relative Error (log)')
        ax2.set_title(f'{group_name}Relative Error')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return fig

    def plot_latency_comparison(self, collector, group_name, output_path):
        """Plot average per-operation latency for each scheme."""
        plt.figure(figsize=(8, 5))
        names = []
        latencies = []
        for scheme_name, runs in collector.results.items():
            if not runs:
                continue
            avg_lat = np.mean([np.mean(r.latencies) for r in runs if r.latencies]) * 1000  # ms
            names.append(scheme_name)
            latencies.append(avg_lat)
        if not names:
            plt.close()
            return
        bars = plt.bar(names, latencies, color='skyblue')
        plt.ylabel('Average Latency (ms)')
        plt.title(f'{group_name}Per-Operation Latency')
        for bar, val in zip(bars, latencies):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                     f'{val:.2f}', ha='center', va='bottom', fontsize=8)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()

    def save_error_table(self, collector, group_name, output_dir):
        """Save per-operation expected, computed, and error values to CSV."""
        for scheme_name, runs in collector.results.items():
            if not runs:
                continue
            run = runs[0]
            if not run.absolute_errors:
                continue
            filepath = os.path.join(output_dir, f"{group_name}_{scheme_name}_errors.csv")
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Operation', 'Expected', 'Computed', 'Absolute Error'])
                for op_idx, (exp, comp, err) in enumerate(zip(
                    run.expected_values, run.computed_values, run.absolute_errors)):
                    writer.writerow([op_idx, exp, comp, err])
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