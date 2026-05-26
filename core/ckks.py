"""CKKS scheme using Pyfhel with multiply_plain via * operator."""

import numpy as np
import config
from core.base import HEScheme, HEKeyPair


class CKKSScheme(HEScheme):
    """CKKS approximate homomorphic encryption scheme."""

    def __init__(self):
        self._name = "CKKS"
        self._he = None
        try:
            from Pyfhel import Pyfhel
            self.Pyfhel = Pyfhel
        except ImportError:
            raise ImportError("Pyfhel is required for CKKS. Install with: pip install Pyfhel")

    @property
    def name(self) -> str:
        return self._name

    def keygen(self) -> HEKeyPair:
        self._he = self.Pyfhel()
        params = {
            "scheme": "CKKS",
            "n": config.POLY_MODULUS_DEGREE,
            "scale": config.CKKS_SCALE,
            "qi_sizes": config.CKKS_QI_SIZES,
        }
        self._he.contextGen(**params)
        self._he.keyGen()
        self._he.relinKeyGen()
        self._he.rotateKeyGen()
        return HEKeyPair(public_key=self._he, secret_key=self._he, context=params)

    def encrypt(self, plaintext: float, keypair: HEKeyPair):
        if self._he is None:
            self._he = keypair.public_key
        return self._he.encrypt(np.array([plaintext], dtype=np.float64))

    def decrypt(self, ciphertext, keypair: HEKeyPair) -> float:
        if self._he is None:
            self._he = keypair.secret_key
        try:
            result = self._he.decryptFrac(ciphertext)
        except AttributeError:
            result = self._he.decrypt(ciphertext)
        if isinstance(result, (list, np.ndarray)):
            return float(np.real(result[0])) if len(result) > 0 else 0.0
        return float(np.real(result))

    def add(self, c1, c2, keypair: HEKeyPair):
        if self._he is None:
            self._he = keypair.public_key
        return c1 + c2

    def multiply(self, c1, c2, keypair: HEKeyPair):
        if self._he is None:
            self._he = keypair.public_key
        result = c1 * c2
        self._he.relinearize(result)
        if hasattr(self._he, "rescale_to_next"):
            self._he.rescale_to_next(result)
        return result

    def multiply_constant(self, ct, constant: float, keypair: HEKeyPair):
        """Multiply ciphertext by a constant using Pyfhel's built-in operator."""
        if self._he is None:
            self._he = keypair.public_key
        return ct * constant   # Pyfhel handles encoding internally

    def get_noise_budget(self, ciphertext) -> float:
        return -1.0