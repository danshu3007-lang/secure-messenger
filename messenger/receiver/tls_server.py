# messenger/receiver/tls_server.py
"""
TLS server context: accepts incoming connections, presents server certificate.

Security properties enforced:
  - TLS 1.3 minimum
  - Server selects cipher (OP_CIPHER_SERVER_PREFERENCE)
  - Optional mutual TLS (mTLS): client must present a cert signed by our CA
  - No SSLv2/3, TLS 1.0/1.1, no compression
"""
import socket
import ssl

from ..common.constants import (
    CA_CERT,
    SERVER_CERT,
    SERVER_KEY,
    TLS12_CIPHERS,
)


def build_tls_server_context(require_client_cert: bool = False) -> ssl.SSLContext:
    """
    Build a strict TLS 1.3 server context.

    require_client_cert=True enables mutual TLS:
      The server rejects any client that doesn't present a certificate
      signed by our CA. Use this in locked-down LAN deployments.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.maximum_version = ssl.TLSVersion.TLSv1_3

    # For TLS 1.2 fallback path: only AEAD ciphers
    ctx.set_ciphers(TLS12_CIPHERS)

    # Load server identity
    ctx.load_cert_chain(certfile=SERVER_CERT, keyfile=SERVER_KEY)

    # Disable weak options
    ctx.options |= ssl.OP_NO_SSLv2
    ctx.options |= ssl.OP_NO_SSLv3
    ctx.options |= ssl.OP_NO_TLSv1
    ctx.options |= ssl.OP_NO_TLSv1_1
    ctx.options |= ssl.OP_NO_COMPRESSION          # CRIME attack mitigation
    ctx.options |= ssl.OP_CIPHER_SERVER_PREFERENCE  # Server picks cipher order

    if require_client_cert:
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.load_verify_locations(cafile=CA_CERT)
    else:
        ctx.verify_mode = ssl.CERT_NONE

    return ctx


def create_server_socket(port: int, bind_host: str = "0.0.0.0") -> socket.socket:
    """
    Create a raw TCP server socket bound to bind_host:port.
    SO_REUSEADDR lets the service restart without TIME_WAIT delays.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((bind_host, port))
    sock.listen(5)
    return sock
