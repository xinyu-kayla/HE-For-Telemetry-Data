"""Router node that processes encrypted packets."""

import time
from typing import List

from core.base import HEScheme, HEKeyPair
from core.packet import TelemetryPacket
from core.operations import RoutingOperation, OperationType


class RouterNode:
    """Router node in a multi-hop network."""
    
    def __init__(self, node_id: int, scheme: HEScheme, keypair: HEKeyPair):
        self.node_id = node_id
        self.scheme = scheme
        self.keypair = keypair
    
    def process_packet(self, packet: TelemetryPacket,
                       operations: List[RoutingOperation]) -> TelemetryPacket:
        start_time = time.perf_counter()
        new_ciphertexts = list(packet.ciphertexts)
        
        for op in operations:
            try:
                if op.op_type == OperationType.ADD_CONSTANT:
                    new_ciphertexts[0] = self.scheme.add_constant(
                        new_ciphertexts[0], op.value, self.keypair
                    )
                elif op.op_type == OperationType.MULTIPLY_CONSTANT:
                    new_ciphertexts[0] = self.scheme.multiply_constant(
                        new_ciphertexts[0], op.value, self.keypair
                    )
                elif op.op_type == OperationType.ADD_CIPHERTEXT:
                    new_ciphertexts[0] = self.scheme.add(
                        new_ciphertexts[0], new_ciphertexts[1], self.keypair
                    )
                elif op.op_type == OperationType.MULTIPLY_CIPHERTEXT:
                    if self.scheme.supports_multiplicative():
                        new_ciphertexts[0] = self.scheme.multiply(
                            new_ciphertexts[0], new_ciphertexts[1], self.keypair
                        )
                elif op.op_type == OperationType.AGGREGATE:
                    aggregated = new_ciphertexts[0]
                    for ct in new_ciphertexts[1:]:
                        if self.scheme.supports_additive():
                            aggregated = self.scheme.add(aggregated, ct, self.keypair)
                    new_ciphertexts = [aggregated]
                elif op.op_type == OperationType.ADD_TIMESTAMP:
                    if len(new_ciphertexts) > 2:
                        timestamp = time.time()
                        new_ciphertexts[2] = self.scheme.add_constant(
                            new_ciphertexts[2], timestamp, self.keypair
                        )
                    packet.metadata['last_timestamp'] = time.time()
                elif op.op_type == OperationType.SCALE:
                    for i in range(len(new_ciphertexts)):
                        new_ciphertexts[i] = self.scheme.multiply_constant(
                            new_ciphertexts[i], op.value, self.keypair
                        )
            except NotImplementedError:
                packet.metadata.setdefault('unsupported_ops', []).append(str(op.op_type))
            except Exception as e:
                packet.metadata.setdefault('errors', []).append(str(e))
        
        elapsed = time.perf_counter() - start_time
        new_packet = TelemetryPacket(
            ciphertexts=new_ciphertexts,
            metadata=packet.metadata.copy(),
            hop_count=packet.hop_count + 1,
            operation_history=packet.operation_history +
                [f"Node{self.node_id}:{len(operations)}ops"],
            timing_history=packet.timing_history + [elapsed],
            noise_readings=packet.noise_readings.copy()
        )
        if len(new_packet.ciphertexts) > 0:
            noise = self.scheme.get_noise_budget(new_packet.ciphertexts[0])
            if noise >= 0:
                new_packet.noise_readings.append(noise)
        return new_packet