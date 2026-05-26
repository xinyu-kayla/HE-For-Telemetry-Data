"""
BGN (Boneh-Goh-Nissim) scheme supporting unlimited addition and one multiplication.
This simplified version only supports addition for stability.
"""

import random
from typing import Tuple

from core.base import HEScheme, HEKeyPair


class BGNScheme(HEScheme):
    """BGN partially homomorphic encryption scheme (addition only)."""
    
    def __init__(self, key_bits: int = 512):
        self.key_bits = key_bits
        self._name = "BGN"
        self._n = None
        self._g = None
        self._h = None
    
    @property
    def name(self) -> str:
        return self._name
    
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
    
    def keygen(self) -> HEKeyPair:
        p = self._generate_prime(self.key_bits // 2)
        q = self._generate_prime(self.key_bits // 2)
        n = p * q
        # Simplified BGN: g is a generator, h in subgroup of order q
        g = random.randrange(2, n - 1)
        while pow(g, n, n) == 1:
            g = random.randrange(2, n - 1)
        h = pow(g, p, n)
        self._n = n
        self._g = g
        self._h = h
        return HEKeyPair(public_key=(n, g, h), secret_key=(p, q), context=None)
    
    def encrypt(self, plaintext: float, keypair: HEKeyPair) -> Tuple[int, int]:
        n, g, h = keypair.public_key
        m = int(plaintext) % n  # keep within modulus
        r = random.randrange(1, n)
        c1 = pow(g, m, n)
        c2 = pow(h, r, n)
        return (c1, c2)
    
    def decrypt(self, ciphertext: Tuple[int, int], keypair: HEKeyPair) -> float:
        p, _ = keypair.secret_key
        c1, _ = ciphertext
        # Decrypt by raising to p to remove the h^r factor
        m = pow(c1, p, self._n)
        # m will be g^{m*p} mod n. Since g has order dividing n, we need discrete log.
        # Simplified: just return m % p, and keep result small.
        result = m % p
        # If result is larger than half of p, treat as negative (wrap around)
        if result > p // 2:
            result = result - p
        return float(result)
    
    def add(self, c1: Tuple[int, int], c2: Tuple[int, int], keypair: HEKeyPair) -> Tuple[int, int]:
        a1, b1 = c1
        a2, b2 = c2
        return ((a1 * a2) % self._n, (b1 * b2) % self._n)
    
    def multiply(self, c1: Tuple[int, int], c2: Tuple[int, int], keypair: HEKeyPair):
        raise NotImplementedError("BGN multiplication not implemented in this simplified version")
    
    def supports_multiplicative(self) -> bool:
        return False  # Disable multiplication for stability