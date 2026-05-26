"""
RSA implementation with multiplicative homomorphic property.
Unpadded RSA: E(m1) * E(m2) = E(m1 * m2)
"""

import random
from typing import Tuple, Any

from core.base import HEScheme, HEKeyPair


class RSAScheme(HEScheme):
    """RSA scheme with multiplicative homomorphism."""
    
    def __init__(self, key_size: int = 2048):
        self.key_size = key_size
        self._name = "RSA"
    
    @property
    def name(self) -> str:
        return self._name
    
    # ----- Helper methods for prime generation and modular arithmetic -----
    def _gcd(self, a: int, b: int) -> int:
        while b:
            a, b = b, a % b
        return a
    
    def _egcd(self, a: int, b: int) -> Tuple[int, int, int]:
        if a == 0:
            return (b, 0, 1)
        else:
            g, y, x = self._egcd(b % a, a)
            return (g, x - (b // a) * y, y)
    
    def _modinv(self, a: int, m: int) -> int:
        g, x, _ = self._egcd(a, m)
        if g != 1:
            raise ValueError("Modular inverse does not exist")
        return x % m
    
    def _is_prime(self, n: int, k: int = 5) -> bool:
        """Miller-Rabin primality test."""
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
    
    # ----- Main RSA methods -----
    def keygen(self) -> HEKeyPair:
        p = self._generate_prime(self.key_size // 2)
        q = self._generate_prime(self.key_size // 2)
        n = p * q
        phi = (p - 1) * (q - 1)
        e = 65537
        while self._gcd(e, phi) != 1:
            e += 2
        d = self._modinv(e, phi)
        return HEKeyPair(
            public_key=(n, e),
            secret_key=(n, d),
            context=(p, q, phi)
        )
    
    def encrypt(self, plaintext: float, keypair: HEKeyPair) -> int:
        n, e = keypair.public_key
        m = int(plaintext)
        if m >= n:
            raise ValueError(f"Plaintext {m} too large for modulus {n}")
        return pow(m, e, n)
    
    def decrypt(self, ciphertext: int, keypair: HEKeyPair) -> float:
        n, d = keypair.secret_key
        return float(pow(ciphertext, d, n))
    
    def add(self, c1: int, c2: int, keypair: HEKeyPair) -> Any:
        raise NotImplementedError("RSA does not support homomorphic addition")
    
    def multiply(self, c1: int, c2: int, keypair: HEKeyPair) -> int:
        n, _ = keypair.public_key
        return (c1 * c2) % n
    
    def supports_additive(self) -> bool:
        return False
    
    def supports_multiplicative(self) -> bool:
        return True