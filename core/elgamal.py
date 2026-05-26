"""
ElGamal encryption with multiplicative homomorphic property.
E(m1) * E(m2) = E(m1 * m2)
"""

import random
from typing import Tuple

from core.base import HEScheme, HEKeyPair


class ElGamalScheme(HEScheme):
    """ElGamal encryption scheme."""
    
    def __init__(self, key_size: int = 16):
        self.key_size = key_size
        self._name = "ElGamal"
    
    @property
    def name(self) -> str:
        return self._name
    
    # ----- Primality utilities -----
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
    
    def _primitive_root(self, p: int) -> int:
        """Find a primitive root modulo p."""
        if p == 2:
            return 1
        phi = p - 1
        factors = []
        n = phi
        i = 2
        while i * i <= n:
            if n % i == 0:
                factors.append(i)
                while n % i == 0:
                    n //= i
            i += 1
        if n > 1:
            factors.append(n)
        for g in range(2, p):
            ok = True
            for factor in factors:
                if pow(g, phi // factor, p) == 1:
                    ok = False
                    break
            if ok:
                return g
        return 2
    
    # ----- Main ElGamal -----
    def keygen(self) -> HEKeyPair:
        p = self._generate_prime(self.key_size)
        g = self._primitive_root(p)
        x = random.randrange(2, p - 1)   # private key
        h = pow(g, x, p)                 # public key component
        return HEKeyPair(
            public_key=(p, g, h),
            secret_key=(p, g, x),
            context=None
        )
    
    def encrypt(self, plaintext: float, keypair: HEKeyPair) -> Tuple[int, int]:
        p, g, h = keypair.public_key
        m = int(plaintext)
        y = random.randrange(2, p - 1)
        c1 = pow(g, y, p)
        c2 = (m * pow(h, y, p)) % p
        return (c1, c2)
    
    def decrypt(self, ciphertext: Tuple[int, int], keypair: HEKeyPair) -> float:
        p, g, x = keypair.secret_key
        c1, c2 = ciphertext
        s = pow(c1, x, p)
        s_inv = pow(s, p - 2, p)
        m = (c2 * s_inv) % p
        return float(m)
    
    def add(self, c1: Tuple[int, int], c2: Tuple[int, int], keypair: HEKeyPair):
        raise NotImplementedError("ElGamal does not support homomorphic addition")
    
    def multiply(self, c1: Tuple[int, int], c2: Tuple[int, int],
                 keypair: HEKeyPair) -> Tuple[int, int]:
        p, _, _ = keypair.public_key
        a1, b1 = c1
        a2, b2 = c2
        return ((a1 * a2) % p, (b1 * b2) % p)
    
    def supports_additive(self) -> bool:
        return False
    
    def supports_multiplicative(self) -> bool:
        return True