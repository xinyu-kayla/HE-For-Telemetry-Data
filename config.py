"""
Configuration settings for homomorphic encryption telemetry validation model.
"""

# Experiment Configuration
NUM_ROUTERS_ADDITIVE = 12
NUM_ROUTERS_MULTIPLICATIVE = 10
NUM_RUNS_PER_SCHEME = 5
NUM_FIELDS = 3

# Telemetry Data Values
INITIAL_TELEMETRY_ADDITIVE = 50.0
INITIAL_TELEMETRY_MULTIPLICATIVE = 2.0
SECONDARY_TELEMETRY_MULTIPLICATIVE = 3.0

# RSA Configuration
RSA_KEY_SIZE = 1024

# ElGamal Configuration
ELGAMAL_KEY_SIZE = 256

# Paillier Configuration
PAILLIER_KEY_SIZE = 1024

# BGV/BFV/CKKS Configuration (Pyfhel)
POLY_MODULUS_DEGREE = 2**14
PLAINTEXT_MODULUS = 65537
CKKS_SCALE = 2**40
CKKS_QI_SIZES = [60, 40, 40, 40, 40, 60]

# GSW Configuration
GSW_N = 4
GSW_Q = 2**20

# Output Settings
OUTPUT_DIR = "./results"
SAVE_PLOTS = True
SAVE_DATA = True
SHOW_PLOTS = False

# Performance
ENABLE_DETAILED_LOGGING = False
USE_GPU_ACCELERATION = False

# Fully Homomorphic Configuration
NUM_ROUTERS_FULLY = 6
INITIAL_TELEMETRY_FULLY = 10.0
SECONDARY_TELEMETRY_FULLY = 15.0