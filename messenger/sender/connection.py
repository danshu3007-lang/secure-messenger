# messenger/sender/connection.py
"""
High-level send logic: connect → encrypt (optional) → send → close.
No state is retained after this function returns.
"""
import os

from .tls_client import connect_tls
from ..common.serializer import encode_message
from ..common.exceptions import MessengerError


def send_message(host: str, port: int, message: str, e2e: bool = False) -> None:
    """
    Connect to receiver over TLS, send one message, close connection.
    If e2e=True, also encrypts the message payload with AES-256-GCM
    using the pre-shared key at $MESSENGER_CERT_DIR/e2e.key.
    """
    if e2e:
        from ..crypto.e2e import load_psk, encrypt_message as e2e_encrypt
        psk = load_psk()
        # Encrypt plaintext; encode the raw ciphertext bytes as latin-1
        # so it can travel through the JSON wire format transparently.
        ciphertext = e2e_encrypt(message, psk)
        wire_message = ciphertext.hex()   # hex string is safe in JSON
    else:
        wire_message = message

    ssl_sock = connect_tls(host, port)
    try:
        wire_data = encode_message(wire_message)
        ssl_sock.sendall(wire_data)
        # Graceful TLS shutdown before TCP close
        try:
            ssl_sock.unwrap()
        except Exception:
            pass
    finally:
        ssl_sock.close()
