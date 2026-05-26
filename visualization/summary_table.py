"""Generate summary tables."""

import os
import pandas as pd
from metrics.collector import MetricsCollector


def generate_summary_table(collector_additive: MetricsCollector,
                           collector_multiplicative: MetricsCollector,
                           output_path: str) -> pd.DataFrame:
    add_df = collector_additive.generate_summary_table()
    mul_df = collector_multiplicative.generate_summary_table()
    add_df['Experiment Group'] = 'Additive'
    mul_df['Experiment Group'] = 'Multiplicative'
    combined = pd.concat([add_df, mul_df], ignore_index=True)
    combined = combined[['Experiment Group', 'Scheme', 'Runs', 'Success Rate',
                         'Mean Final Error', 'Mean Final Rel. Error', 'Mean Total Time (ms)']]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined.to_csv(output_path, index=False)
    return combined