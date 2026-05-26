"""Telemetry packet data structure."""

from typing import List, Any, Dict
from dataclasses import dataclass, field


@dataclass
class TelemetryPacket:
    """Encrypted telemetry data packet that traverses the network."""
    ciphertexts: List[Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    hop_count: int = 0
    operation_history: List[str] = field(default_factory=list)
    timing_history: List[float] = field(default_factory=list)
    noise_readings: List[float] = field(default_factory=list)