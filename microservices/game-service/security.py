"""
Utilities for encrypting and verifying immutable game history snapshots.
"""

import base64
import json
import os
import hmac
import hashlib
from typing import Any, Dict, Tuple

from cryptography.fernet import Fernet


class SecurityConfigurationError(RuntimeError):
    """Raised when GAME_HISTORY_KEY is missing or malformed."""


class HistorySecurity:
    """Handles encryption/decryption and integrity protection for history data."""

    def __init__(self, encoded_key: str | None = None) -> None:
        raw_key = (encoded_key or os.getenv('GAME_HISTORY_KEY', '')).strip()
        if not raw_key:
            raise SecurityConfigurationError('GAME_HISTORY_KEY environment variable is required')

        try:
            key_bytes = base64.urlsafe_b64decode(raw_key)
        except Exception as exc:  # pragma: no cover - defensive
            raise SecurityConfigurationError('GAME_HISTORY_KEY must be url-safe base64') from exc

        if len(key_bytes) != 32:
            raise SecurityConfigurationError('GAME_HISTORY_KEY must decode to 32 bytes (Fernet requirement)')

        self._fernet = Fernet(raw_key)
        # Derive a dedicated HMAC key so encryption and integrity keys are logically separated.
        self._hmac_key = hashlib.sha256(key_bytes + b'|battlecards-history|').digest()

    def encrypt_snapshot(self, payload: Dict[str, Any]) -> Tuple[bytes, str]:
        """Encrypt a snapshot and return (ciphertext, hex_hmac)."""
        serialized = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
        encrypted = self._fernet.encrypt(serialized)
        digest = hmac.new(self._hmac_key, encrypted, hashlib.sha256).hexdigest()
        return encrypted, digest

    def decrypt_snapshot(self, encrypted_payload: bytes) -> Dict[str, Any]:
        """Decrypt and deserialize an encrypted snapshot."""
        serialized = self._fernet.decrypt(encrypted_payload)
        return json.loads(serialized.decode('utf-8'))

    def verify_snapshot(self, encrypted_payload: bytes, integrity_hash: str) -> bool:
        """Verify the message authentication code for a stored snapshot."""
        expected = hmac.new(self._hmac_key, encrypted_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, integrity_hash)


_history_security: HistorySecurity | None = None


def get_history_security() -> HistorySecurity:
    """Lazily construct the singleton HistorySecurity helper."""
    global _history_security
    if _history_security is None:
        _history_security = HistorySecurity()
    return _history_security


def reset_history_security() -> None:
    """Reset cached helper (useful in tests)."""
    global _history_security
    _history_security = None

