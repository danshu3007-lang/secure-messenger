# tests/unit/test_e2e_crypto.py
"""
Unit tests for the E2E encryption layer.

Tests verify:
  - Encrypt/decrypt round-trip works correctly.
  - Every encrypt call produces a different ciphertext (random nonce).
  - Per-message key derivation: same PSK + different nonce → different key.
  - Tampered ciphertext raises E2EKeyError (GCM tag validation).
  - Wrong key raises E2EKeyError.
  - Short/empty ciphertext raises E2EKeyError.
"""
import os
import pytest

from messenger.crypto.e2e import (
    encrypt_message,
    decrypt_message,
    derive_message_key,
    NONCE_SIZE,
    KEY_SIZE,
)
from messenger.common.exceptions import E2EKeyError


@pytest.fixture
def psk() -> bytes:
    """A fresh random 32-byte PSK for each test."""
    return os.urandom(32)


class TestEncryptDecryptRoundTrip:
    def test_basic_roundtrip(self, psk):
        plaintext = "Hello, secure world!"
        ciphertext = encrypt_message(plaintext, psk)
        assert decrypt_message(ciphertext, psk) == plaintext

    def test_empty_string(self, psk):
        plaintext = ""
        ciphertext = encrypt_message(plaintext, psk)
        assert decrypt_message(ciphertext, psk) == plaintext

    def test_unicode_message(self, psk):
        plaintext = "नमस्ते दुनिया 🔐"
        ciphertext = encrypt_message(plaintext, psk)
        assert decrypt_message(ciphertext, psk) == plaintext

    def test_long_message(self, psk):
        plaintext = "A" * 3000
        ciphertext = encrypt_message(plaintext, psk)
        assert decrypt_message(ciphertext, psk) == plaintext


class TestNonceUniqueness:
    def test_same_plaintext_different_ciphertext(self, psk):
        """Each encryption must produce a different ciphertext (random nonce)."""
        c1 = encrypt_message("same message", psk)
        c2 = encrypt_message("same message", psk)
        assert c1 != c2, "Two encryptions of the same message must differ"

    def test_ciphertext_longer_than_nonce(self, psk):
        ct = encrypt_message("test", psk)
        assert len(ct) > NONCE_SIZE


class TestPerMessageKeyDiversity:
    def test_different_nonces_produce_different_keys(self, psk):
        """
        The key fix: nonce is used as HKDF salt, so different nonces
        produce different derived keys even from the same PSK.
        """
        nonce1 = os.urandom(NONCE_SIZE)
        nonce2 = os.urandom(NONCE_SIZE)
        # In the astronomically unlikely event of nonce collision, regenerate
        while nonce2 == nonce1:
            nonce2 = os.urandom(NONCE_SIZE)

        key1 = derive_message_key(psk, nonce1)
        key2 = derive_message_key(psk, nonce2)

        assert key1 != key2, (
            "Different nonces must produce different derived keys. "
            "If this fails, the nonce is not being used as HKDF salt."
        )

    def test_derived_key_length(self, psk):
        nonce = os.urandom(NONCE_SIZE)
        key = derive_message_key(psk, nonce)
        assert len(key) == KEY_SIZE

    def test_same_nonce_same_key(self, psk):
        """Deterministic: same inputs → same derived key."""
        nonce = os.urandom(NONCE_SIZE)
        key1 = derive_message_key(psk, nonce)
        key2 = derive_message_key(psk, nonce)
        assert key1 == key2


class TestTamperDetection:
    def test_bit_flip_in_ciphertext_raises(self, psk):
        ct = bytearray(encrypt_message("test message", psk))
        ct[-1] ^= 0xFF   # flip last byte (inside GCM tag)
        with pytest.raises(E2EKeyError, match="tampered"):
            decrypt_message(bytes(ct), psk)

    def test_byte_appended_raises(self, psk):
        ct = encrypt_message("test", psk) + b"\x00"
        with pytest.raises(E2EKeyError):
            decrypt_message(ct, psk)

    def test_truncated_ciphertext_raises(self, psk):
        ct = encrypt_message("test", psk)
        with pytest.raises(E2EKeyError):
            decrypt_message(ct[:NONCE_SIZE], psk)   # only nonce, no payload

    def test_empty_ciphertext_raises(self, psk):
        with pytest.raises(E2EKeyError):
            decrypt_message(b"", psk)


class TestWrongKey:
    def test_wrong_psk_raises(self, psk):
        ct = encrypt_message("secret", psk)
        wrong_psk = os.urandom(32)
        with pytest.raises(E2EKeyError):
            decrypt_message(ct, wrong_psk)
