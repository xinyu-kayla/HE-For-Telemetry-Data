"""Scheme registration and factory."""

from core.base import HEScheme
from core.rsa import RSAScheme
from core.elgamal import ElGamalScheme
from core.paillier import PaillierScheme
from core.bgv import BGVScheme
from core.bfv import BFVScheme
from core.ckks import CKKSScheme
from core.bgn import BGNScheme
from core.gsw import GSWScheme

_SCHEMES = {
    'RSA': RSAScheme,
    'ElGamal': ElGamalScheme,
    'Paillier': PaillierScheme,
    'BGV': BGVScheme,
    'BFV': BFVScheme,
    'CKKS': CKKSScheme,
    'BGN': BGNScheme,
    'GSW': GSWScheme,
}


def get_scheme(name: str) -> HEScheme:
    """Instantiate a scheme by name."""
    if name not in _SCHEMES:
        raise ValueError(f"Unknown scheme: {name}. Available: {list(_SCHEMES.keys())}")
    return _SCHEMES[name]()