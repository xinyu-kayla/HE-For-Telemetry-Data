"""GSW (Gentry-Sahai-Waters) fully homomorphic encryption scheme.

Supports boolean (0/1) plaintexts with unlimited additions and
a limited number of multiplications before noise overwhelms the signal.
"""

import numpy as np

from core.base import HEScheme, HEKeyPair


class GSWScheme(HEScheme):
    """GSW fully homomorphic encryption scheme (boolean plaintexts)."""

    def __init__(self, n: int = 4, q: int = 2**20, sigma: int = 1):
        self.n = n
        self.q = q
        self.sigma = sigma
        self.l = int(np.log2(q))
        self.m = (n + 1) * self.l
        self._name = "GSW"
        self._noise_budgets = []

        # Key placeholders
        self.s_orig = None
        self.sk = None
        self.G = None

    @property
    def name(self) -> str:
        return self._name

    def _bit_decomp_vector(self, v):
        """Bit-decompose a vector into l bits per entry."""
        res = []
        for val in v:
            val = int(val) % self.q
            res.extend([(val >> i) & 1 for i in range(self.l)])
        return np.array(res, dtype=np.int64)

    def g_inv(self, M):
        """G^{-1} : bit-decompose each column of M. Output shape: (m, m)."""
        return np.column_stack(
            [self._bit_decomp_vector(M[:, j]) for j in range(M.shape[1])]
        )

    def keygen(self) -> HEKeyPair:
        s = np.random.randint(0, 2, size=self.n)
        self.s_orig = s
        # Secret key vector: sk = (-s, 1) so that sk^T · [A; b] = -sA + b ≈ e
        self.sk = np.append(-s, 1)

        # Gadget matrix G of shape (n+1, m)
        self.G = np.zeros((self.n + 1, self.m), dtype=np.int64)
        for i in range(self.n + 1):
            for j in range(self.l):
                self.G[i, i * self.l + j] = 1 << j

        return HEKeyPair(
            public_key={"n": self.n, "q": self.q, "m": self.m, "G": self.G},
            secret_key=self.sk,
            context={"s_orig": self.s_orig},
        )

    def encrypt(self, plaintext: float, keypair: HEKeyPair) -> np.ndarray:
        m_val = int(plaintext)
        n = keypair.public_key["n"]
        q = keypair.public_key["q"]
        m = keypair.public_key["m"]
        G = keypair.public_key["G"]
        s_orig = keypair.context["s_orig"]

        A = np.random.randint(0, q, size=(n, m))
        e = np.random.randint(-2, 3, size=m)
        b = (A.T @ s_orig + e) % q
        C = np.vstack([A, b])
        C = (C + m_val * G) % q
        return C

    def decrypt(self, ciphertext: np.ndarray, keypair: HEKeyPair) -> float:
        sk = keypair.secret_key
        q = keypair.public_key["q"]
        v = (sk @ ciphertext) % q
        val = v[-1]
        if abs(val - q // 2) < q // 4:
            return 1.0
        return 0.0

    def add(
        self, c1: np.ndarray, c2: np.ndarray, keypair: HEKeyPair
    ) -> np.ndarray:
        q = keypair.public_key["q"]
        return (c1 + c2) % q

    def multiply(
        self, c1: np.ndarray, c2: np.ndarray, keypair: HEKeyPair
    ) -> np.ndarray:
        q = keypair.public_key["q"]
        Ginv = self.g_inv(c2)
        return (c1 @ Ginv) % q

    def get_noise_budget(self, ciphertext) -> float:
        q = ciphertext.shape[0]
        noise_est = float(np.sum(np.abs(ciphertext))) / (q * 1000.0)
        self._noise_budgets.append(noise_est)
        return noise_est