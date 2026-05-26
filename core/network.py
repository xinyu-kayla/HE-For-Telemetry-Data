"""Network simulator that manages multiple routers."""

from typing import List

from core.base import HEScheme, HEKeyPair
from core.packet import TelemetryPacket
from core.router import RouterNode
from core.operations import RoutingOperation


class NetworkSimulator:
    """Simulates a multi-hop network with a sequence of router nodes."""
    
    def __init__(self, scheme: HEScheme):
        self.scheme = scheme
        self.keypair = None
        self.routers: List[RouterNode] = []
    
    def initialize(self, num_routers: int) -> HEKeyPair:
        self.keypair = self.scheme.keygen()
        self.routers = [RouterNode(i, self.scheme, self.keypair)
                        for i in range(num_routers)]
        return self.keypair
    
    def send_packet(self, plaintext_values: List[float],
                    router_operations: List[List[RoutingOperation]]) -> TelemetryPacket:
        if self.keypair is None:
            raise RuntimeError("Network not initialized. Call initialize() first.")
        if len(router_operations) != len(self.routers):
            raise ValueError("Operation count mismatch.")
        
        initial_ciphertexts = [self.scheme.encrypt(val, self.keypair)
                               for val in plaintext_values]
        packet = TelemetryPacket(ciphertexts=initial_ciphertexts,
                                 metadata={'source_values': plaintext_values})
        for router, ops in zip(self.routers, router_operations):
            packet = router.process_packet(packet, ops)
        return packet
    
    def get_final_value(self, packet: TelemetryPacket) -> float:
        if not packet.ciphertexts:
            return 0.0
        return self.scheme.decrypt(packet.ciphertexts[0], self.keypair)
    
    def get_all_fields(self, packet: TelemetryPacket) -> List[float]:
        return [self.scheme.decrypt(ct, self.keypair) for ct in packet.ciphertexts]