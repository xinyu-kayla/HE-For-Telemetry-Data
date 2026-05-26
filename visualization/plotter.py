"""Main plotting class that orchestrates all visualizations."""

import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Optional

from metrics.collector import MetricsCollector
from visualization.error_plots import plot_error_accumulation
from visualization.latency_plots import plot_latency_comparison
from visualization.summary_table import generate_summary_table


class ExperimentPlotter:
    """Creates publication-quality visualizations for HE experiment results."""
    
    def __init__(self, style: str = 'seaborn-v0_8-darkgrid'):
        plt.style.use(style)
        sns.set_palette("husl")
        self.colors = sns.color_palette("husl", 10)
    
    def plot_error_accumulation(self, collector: MetricsCollector,
                                title_prefix: str = "",
                                save_path: Optional[str] = None) -> plt.Figure:
        return plot_error_accumulation(collector, title_prefix, save_path, self.colors)
    
    def plot_latency_comparison(self, collector: MetricsCollector,
                                title_prefix: str = "",
                                save_path: Optional[str] = None) -> plt.Figure:
        return plot_latency_comparison(collector, title_prefix, save_path, self.colors)
    
    def plot_combined_comparison(self, collector_additive: MetricsCollector,
                                  collector_multiplicative: MetricsCollector,
                                  output_dir: str = "./results"):
        os.makedirs(output_dir, exist_ok=True)
        self.plot_error_accumulation(collector_additive, "Additive Group - ",
                                     f"{output_dir}/additive_error_accumulation.png")
        self.plot_latency_comparison(collector_additive, "Additive Group - ",
                                     f"{output_dir}/additive_latency_comparison.png")
        self.plot_error_accumulation(collector_multiplicative, "Multiplicative Group - ",
                                     f"{output_dir}/multiplicative_error_accumulation.png")
        self.plot_latency_comparison(collector_multiplicative, "Multiplicative Group - ",
                                     f"{output_dir}/multiplicative_latency_comparison.png")
        generate_summary_table(collector_additive, collector_multiplicative,
                               f"{output_dir}/summary_table.csv")