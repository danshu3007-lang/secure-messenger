# tests/unit/test_e2e_crypto.py
import os
import pytest

from messenger.crypto.e2e import (
    encrypt_message,
    decrypt_message,
    derive_message_key,
    generate_psk,
    NONCE_SIZE,
    KEY_SIZE,
)
from messenger.common.exceptions import E2EKeyError


@pytest.fixture
def psk():
    """Generate a fresh 32-byte PSK for each test."""
    return os.urandom(KEY_SIZE)


class TestKeyDerivation:
    def test_derive_key_length(self, psk):
        key = derive_message_key(psk)
        assert len(key) == KEY_SIZE

    def test_same_psk_same_key(self, psk):
        k1 = derive_message_key(psk)
        k2 = derive_message_key(psk)
        assert k1 == k2

    def test_different_context_different_key(self, psk):
        k1 = derive_message_key(psk, b"context-a")
        k2 = derive_message_key(psk, b"context-b")
        assert k1 != k2


class TestEncryptDecrypt:
    def test_roundtrip(self, psk):
        msg = "Hello, secure world!"
        ciphertext = encrypt_message(msg, psk)
        result = decrypt_message(ciphertext, psk)
        assert result == msg

    def test_unicode_roundtrip(self, psk):
        msg = "नमस्ते 🔐 Ünïcödé"
        ciphertext = encrypt_message(msg, psk)
        assert decrypt_message(ciphertext, psk) == msg

    def test_ciphertext_different_each_time(self, psk):
        msg = "Same message"
        c1 = encrypt_message(msg, psk)
        c2 = encrypt_message(msg, psk)
        # Different nonces → different ciphertexts
        assert c1 != c2

    def test_ciphertext_longer_than_nonce(self, psk):
        c = encrypt_message("Hi", psk)
        assert len(c) > NONCE_SIZE

    def test_wrong_key_raises(self, psk):
        wrong_psk = os.urandom(KEY_SIZE)
        ciphertext = encrypt_message("Secret", psk)
        with pytest.raises(E2EKeyError):
            decrypt_message(ciphertext, wrong_psk)

    def test_tampered_ciphertext_raises(self, psk):
        ciphertext = encrypt_message("Secret", psk)
        # Flip a byte in the ciphertext body
        tampered = bytearray(ciphertext)
        tampered[NONCE_SIZE] ^= 0xFF
        with pytest.raises(E2EKeyError):
            decrypt_message(bytes(tampered), psk)

    def test_truncated_ciphertext_raises(self, psk):
        with pytest.raises(E2EKeyError):
            decrypt_message(b"\x00" * NONCE_SIZE, psk)

    def test_empty_bytes_raises(self, psk):
        with pytest.raises(E2EKeyError):
            decrypt_message(b"", psk)


class TestGeneratePsk:
    def test_generates_file(self, tmp_path):
        key_path = str(tmp_path / "e2e.key")
        generate_psk(key_path)
        assert os.path.exists(key_path)
        with open(key_path, "rb") as f:
            key = f.read()
        assert len(key) == KEY_SIZE

    def test_file_permissions(self, tmp_path):
        key_path = str(tmp_path / "e2e.key")
        generate_psk(key_path)
        mode = oct(os.stat(key_path).st_mode)
        assert mode.endswith("600")
