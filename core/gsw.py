"""
GSW (Gentry-Sahai-Waters) fully homomorphic encryption scheme.
Simplified implementation for demonstration.
"""

import random
import numpy as np
from typing import List, Any

from core.base import HEScheme, HEKeyPair


class GSWScheme(HEScheme):
    """GSW fully homomorphic encryption scheme."""
    
    def __init__(self, n: int = 32, q: int = 2**30, B: int = 2**15):
        self.n = n      # LWE dimension
        self.q = q      # modulus
        self.B = B      # bound
        self._name = "GSW"
        self._noise_budgets = []
    
    @property
    def name(self) -> str:
        return self._name
    
    def _sample_uniform(self, size: int) -> List[int]:
        return [random.randrange(self.q) for _ in range(size)]
    
    def _sample_error(self, sigma: float = 3.2) -> int:
        return int(np.random.normal(0, sigma)) % self.q
    
    def keygen(self) -> HEKeyPair:
        # Secret key (LWE secret)
        s = [random.randrange(self.q) for _ in range(self.n)]
        # Public key (A, b = A*s + e)
        A = [self._sample_uniform(self.n) for _ in range(self.n)]
        e = self._sample_error()
        b = [(sum(A[i][j] * s[j] for j in range(self.n)) + e) % self.q 
             for i in range(self.n)]
        return HEKeyPair(public_key=(A, b), secret_key=s, context=None)
    
    def encrypt(self, plaintext: float, keypair: HEKeyPair) -> List[List[int]]:
        A, b = keypair.public_key
        m = int(plaintext)
        C = []
        for i in range(len(A)):
            row = []
            for j in range(len(A[i])):
                r = random.randrange(2)
                val = r * A[i][j]
                row.append(val % self.q)
            row[-1] = (row[-1] + m * (1 if i == len(A)-1 else 0)) % self.q
            C.append(row)
        return C
    
    def decrypt(self, ciphertext: List[List[int]], keypair: HEKeyPair) -> float:
        s = keypair.secret_key
        n = len(s)
        result = 0
        for i in range(n):
            result += ciphertext[i][i] * s[i]
        result = result % self.q
        # Simplified extraction
        if result > self.q // 2:
            result = 0
        else:
            result = 1
        return float(result)
    
    def add(self, c1: List[List[int]], c2: List[List[int]], keypair: HEKeyPair) -> List[List[int]]:
        n = len(c1)
        result = []
        for i in range(n):
            row = []
            for j in range(n):
                row.append((c1[i][j] + c2[i][j]) % self.q)
            result.append(row)
        return result
    
    def multiply(self, c1: List[List[int]], c2: List[List[int]], keypair: HEKeyPair) -> List[List[int]]:
        n = len(c1)
        result = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                total = 0
                for k in range(n):
                    total += c1[i][k] * c2[k][j]
                result[i][j] = total % self.q
        return result
    
    def get_noise_budget(self, ciphertext: Any) -> float:
        noise_est = sum(sum(abs(v) for v in row) for row in ciphertext) / (self.q * len(ciphertext))
        self._noise_budgets.append(noise_est)
        return noise_est