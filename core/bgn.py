"""BGN additive homomorphic encryption (exponential ElGamal variant)."""

import random
from typing import Tuple

from Crypto.Util import number

from core.base import HEScheme, HEKeyPair


class BGNScheme(HEScheme):
    """BGN partially homomorphic encryption scheme (addition only)."""

    def __init__(self, key_bits: int = 256):
        self.key_bits = key_bits
        self._name = "BGN"
        self.q = None
        self.g = None
        self.sk = None
        self.pk = None

    @property
    def name(self) -> str:
        return self._name

    def keygen(self) -> HEKeyPair:
        self.q = number.getPrime(self.key_bits)
        self.g = 2
        self.sk = number.getRandomRange(2, self.q - 2)
        self.pk = pow(self.g, self.sk, self.q)
        return HEKeyPair(
            public_key=(self.q, self.g, self.pk),
            secret_key=(self.q, self.g, self.sk),
            context=None,
        )

    def encrypt(self, plaintext: float, keypair: HEKeyPair) -> Tuple[int, int]:
        q, g, pk = keypair.public_key
        m = int(plaintext)
        r = number.getRandomRange(2, q - 2)
        c1 = pow(g, r, q)
        c2 = (pow(pk, r, q) * pow(g, m, q)) % q
        return (c1, c2)

    def decrypt(self, ciphertext: Tuple[int, int], keypair: HEKeyPair) -> float:
        q, g, sk = keypair.secret_key
        c1, c2 = ciphertext
        g_m = (c2 * pow(c1, -sk, q)) % q
        for m_test in range(200000):
            if pow(g, m_test, q) == g_m:
                return float(m_test)
        return -1.0

    def add(self, c1: Tuple[int, int], c2: Tuple[int, int], keypair: HEKeyPair) -> Tuple[int, int]:
        q, _, _ = keypair.public_key
        return ((c1[0] * c2[0]) % q, (c1[1] * c2[1]) % q)

    def multiply(self, c1, c2, keypair: HEKeyPair):
        raise NotImplementedError("BGN multiplication requires bilinear pairing environment")

    def supports_multiplicative(self) -> bool:
        return False