"""Helper utility functions."""

import json
import pickle
import os
from typing import Any, Dict, List
import numpy as np


def save_experiment_data(data: Any, filepath: str):
    """Save experiment data to file (JSON or pickle)."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except (TypeError, OverflowError):
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)


def load_experiment_data(filepath: str) -> Any:
    """Load experiment data from file."""
    with open(filepath, 'rb') as f:
        try:
            return pickle.load(f)
        except pickle.PickleError:
            f.seek(0)
            return json.load(f)


def print_experiment_summary(collector, group_name: str):
    """Print formatted summary of experiment results."""
    print(f"\n{'='*60}")
    print(f"{group_name} Experiment Summary")
    print(f"{'='*60}")
    summary_df = collector.generate_summary_table()
    print(summary_df.to_string(index=False))
    print(f"\n{'='*60}\n")