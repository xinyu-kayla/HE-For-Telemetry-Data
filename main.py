#!/usr/bin/env python3
"""Main entry point for telemetry HE validation model."""

import sys
import os
import warnings
import argparse
import time
from datetime import datetime

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import config
from experiments.additive_experiment import AdditiveExperiment
from experiments.multiplicative_experiment import MultiplicativeExperiment
from experiments.fully_experiment import FullyExperiment
from visualization.plotter import ExperimentPlotter
from utils.helpers import print_experiment_summary, save_experiment_data


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Telemetry Homomorphic Encryption Validation Model"
    )
    parser.add_argument("--additive", action="store_true", help="Run additive group experiments")
    parser.add_argument(
        "--multiplicative", action="store_true", help="Run multiplicative group experiments"
    )
    parser.add_argument("--fully", action="store_true", help="Run fully homomorphic experiments")
    parser.add_argument("--all", action="store_true", help="Run all experiment groups")

    parser.add_argument(
        "--schemes", type=str, default="", help="Comma-separated list of specific schemes"
    )

    parser.add_argument("--runs", type=int, default=None, help="Number of runs per scheme")
    parser.add_argument(
        "--routers-add", type=int, default=None, help="Number of routers for additive group"
    )
    parser.add_argument(
        "--routers-mul", type=int, default=None, help="Number of routers for multiplicative group"
    )
    parser.add_argument(
        "--routers-fully", type=int, default=None, help="Number of routers for fully group"
    )

    parser.add_argument("--no-plots", action="store_true", help="Skip generating plots")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for results")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    parser.add_argument(
        "--stress", action="store_true",
        help="Run stress tests (limit testing) instead of fixed-step experiments"
    )
    parser.add_argument(
        "--max-steps", type=int, default=50,
        help="Maximum steps to attempt in stress test (default: 50)"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.5,
        help="Relative error threshold for stress test failure (default: 0.5)"
    )

    return parser.parse_args()


