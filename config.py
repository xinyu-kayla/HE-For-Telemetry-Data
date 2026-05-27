"""
Configuration settings for homomorphic encryption telemetry validation model.
"""

# Experiment Configuration
NUM_ROUTERS_ADDITIVE = 12
NUM_ROUTERS_MULTIPLICATIVE = 4
NUM_RUNS_PER_SCHEME = 5
NUM_FIELDS = 3

# Telemetry Data Values (will be overridden per scheme type)
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
CKKS_QI_SIZES = [60, 40, 40, 40, 40, 40, 40, 60]

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
NUM_ROUTERS_FULLY = 3
INITIAL_TELEMETRY_FULLY = 10.0
SECONDARY_TELEMETRY_FULLY = 15.0

# ===================== Per‑scheme type adaption =====================
# Scheme type map: 'scheme_name' -> 'integer', 'float', or 'boolean'
SCHEME_TYPES = {
    'RSA': 'integer',
    'ElGamal': 'integer',
    'Paillier': 'integer',
    'BGN': 'integer',
    'BGV': 'integer',
    'BFV': 'integer',
    'CKKS': 'float',
    'GSW': 'boolean',
}

# Initial values for each type in each experiment group
INITIAL_VALUES = {
    'additive':   {'integer': 100,  'float': 100.0,  'boolean': 1},
    'multiplicative': {'integer': 2, 'float': 2.0, 'boolean': 1},
    'fully':      {'integer': 10,  'float': 10.0,  'boolean': 1},
}

# Operation value ranges for each type (uniform distribution)
# For boolean, all values will be taken modulo 2 later.
OP_VALUE_RANGES = {
    'additive':   {'integer': (1, 10),     'float': (1.0, 10.0),   'boolean': (0, 1)},
    'multiplicative': {'integer': (1, 2),  'float': (0.95, 1.05), 'boolean': (0, 1)},
    'fully':      {
        'add':   {'integer': (1, 5),       'float': (1.0, 5.0),     'boolean': (0, 1)},
        'mul':   {'integer': (1, 2),       'float': (0.95, 1.05),   'boolean': (0, 1)},
    },
}