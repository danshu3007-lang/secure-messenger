# messenger/crypto/e2e.py
"""
AES-256-GCM end-to-end encryption layer.

Key model: Pre-Shared Key (PSK)
  Both sender and receiver share a 32-byte secret.
  Exchange out-of-band: in person, QR code, or secure file copy.
  Default path: /etc/messenger/certs/e2e.key  (chmod 600)

Security properties:
  - Each message uses a unique random 96-bit nonce (os.urandom).
  - Per-message key is derived from PSK + nonce via HKDF-SHA256.
    This means every message uses a DIFFERENT encryption key.
  - AES-256-GCM provides authenticated encryption (AEAD):
    any bit-flip in the ciphertext is detected and rejected.
  - If the PSK is compromised, all recorded traffic can be decrypted.
    This is a known limitation of PSK-based systems.
    Roadmap: replace PSK with ECDH ephemeral key exchange.

What this is NOT:
  - Not Signal Protocol / Double Ratchet
  - Not forward-secret at the session level (no ratcheting)
  - Not anonymous (IPs are visible at the TLS layer)
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
CONTEXT    = b"messenger-e2e-v1"


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


def derive_message_key(psk: bytes, nonce: bytes) -> bytes:
    """
    Derive a per-message key from PSK + nonce using HKDF-SHA256.

    Using the nonce as HKDF salt means every message gets a unique
    derived key — even if two messages have the same plaintext,
    the ciphertext and key are both different.

    This is stronger than using the PSK directly as the encryption key.
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=nonce,        # unique per message — critical for key diversity
        info=CONTEXT,
    )
    return hkdf.derive(psk)


def encrypt_message(plaintext: str, psk: bytes) -> bytes:
    """
    Encrypt a message with AES-256-GCM.

    Steps:
      1. Generate a random 96-bit nonce.
      2. Derive a per-message key via HKDF(PSK, nonce).
      3. Encrypt + authenticate with AES-256-GCM.

    Wire format: [12-byte nonce][ciphertext][16-byte GCM tag]
    The GCM tag is appended automatically by the AESGCM library.
    """
    nonce = os.urandom(NONCE_SIZE)
    key = derive_message_key(psk, nonce)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ciphertext


def decrypt_message(ciphertext_with_nonce: bytes, psk: bytes) -> str:
    """
    Decrypt and authenticate an AES-256-GCM message.

    Extracts the nonce, re-derives the per-message key, then decrypts.
    Raises E2EKeyError if the GCM tag is invalid (tampered or wrong key).
    """
    if len(ciphertext_with_nonce) <= NONCE_SIZE:
        raise E2EKeyError("Ciphertext too short — corrupted or empty.")

    nonce      = ciphertext_with_nonce[:NONCE_SIZE]
    ciphertext = ciphertext_with_nonce[NONCE_SIZE:]

    key = derive_message_key(psk, nonce)
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
    print("    NEVER transmit it over the network.")
    print(f"    Key fingerprint (first 8 bytes): {key[:8].hex()}")
