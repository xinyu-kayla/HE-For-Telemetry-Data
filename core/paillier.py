"""
Paillier cryptosystem with additive homomorphic property.
E(m1) * E(m2) = E(m1 + m2)

Supports floating-point numbers by scaling with SCALE factor.
"""

import random
import math
from typing import Any

from core.base import HEScheme, HEKeyPair


class PaillierScheme(HEScheme):
    """Paillier encryption scheme with floating-point scaling."""
    
    def __init__(self, key_size: int = 2048):
        self.key_size = key_size
        self._name = "Paillier"
        self.SCALE = 100  # Scale factor for floating-point precision
    
    @property
    def name(self) -> str:
        return self._name
    
    # ----- Helper functions -----
    def _lcm(self, a: int, b: int) -> int:
        return a // math.gcd(a, b) * b
    
    def _L(self, x: int, n: int) -> int:
        return (x - 1) // n
    
    def _is_prime(self, n: int, k: int = 5) -> bool:
        if n < 2:
            return False
        for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]:
            if n % p == 0:
                return n == p
        d = n - 1
        s = 0
        while d % 2 == 0:
            d //= 2
            s += 1
        for _ in range(k):
            a = random.randrange(2, n - 1)
            x = pow(a, d, n)
            if x == 1 or x == n - 1:
                continue
            for _ in range(s - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        return True
    
    def _generate_prime(self, bits: int) -> int:
        while True:
            n = random.getrandbits(bits)
            n |= (1 << bits - 1) | 1
            if self._is_prime(n):
                return n
    
    # ----- Main Paillier -----
    def keygen(self) -> HEKeyPair:
        p = self._generate_prime(self.key_size // 2)
        q = self._generate_prime(self.key_size // 2)
        n = p * q
        nsq = n * n
        lambda_ = self._lcm(p - 1, q - 1)
        g = n + 1
        mu = pow(self._L(pow(g, lambda_, nsq), n), -1, n)
        return HEKeyPair(
            public_key=(n, g),
            secret_key=(lambda_, mu),
            context=nsq
        )
    
    def encrypt(self, plaintext: float, keypair: HEKeyPair) -> int:
        """Encrypt float by scaling to integer."""
        n, g = keypair.public_key
        nsq = n * n
        m = int(round(plaintext * self.SCALE))
        r = random.randrange(1, n)
        while math.gcd(r, n) != 1:
            r = random.randrange(1, n)
        ciphertext = (pow(g, m, nsq) * pow(r, n, nsq)) % nsq
        return ciphertext
    
    def decrypt(self, ciphertext: int, keypair: HEKeyPair) -> float:
        """Decrypt and divide by scale."""
        n, _ = keypair.public_key
        lambda_, mu = keypair.secret_key
        nsq = n * n
        x = pow(ciphertext, lambda_, nsq)
        m = (self._L(x, n) * mu) % n
        return float(m) / self.SCALE
    
    def add(self, c1: int, c2: int, keypair: HEKeyPair) -> int:
        n, _ = keypair.public_key
        nsq = n * n
        return (c1 * c2) % nsq
    
    def multiply(self, c1: int, c2: int, keypair: HEKeyPair):
        raise NotImplementedError("Paillier does not support homomorphic multiplication")
    
    def supports_additive(self) -> bool:
        return True
    
    def supports_multiplicative(self) -> bool:
        return False