"""
BGV (Brakerski-Gentry-Vaikuntanathan) scheme using Pyfhel.
Supports both addition and multiplication.
"""

from core.base import HEScheme, HEKeyPair


class BGVScheme(HEScheme):
    """BGV fully homomorphic encryption scheme."""
    
    def __init__(self):
        self._name = "BGV"
        self._he = None
        try:
            from Pyfhel import Pyfhel
            self.Pyfhel = Pyfhel
        except ImportError:
            raise ImportError("Pyfhel is required for BGV. Install with: pip install Pyfhel")
    
    @property
    def name(self) -> str:
        return self._name
    
    def keygen(self) -> HEKeyPair:
        from Pyfhel import Pyfhel
        self._he = Pyfhel()
        params = {
            'scheme': 'BGV',
            'n': 2**13,
            't': 65537,
            't_bits': 20,
            'sec': 128
        }
        self._he.contextGen(**params)
        self._he.keyGen()
        return HEKeyPair(public_key=self._he, secret_key=self._he, context=params)
    
    def encrypt(self, plaintext: float, keypair: HEKeyPair):
        if self._he is None:
            self._he = keypair.public_key
        pt_int = int(plaintext)
        return self._he.encryptInt(pt_int)
    
    def decrypt(self, ciphertext, keypair: HEKeyPair) -> float:
        if self._he is None:
            self._he = keypair.secret_key
        return float(self._he.decryptInt(ciphertext)[0])
    
    def add(self, c1, c2, keypair: HEKeyPair):
        if self._he is None:
            self._he = keypair.public_key
        return c1 + c2
    
    def multiply(self, c1, c2, keypair: HEKeyPair):
        if self._he is None:
            self._he = keypair.public_key
        return c1 * c2
    
    def get_noise_budget(self, ciphertext) -> float:
        if hasattr(self._he, 'noiseBudget'):
            return float(self._he.noiseBudget(ciphertext))
        return -1.0