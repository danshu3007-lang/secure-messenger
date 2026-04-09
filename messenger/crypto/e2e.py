# messenger/crypto/e2e.py
"""
AES-256-GCM end-to-end encryption layer.

Key sharing model (pre-shared key):
  Both sender and receiver share a 32-byte secret.
  Exchange out-of-band (in person, QR code, secure copy).
  Default path: /etc/messenger/certs/e2e.key (chmod 600)

For production: replace PSK with ECDH key agreement over the TLS channel.
"""
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag

from ..common.constants import E2E_KEY
from ..common.exceptions import E2EKeyError

NONCE_SIZE = 12   # 96-bit nonce — standard for AES-GCM
KEY_SIZE   = 32   # 256-bit key


def load_psk(path: str = None) -> bytes:
    """
    Load pre-shared key from file.
    Must be exactly 32 bytes (256 bits), chmod 600.
    """
    path = path or E2E_KEY
    try:
        with open(path, "rb") as f:
            key = f.read()
    except FileNotFoundError:
        raise E2EKeyError(
            f"E2E key not found at {path}. "
            "Run: messenger-keygen"
        )
    if len(key) != KEY_SIZE:
        raise E2EKeyError(
            f"E2E key must be exactly {KEY_SIZE} bytes. "
            f"Got {len(key)}. Regenerate with: messenger-keygen"
        )
    return key


def derive_message_key(psk: bytes, context: bytes = b"messenger-e2e-v1") -> bytes:
    """
    Derive a per-session key from PSK using HKDF-SHA256.
    Best practice: never use the PSK directly as an encryption key.
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=None,
        info=context,
    )
    return hkdf.derive(psk)


def encrypt_message(plaintext: str, psk: bytes) -> bytes:
    """
    Encrypt a message with AES-256-GCM.
    Returns: [12-byte nonce][ciphertext + 16-byte GCM tag]
    The GCM tag provides authentication — any tampering is detected on decrypt.
    """
    key = derive_message_key(psk)
    nonce = os.urandom(NONCE_SIZE)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ciphertext


def decrypt_message(ciphertext_with_nonce: bytes, psk: bytes) -> str:
    """
    Decrypt and authenticate an AES-256-GCM message.
    Raises E2EKeyError if authentication tag is invalid (tampered or wrong key).
    """
    if len(ciphertext_with_nonce) <= NONCE_SIZE:
        raise E2EKeyError("Ciphertext too short — corrupted or empty.")
    nonce      = ciphertext_with_nonce[:NONCE_SIZE]
    ciphertext = ciphertext_with_nonce[NONCE_SIZE:]
    key = derive_message_key(psk)
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except InvalidTag:
        raise E2EKeyError(
            "E2E decryption failed: message was tampered with, "
            "or you are using the wrong key."
        )
    return plaintext.decode("utf-8")


def generate_psk(output_path: str = None) -> None:
    """
    CLI entry point: messenger-keygen
    Generates a new 256-bit PSK and writes it to file (chmod 600).
    """
    path = output_path or E2E_KEY
    os.makedirs(os.path.dirname(path), exist_ok=True)
    key = os.urandom(KEY_SIZE)
    with open(path, "wb") as f:
        f.write(key)
    os.chmod(path, 0o600)
    print(f"[✓] New E2E key written to {path}")
    print("    Share this file with your receiver out-of-band.")
    print("    Never transmit it over the network.")
