"""BFV scheme using Pyfhel with proper relinearization and multiply_plain."""

import numpy as np

from core.base import HEScheme, HEKeyPair


class BFVScheme(HEScheme):
    """BFV fully homomorphic encryption scheme."""

    def __init__(self):
        self._name = "BFV"
        self._he = None
        try:
            from Pyfhel import Pyfhel
            self.Pyfhel = Pyfhel
        except ImportError:
            raise ImportError("Pyfhel is required for BFV. Install with: pip install Pyfhel")

    @property
    def name(self) -> str:
        return self._name

    def keygen(self) -> HEKeyPair:
        self._he = self.Pyfhel()
        params = {"scheme": "BFV", "n": 2**12, "t": 65537, "sec": 128}
        self._he.contextGen(**params)
        self._he.keyGen()
        self._he.relinKeyGen()
        self._he.rotateKeyGen()
        return HEKeyPair(public_key=self._he, secret_key=self._he, context=params)

    def encrypt(self, plaintext: float, keypair: HEKeyPair):
        if self._he is None:
            self._he = keypair.public_key
        return self._he.encrypt(np.array([int(plaintext)], dtype=np.int64))

    def decrypt(self, ciphertext, keypair: HEKeyPair) -> float:
        if self._he is None:
            self._he = keypair.secret_key
        res = self._he.decrypt(ciphertext)
        if isinstance(res, (list, np.ndarray)):
            return float(res[0]) if len(res) > 0 else 0.0
        return float(res)

    def add(self, c1, c2, keypair: HEKeyPair):
        if self._he is None:
            self._he = keypair.public_key
        return c1 + c2

    def multiply(self, c1, c2, keypair: HEKeyPair):
        if self._he is None:
            self._he = keypair.public_key
        result = c1 * c2
        self._he.relinearize(result)
        return result

    def multiply_constant(self, ct, constant: float, keypair: HEKeyPair):
        """Multiply ciphertext by a plaintext constant using multiply_plain."""
        if self._he is None:
            self._he = keypair.public_key
        pt_int = int(constant)
        plain = self._he.encode(np.array([pt_int], dtype=np.int64))
        return self._he.multiply_plain(ct, plain)

    def get_noise_budget(self, ciphertext) -> float:
        if hasattr(self._he, "noiseBudget"):
            return float(self._he.noiseBudget(ciphertext))
        return -1.0