# messenger/receiver/server.py
"""
Main receiver loop.

Security guarantees:
  - No message is ever written to disk.
  - No message is ever written to the system log (only metadata is logged).
  - Message content appears on stdout ONLY, then is discarded.
  - Connection is closed immediately after one message.
"""
import socket
import ssl

from .tls_server import build_tls_server_context, create_server_socket
from ..common.serializer import decode_message
from ..common.constants import RECV_TIMEOUT_SECONDS
from ..common.exceptions import MessengerError, InvalidMessageError, E2EKeyError


def run_receiver(
    port: int,
    mtls: bool = False,
    local_only: bool = False,
    e2e: bool = False,
) -> None:
    """
    Accept connections in a loop.
    Each connection: TLS handshake → read one message → print → discard → close.

    Parameters
    ----------
    port       : TCP port to listen on.
    mtls       : If True, require client certificate (mutual TLS).
    local_only : If True, bind to 127.0.0.1 instead of 0.0.0.0.
    e2e        : If True, decrypt the AES-256-GCM layer after TLS unwrap.
    """
    bind_host = "127.0.0.1" if local_only else "0.0.0.0"
    ctx = build_tls_server_context(require_client_cert=mtls)
    raw_server = create_server_socket(port, bind_host)

    mode_flags = []
    if mtls:
        mode_flags.append("mTLS")
    if e2e:
        mode_flags.append("E2E")
    mode_str = " + ".join(mode_flags) if mode_flags else "TLS only"

    print(f"[*] Listening on {bind_host}:{port}  [{mode_str}]")
    print(f"[*] Press Ctrl+C to stop.\n")

    psk = None
    if e2e:
        from ..crypto.e2e import load_psk
        psk = load_psk()
        print("[*] E2E key loaded.\n")

    try:
        while True:
            raw_conn, addr = raw_server.accept()
            client_ip   = addr[0]
            client_port = addr[1]

            # Metadata only — never log message content here
            print(f"[+] Connection from {client_ip}:{client_port}")

            try:
                ssl_conn = ctx.wrap_socket(raw_conn, server_side=True)
                ssl_conn.settimeout(RECV_TIMEOUT_SECONDS)

                wire_message = decode_message(ssl_conn)

                if e2e and psk:
                    from ..crypto.e2e import decrypt_message
                    try:
                        ciphertext = bytes.fromhex(wire_message)
                        message = decrypt_message(ciphertext, psk)
                    except (ValueError, E2EKeyError) as exc:
                        print(f"[!] E2E decryption failed from {client_ip}: {exc}")
                        continue
                else:
                    message = wire_message

                # ── The only point message content is displayed ──
                # Goes to stdout only. Never logged. Never stored.
                print(f"\n  ┌─ MESSAGE from {client_ip} ─────────────────")
                print(f"  │  {message}")
                print(f"  └────────────────────────────────────────────\n")

                # Graceful TLS shutdown
                try:
                    ssl_conn.unwrap()
                except Exception:
                    pass

            except ssl.SSLError as exc:
                print(f"[!] TLS error from {client_ip}: {exc}")
            except InvalidMessageError as exc:
                print(f"[!] Bad message from {client_ip}: {exc}")
            except socket.timeout:
                print(f"[!] Read timeout from {client_ip}")
            except MessengerError as exc:
                print(f"[!] Error: {exc}")
            finally:
                try:
                    raw_conn.close()
                except Exception:
                    pass
                print(f"[-] Connection from {client_ip}:{client_port} closed.")

    except KeyboardInterrupt:
        print("\n[*] Receiver shutting down.")
    finally:
        raw_server.close()
