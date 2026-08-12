"""Symmetric encryption for secrets stored in the database.

Used for Nextcloud app passwords: they are real credentials to a user's own Nextcloud
account, so a database dump alone must not be enough to use them.
"""

import base64
import hashlib
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

log = logging.getLogger(__name__)

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = os.getenv("NC_APP_PASSWORD_KEY")
        if not key:
            # Dev convenience. In production set NC_APP_PASSWORD_KEY to an independent value,
            # otherwise leaking SECRET_KEY also decrypts every stored app password.
            log.warning(
                "NC_APP_PASSWORD_KEY is not set — deriving it from SECRET_KEY. "
                "Set an independent key in production."
            )
            secret = os.getenv("SECRET_KEY", "change-me-in-production").encode()
            key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest()).decode()
        _fernet = Fernet(key)
    return _fernet


def encrypt_secret(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str | None:
    """Decrypt, or return None if the key has rotated or the value is corrupt.

    Callers degrade to a fallback credential rather than failing the request.
    """
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except (InvalidToken, ValueError):
        log.warning("Could not decrypt a stored secret — wrong or rotated key?")
        return None
