"""
CKKS (Cheon-Kim-Kim-Song) scheme using Pyfhel.
Supports approximate floating-point arithmetic with addition and multiplication.
"""

from core.base import HEScheme, HEKeyPair


class CKKSScheme(HEScheme):
    """CKKS approximate homomorphic encryption scheme."""
    
    def __init__(self):
        self._name = "CKKS"
        self._he = None
        self._scale = 2**40
        try:
            from Pyfhel import Pyfhel
            self.Pyfhel = Pyfhel
        except ImportError:
            raise ImportError("Pyfhel is required for CKKS. Install with: pip install Pyfhel")
    
    @property
    def name(self) -> str:
        return self._name
    
    def keygen(self) -> HEKeyPair:
        from Pyfhel import Pyfhel
        self._he = Pyfhel()
        params = {
            'scheme': 'CKKS',
            'n': 2**14,
            'scale': self._scale,
            'qi_sizes': [60, 40, 40, 60]
        }
        self._he.contextGen(**params)
        self._he.keyGen()
        self._he.rotateKeyGen()
        return HEKeyPair(public_key=self._he, secret_key=self._he, context=params)
    
    def encrypt(self, plaintext: float, keypair: HEKeyPair):
        if self._he is None:
            self._he = keypair.public_key
        return self._he.encryptFrac([plaintext])
    
    def decrypt(self, ciphertext, keypair: HEKeyPair) -> float:
        if self._he is None:
            self._he = keypair.secret_key
        result = self._he.decryptFrac(ciphertext)
        if isinstance(result, (list, tuple)):
            return float(result[0])
        return float(result)
    
    def add(self, c1, c2, keypair: HEKeyPair):
        if self._he is None:
            self._he = keypair.public_key
        return c1 + c2
    
    def multiply(self, c1, c2, keypair: HEKeyPair):
        if self._he is None:
            self._he = keypair.public_key
        result = c1 * c2
        if hasattr(self._he, 'rescale_to_next'):
            result = self._he.rescale_to_next(result)
        return result
    
    def get_noise_budget(self, ciphertext) -> float:
        return -1.0  # CKKS uses approximate arithmetic