"""Operation types and routing operation definitions."""

from enum import Enum
from dataclasses import dataclass
from typing import Any


class OperationType(Enum):
    """Types of homomorphic operations at a router."""
    ADD_CONSTANT = "add_constant"
    MULTIPLY_CONSTANT = "multiply_constant"
    ADD_CIPHERTEXT = "add_ciphertext"
    MULTIPLY_CIPHERTEXT = "multiply_ciphertext"
    AGGREGATE = "aggregate"
    ADD_TIMESTAMP = "add_timestamp"
    SCALE = "scale"


@dataclass
class RoutingOperation:
    """Defines a single operation to be applied at a router node."""
    op_type: OperationType
    value: Any = None
    description: str = ""
    
    def __post_init__(self):
        if not self.description:
            self.description = f"{self.op_type.value}"