"""BGV scheme using Pyfhel with proper relinearization."""

import numpy as np

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
            raise ImportError(
                "Pyfhel is required for BGV. Install with: pip install Pyfhel"
            )

    @property
    def name(self) -> str:
        return self._name

    def keygen(self) -> HEKeyPair:
        self._he = self.Pyfhel()
        params = {"scheme": "BGV", "n": 2**12, "t": 65537, "sec": 128}
        self._he.contextGen(**params)
        self._he.keyGen()
        self._he.relinKeyGen()
        return HEKeyPair(public_key=self._he, secret_key=self._he, context=params)

    def encrypt(self, plaintext: float, keypair: HEKeyPair):
        if self._he is None:
            self._he = keypair.public_key
        pt_int = int(plaintext)
        return self._he.encrypt(pt_int)    # 直接传整数，Pyfhel 3.x 支持

    def decrypt(self, ciphertext, keypair: HEKeyPair) -> float:
        if self._he is None:
            self._he = keypair.secret_key
        res = self._he.decrypt(ciphertext)
        # 解密返回单个整数或列表，统一处理
        if isinstance(res, (list, np.ndarray)):
            return float(res[-1])   # 取最后一个槽（通常包含有效值）
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

    def get_noise_budget(self, ciphertext) -> float:
        if hasattr(self._he, "noiseBudget"):
            return float(self._he.noiseBudget(ciphertext))
        return -1.0