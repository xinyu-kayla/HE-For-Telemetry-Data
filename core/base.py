"""Abstract base classes for homomorphic encryption schemes."""

import abc
from typing import Any, Tuple
from dataclasses import dataclass


@dataclass
class HEKeyPair:
    """Container for public/private key pairs"""
    public_key: Any
    secret_key: Any
    context: Any = None


class HEScheme(abc.ABC):
    """Abstract base class for all homomorphic encryption schemes"""
    
    @abc.abstractmethod
    def keygen(self) -> HEKeyPair:
        """Generate key pair for the encryption scheme"""
        pass
    
    @abc.abstractmethod
    def encrypt(self, plaintext: float, keypair: HEKeyPair) -> Any:
        """Encrypt a plaintext value"""
        pass
    
    @abc.abstractmethod
    def decrypt(self, ciphertext: Any, keypair: HEKeyPair) -> float:
        """Decrypt a ciphertext back to plaintext"""
        pass
    
    @abc.abstractmethod
    def add(self, c1: Any, c2: Any, keypair: HEKeyPair) -> Any:
        """Homomorphic addition of two ciphertexts"""
        pass
    
    @abc.abstractmethod
    def multiply(self, c1: Any, c2: Any, keypair: HEKeyPair) -> Any:
        """Homomorphic multiplication of two ciphertexts"""
        pass
    
    def add_constant(self, ciphertext: Any, constant: float, keypair: HEKeyPair) -> Any:
        """Add a constant to a ciphertext"""
        const_ct = self.encrypt(constant, keypair)
        return self.add(ciphertext, const_ct, keypair)
    
    def multiply_constant(self, ciphertext: Any, constant: float, keypair: HEKeyPair) -> Any:
        """Multiply a ciphertext by a constant"""
        const_ct = self.encrypt(constant, keypair)
        return self.multiply(ciphertext, const_ct, keypair)
    
    def get_noise_budget(self, ciphertext: Any) -> float:
        """Get current noise budget (returns -1 if not applicable)"""
        return -1.0
    
    def supports_additive(self) -> bool:
        """Return True if scheme supports homomorphic addition"""
        return True
    
    def supports_multiplicative(self) -> bool:
        """Return True if scheme supports homomorphic multiplication"""
        return True
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Name of the encryption scheme"""
        pass