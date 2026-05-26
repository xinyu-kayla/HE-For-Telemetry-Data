#!/usr/bin/env python3
"""
Main entry point for telemetry HE validation model.
"""

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
from visualization.plotter import ExperimentPlotter
from utils.helpers import print_experiment_summary, save_experiment_data


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Telemetry Homomorphic Encryption Validation Model"
    )
    parser.add_argument('--additive', action='store_true',
                        help='Run additive group experiments')
    parser.add_argument('--multiplicative', action='store_true',
                        help='Run multiplicative group experiments')
    parser.add_argument('--all', action='store_true',
                        help='Run both additive and multiplicative experiments')
    parser.add_argument('--schemes', type=str, default='',
                        help='Comma-separated list of specific schemes')
    parser.add_argument('--runs', type=int, default=None,
                        help='Number of runs per scheme')
    parser.add_argument('--routers-add', type=int, default=None,
                        help='Number of routers for additive group')
    parser.add_argument('--routers-mul', type=int, default=None,
                        help='Number of routers for multiplicative group')
    parser.add_argument('--no-plots', action='store_true',
                        help='Skip generating plots')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory for results')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    return parser.parse_args()


def setup_output_directory(output_dir: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_output_dir = os.path.join(output_dir, f"run_{timestamp}")
    os.makedirs(full_output_dir, exist_ok=True)
    return full_output_dir


def main():
    args = parse_arguments()
    import numpy as np
    np.random.seed(args.seed)
    
    run_additive = args.additive or args.all or (not args.additive and not args.multiplicative)
    run_multiplicative = args.multiplicative or args.all or (not args.additive and not args.multiplicative)
    
    num_runs = args.runs if args.runs is not None else config.NUM_RUNS_PER_SCHEME
    num_routers_add = args.routers_add if args.routers_add is not None else config.NUM_ROUTERS_ADDITIVE
    num_routers_mul = args.routers_mul if args.routers_mul is not None else config.NUM_ROUTERS_MULTIPLICATIVE
    output_dir = args.output_dir if args.output_dir is not None else config.OUTPUT_DIR
    
    specific_schemes = [s.strip() for s in args.schemes.split(',')] if args.schemes else []
    
    print("=" * 70)
    print("TELEMETRY HOMOMORPHIC ENCRYPTION VALIDATION MODEL")
    print("=" * 70)
    print(f"Random seed: {args.seed}")
    print(f"Runs per scheme: {num_runs}")
    print(f"Additive routers: {num_routers_add}")
    print(f"Multiplicative routers: {num_routers_mul}")
    if specific_schemes:
        print(f"Specific schemes: {specific_schemes}")
    print("=" * 70)
    
    full_output_dir = setup_output_directory(output_dir)
    print(f"Results will be saved to: {full_output_dir}\n")
    
    collector_additive = None
    collector_multiplicative = None
    
    start_time = time.time()
    
    # Run additive experiments
    if run_additive:
        print("\n" + "=" * 50)
        print("ADDITIVE GROUP EXPERIMENTS")
        print("Schemes: Paillier, BGV, BFV, CKKS, BGN, GSW")
        print("=" * 50 + "\n")
        
        additive_exp = AdditiveExperiment(
            num_routers=num_routers_add,
            num_fields=config.NUM_FIELDS
        )
        if specific_schemes:
            additive_exp.additive_schemes = [s for s in specific_schemes 
                                              if s in additive_exp.additive_schemes]
        
        collector_additive = additive_exp.run_suite(
            num_runs_per_scheme=num_runs,
            initial_value=config.INITIAL_TELEMETRY_ADDITIVE,
            show_progress=True
        )
        print_experiment_summary(collector_additive, "Additive Group")
        
        for scheme_name, runs in collector_additive.results.items():
            save_path = os.path.join(full_output_dir, f"additive_{scheme_name}_metrics.pkl")
            save_experiment_data([r.to_dict() for r in runs], save_path)
    
    # Run multiplicative experiments
    if run_multiplicative:
        print("\n" + "=" * 50)
        print("MULTIPLICATIVE GROUP EXPERIMENTS")
        print("Schemes: RSA, ElGamal, BGV, BFV, CKKS, GSW")
        print("=" * 50 + "\n")
        
        multiplicative_exp = MultiplicativeExperiment(
            num_routers=num_routers_mul,
            num_fields=config.NUM_FIELDS
        )
        if specific_schemes:
            multiplicative_exp.multiplicative_schemes = [s for s in specific_schemes 
                                                         if s in multiplicative_exp.multiplicative_schemes]
        
        collector_multiplicative = multiplicative_exp.run_suite(
            num_runs_per_scheme=num_runs,
            initial_value=config.INITIAL_TELEMETRY_MULTIPLICATIVE,
            secondary_value=config.SECONDARY_TELEMETRY_MULTIPLICATIVE,
            show_progress=True
        )
        print_experiment_summary(collector_multiplicative, "Multiplicative Group")
        
        for scheme_name, runs in collector_multiplicative.results.items():
            save_path = os.path.join(full_output_dir, f"multiplicative_{scheme_name}_metrics.pkl")
            save_experiment_data([r.to_dict() for r in runs], save_path)
    
    # Generate visualizations
    if not args.no_plots and (collector_additive or collector_multiplicative):
        plotter = ExperimentPlotter()
        if collector_additive and collector_multiplicative:
            plotter.plot_combined_comparison(collector_additive, collector_multiplicative, full_output_dir)
        elif collector_additive:
            plotter.plot_error_accumulation(collector_additive, "Additive Group - ",
                                            os.path.join(full_output_dir, "additive_error_accumulation.png"))
            plotter.plot_latency_comparison(collector_additive, "Additive Group - ",
                                            os.path.join(full_output_dir, "additive_latency_comparison.png"))
        elif collector_multiplicative:
            plotter.plot_error_accumulation(collector_multiplicative, "Multiplicative Group - ",
                                            os.path.join(full_output_dir, "multiplicative_error_accumulation.png"))
            plotter.plot_latency_comparison(collector_multiplicative, "Multiplicative Group - ",
                                            os.path.join(full_output_dir, "multiplicative_latency_comparison.png"))
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"EXPERIMENT COMPLETED in {elapsed:.2f} seconds")
    print(f"Results saved to: {full_output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()