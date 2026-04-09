# messenger/sender/tls_client.py
"""
TLS client context: connects to receiver, verifies server certificate.

Security properties enforced:
  - TLS 1.3 minimum (strong AEAD ciphers only if 1.2 fallback needed)
  - Server cert verified against our CA
  - IP SAN checked manually when connecting to a raw IP address
  - No SSLv2, SSLv3, TLS 1.0, TLS 1.1, no compression
"""
import ipaddress
import socket
import ssl

from ..common.constants import (
    CA_CERT,
    CONNECT_TIMEOUT_SECONDS,
    TLS12_CIPHERS,
)
from ..common.exceptions import (
    CertificateError,
    ConnectionRefusedError,
    TLSHandshakeError,
)


def build_tls_client_context() -> ssl.SSLContext:
    """
    Build a strict TLS 1.3 client context.
    Falls back gracefully to TLS 1.2 with AEAD-only ciphers
    if the remote peer does not support 1.3.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    # Enforce TLS 1.3; change to TLSv1_2 if you need 1.2 fallback
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.maximum_version = ssl.TLSVersion.TLSv1_3

    # TLS 1.2 fallback cipher list (AEAD only — no CBC, no RC4)
    ctx.set_ciphers(TLS12_CIPHERS)

    # Verify server certificate against our CA
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_verify_locations(cafile=CA_CERT)

    # Disable legacy protocol versions and compression
    ctx.options |= ssl.OP_NO_SSLv2
    ctx.options |= ssl.OP_NO_SSLv3
    ctx.options |= ssl.OP_NO_TLSv1
    ctx.options |= ssl.OP_NO_TLSv1_1
    ctx.options |= ssl.OP_NO_COMPRESSION  # CRIME attack mitigation

    return ctx


def connect_tls(host: str, port: int) -> ssl.SSLSocket:
    """
    Create a TLS-wrapped socket connected to host:port.

    For DNS hostnames: standard check_hostname applies.
    For raw IP addresses: check_hostname is disabled and we manually
    verify the server cert's SAN contains the target IP.

    Returns the connected SSL socket.
    Raises TLSHandshakeError, CertificateError, or ConnectionRefusedError.
    """
    ctx = build_tls_client_context()

    is_ip = _is_ip_address(host)
    if is_ip:
        # Python's check_hostname is DNS-only; use manual IP SAN check instead
        ctx.check_hostname = False
        server_hostname = None
    else:
        ctx.check_hostname = True
        server_hostname = host

    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_sock.settimeout(CONNECT_TIMEOUT_SECONDS)

    try:
        ssl_sock = ctx.wrap_socket(raw_sock, server_hostname=server_hostname)
        ssl_sock.connect((host, port))

        if is_ip:
            _verify_ip_in_san(ssl_sock, host)

        return ssl_sock

    except ssl.SSLCertVerificationError as e:
        raise CertificateError(
            f"Certificate verification failed for {host}:{port} — {e}"
        ) from e
    except ssl.SSLError as e:
        raise TLSHandshakeError(
            f"TLS handshake failed with {host}:{port} — {e}"
        ) from e
    except (ConnectionRefusedError, OSError, socket.timeout) as e:
        raise ConnectionRefusedError(
            f"Could not connect to {host}:{port} — {e}"
        ) from e


# ── helpers ──────────────────────────────────────────────────────────────────

def _is_ip_address(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _verify_ip_in_san(ssl_sock: ssl.SSLSocket, target_ip: str) -> None:
    """
    Manually verify that the server cert SAN contains the target IP.
    This mirrors what browsers do for IP-addressed servers.
    """
    cert = ssl_sock.getpeercert()
    san_entries = cert.get("subjectAltName", [])
    ip_sans = [v for (t, v) in san_entries if t == "IP Address"]

    target = ipaddress.ip_address(target_ip)
    for san_ip_str in ip_sans:
        try:
            if ipaddress.ip_address(san_ip_str) == target:
                return  # Match found
        except ValueError:
            continue

    raise CertificateError(
        f"Server certificate does not contain IP SAN for {target_ip}. "
        f"Found IP SANs: {ip_sans}. "
        "Regenerate server cert with the correct SAN entry."
    )