def setup_output_directory(output_dir: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_output_dir = os.path.join(output_dir, f"run_{timestamp}")
    os.makedirs(full_output_dir, exist_ok=True)
    return full_output_dir


def run_experiment_group(exp_class, group_name, scheme_list_key, num_routers, initial_value,
                         args, full_output_dir):
    
    exp = exp_class(num_routers=num_routers, num_fields=config.NUM_FIELDS)

    if args.schemes:
        specific = [s.strip() for s in args.schemes.split(",")]
        allowed = getattr(exp, scheme_list_key)
        setattr(exp, scheme_list_key, [s for s in specific if s in allowed])

    if args.stress:
        print(f"\n>>> Running STRESS TEST for {group_name} (max_steps={args.max_steps}, threshold={args.threshold})")
        collector = exp.run_stress_suite(
            num_runs_per_scheme=args.runs,
            initial_value=initial_value,
            max_steps=args.max_steps,
            error_threshold=args.threshold,
            show_progress=True
        )
    else:
        print(f"\n>>> Running STANDARD experiment for {group_name}")
        collector = exp.run_suite(
            num_runs_per_scheme=args.runs,
            initial_value=initial_value,
            show_progress=True
        )

    print_experiment_summary(collector, f"{group_name} Group")

    for scheme_name, runs in collector.results.items():
        prefix = group_name.lower().replace(" ", "_")
        save_path = os.path.join(full_output_dir, f"{prefix}_{scheme_name}_metrics.pkl")
        save_experiment_data([r.to_dict() for r in runs], save_path)

    return collector


def main():
    args = parse_arguments()
    import numpy as np
    np.random.seed(args.seed)

    run_all = args.all or (not args.additive and not args.multiplicative and not args.fully)
    run_additive = args.additive or run_all
    run_multiplicative = args.multiplicative or run_all
    run_fully = args.fully or run_all

    num_runs = args.runs if args.runs is not None else config.NUM_RUNS_PER_SCHEME
    num_routers_add = args.routers_add if args.routers_add is not None else config.NUM_ROUTERS_ADDITIVE
    num_routers_mul = args.routers_mul if args.routers_mul is not None else config.NUM_ROUTERS_MULTIPLICATIVE
    num_routers_fully = args.routers_fully if args.routers_fully is not None else config.NUM_ROUTERS_FULLY
    output_dir = args.output_dir if args.output_dir is not None else config.OUTPUT_DIR

    print("=" * 70)
    print("TELEMETRY HOMOMORPHIC ENCRYPTION VALIDATION MODEL")
    print("=" * 70)
    print(f"Random seed: {args.seed}")
    print(f"Mode: {'STRESS TEST' if args.stress else 'STANDARD (fixed steps)'}")
    if args.stress:
        print(f"  Max steps: {args.max_steps}, Error threshold: {args.threshold}")
    print(f"Runs per scheme: {num_runs}")
    print(f"Additive routers: {num_routers_add}")
    print(f"Multiplicative routers: {num_routers_mul}")
    print(f"Fully homomorphic routers: {num_routers_fully}")
    if args.schemes:
        print(f"Specific schemes: {args.schemes}")
    print("=" * 70)

    full_output_dir = setup_output_directory(output_dir)
    print(f"Results will be saved to: {full_output_dir}\n")

    start_time = time.time()

    collector_additive = None
    collector_multiplicative = None
    collector_fully = None

    if run_additive:
        collector_additive = run_experiment_group(
            AdditiveExperiment,
            "Additive",
            "additive_schemes",
            num_routers_add,
            config.INITIAL_TELEMETRY_ADDITIVE,
            args,
            full_output_dir
        )

    if run_multiplicative:
        collector_multiplicative = run_experiment_group(
            MultiplicativeExperiment,
            "Multiplicative",
            "multiplicative_schemes",
            num_routers_mul,
            config.INITIAL_TELEMETRY_MULTIPLICATIVE,
            args,
            full_output_dir
        )

    if run_fully:
        collector_fully = run_experiment_group(
            FullyExperiment,
            "Fully",
            "fully_schemes",
            num_routers_fully,
            config.INITIAL_TELEMETRY_FULLY,
            args,
            full_output_dir
        )

    if not args.no_plots:
        plotter = ExperimentPlotter()

        def plot_group(collector, group_prefix, file_suffix):
            if collector:
                plotter.plot_error_accumulation(
                    collector,
                    f"{group_prefix} - ",
                    os.path.join(full_output_dir, f"{file_suffix}_error_accumulation.png")
                )
                plotter.plot_latency_comparison(
                    collector,
                    f"{group_prefix} - ",
                    os.path.join(full_output_dir, f"{file_suffix}_latency_comparison.png")
                )
                plotter.save_error_table(collector, file_suffix, full_output_dir)

        plot_group(collector_additive, "Additive Group", "additive")
        plot_group(collector_multiplicative, "Multiplicative Group", "multiplicative")
        plot_group(collector_fully, "Fully Homomorphic Group", "fully")

        gsw_collectors = []
        gsw_group_names = []
        if collector_additive and 'GSW' in collector_additive.results:
            gsw_collectors.append(collector_additive)
            gsw_group_names.append('Additive')
        if collector_multiplicative and 'GSW' in collector_multiplicative.results:
            gsw_collectors.append(collector_multiplicative)
            gsw_group_names.append('Multiplicative')
        if collector_fully and 'GSW' in collector_fully.results:
            gsw_collectors.append(collector_fully)
            gsw_group_names.append('Fully')
        if gsw_collectors:
            plotter.plot_gsw_bit_accuracy(
                gsw_collectors, gsw_group_names,
                os.path.join(full_output_dir, "gsw_bit_accuracy.png")
            )

    if args.stress:
        print("\n" + "=" * 70)
        print("STRESS TEST SUMMARY - Maximum Sustainable Operations")
        print("=" * 70)
        for group_name, collector in [
            ("Additive", collector_additive),
            ("Multiplicative", collector_multiplicative),
            ("Fully", collector_fully)
        ]:
            if collector and collector.results:
                print(f"\n{group_name} Group:")
                for scheme, runs in collector.results.items():
                    if runs:
                        max_ops = max(r.max_sustainable_ops for r in runs)
                        failures = [r.failure_step for r in runs if r.failure_step != -1]
                        success_count = sum(1 for r in runs if r.success)
                        print(f"  {scheme:10s} : max_ops = {max_ops:3d}, "
                              f"successful runs = {success_count}/{len(runs)}, "
                              f"failures at steps {failures if failures else 'none'}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"EXPERIMENT COMPLETED in {elapsed:.2f} seconds")
    print(f"Results saved to: {full_output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()