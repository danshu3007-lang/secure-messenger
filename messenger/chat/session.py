# messenger/chat/session.py
"""
Two-way interactive chat session.

How it works:
  - Each peer runs BOTH a sender and a receiver simultaneously.
  - Your receiver listens on your local port.
  - When you type a message, it is sent to the peer's IP:port.
  - When the peer sends you a message, it appears on your screen.
  - Both sides can send and receive freely — true two-way chat.

Architecture:
  ┌─────────────────────────────────────┐
  │              YOUR MACHINE           │
  │                                     │
  │  [Listener thread]  port: MY_PORT   │◄── receives from peer
  │  [Input loop]       → PEER_IP:PORT  │──► sends to peer
  └─────────────────────────────────────┘

Usage:
  chat 192.168.1.5              # chat with peer, default ports
  chat 192.168.1.5 -lp 8444     # your listen port
  chat 192.168.1.5 -pp 8445     # peer's port
"""
import threading
import socket
import ssl
import sys
import os
import time
from datetime import datetime

from ..receiver.tls_server import build_tls_server_context, create_server_socket
from ..sender.connection import send_message
from ..common.serializer import decode_message
from ..common.constants import DEFAULT_PORT, RECV_TIMEOUT_SECONDS
from ..common.exceptions import MessengerError, InvalidMessageError


# ── ANSI colours ─────────────────────────────────────────────────────────────
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
DIM    = "\033[2m"
RESET  = "\033[0m"
CLEAR  = "\r\033[K"   # clear current terminal line


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _print_received(sender_ip: str, message: str):
    """Print incoming message above the input prompt."""
    sys.stdout.write(CLEAR)
    print(f"{DIM}[{_ts()}]{RESET} {CYAN}{sender_ip}{RESET} → {message}")
    sys.stdout.write(f"{GREEN}you{RESET} → ")
    sys.stdout.flush()


def _print_sent(peer_ip: str, message: str):
    sys.stdout.write(CLEAR)
    print(f"{DIM}[{_ts()}]{RESET} {GREEN}you{RESET} → {message}")
    sys.stdout.write(f"{GREEN}you{RESET} → ")
    sys.stdout.flush()


def _print_system(msg: str):
    sys.stdout.write(CLEAR)
    print(f"{YELLOW}[*] {msg}{RESET}")
    sys.stdout.write(f"{GREEN}you{RESET} → ")
    sys.stdout.flush()


def _print_error(msg: str):
    sys.stdout.write(CLEAR)
    print(f"{RED}[!] {msg}{RESET}")
    sys.stdout.write(f"{GREEN}you{RESET} → ")
    sys.stdout.flush()


# ── Listener thread ───────────────────────────────────────────────────────────

class ListenerThread(threading.Thread):
    """
    Runs in the background.
    Accepts TLS connections, reads one message per connection, prints it.
    """
    def __init__(self, my_port: int, e2e: bool = False, psk: bytes = None):
        super().__init__(daemon=True)
        self.my_port = my_port
        self.e2e     = e2e
        self.psk     = psk
        self._stop   = threading.Event()

    def run(self):
        ctx = build_tls_server_context(require_client_cert=False)
        try:
            server_sock = create_server_socket(self.my_port)
        except OSError as e:
            _print_error(f"Cannot bind port {self.my_port}: {e}")
            return

        server_sock.settimeout(1.0)   # non-blocking accept so we can stop

        while not self._stop.is_set():
            try:
                raw_conn, addr = server_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            sender_ip = addr[0]
            try:
                ssl_conn = ctx.wrap_socket(raw_conn, server_side=True)
                ssl_conn.settimeout(RECV_TIMEOUT_SECONDS)
                wire = decode_message(ssl_conn)

                if self.e2e and self.psk:
                    from ..crypto.e2e import decrypt_message
                    ciphertext = bytes.fromhex(wire)
                    message = decrypt_message(ciphertext, self.psk)
                else:
                    message = wire

                _print_received(sender_ip, message)

                try:
                    ssl_conn.unwrap()
                except Exception:
                    pass
            except Exception:
                pass
            finally:
                try:
                    raw_conn.close()
                except Exception:
                    pass

        server_sock.close()

    def stop(self):
        self._stop.set()


# ── Main chat session ─────────────────────────────────────────────────────────

def run_chat(
    peer_ip: str,
    peer_port: int = DEFAULT_PORT,
    my_port: int = DEFAULT_PORT + 1,
    e2e: bool = False,
    username: str = None,
):
    """
    Start an interactive two-way chat session.

    peer_ip   : IP address of the person you're chatting with
    peer_port : port your peer is listening on
    my_port   : port YOU listen on (peer must snd to this port)
    e2e       : enable AES-256-GCM end-to-end encryption
    """
    psk = None
    if e2e:
        from ..crypto.e2e import load_psk
        psk = load_psk()

    # ── Print header ──────────────────────────────────────────────────────────
    os.system("clear")
    print(f"{'═'*54}")
    print(f"  {CYAN}secure-chat{RESET}  |  two-way encrypted terminal chat")
    print(f"{'═'*54}")
    print(f"  Peer     : {CYAN}{peer_ip}:{peer_port}{RESET}")
    print(f"  Listening: port {GREEN}{my_port}{RESET}")
    print(f"  E2E      : {'ON (AES-256-GCM)' if e2e else 'OFF'}")
    print(f"  TLS      : 1.3")
    print(f"{'═'*54}")
    print(f"  {DIM}Type a message and press Enter to send.{RESET}")
    print(f"  {DIM}Type /quit or press Ctrl+C to exit.{RESET}")
    print(f"{'─'*54}\n")

    # ── Start listener in background ──────────────────────────────────────────
    listener = ListenerThread(my_port=my_port, e2e=e2e, psk=psk)
    listener.start()
    time.sleep(0.3)
    _print_system(f"Listening on port {my_port} — waiting for messages...")

    # ── Input loop ────────────────────────────────────────────────────────────
    try:
        while True:
            sys.stdout.write(f"{GREEN}you{RESET} → ")
            sys.stdout.flush()

            try:
                line = input()
            except EOFError:
                break

            line = line.strip()
            if not line:
                continue
            if line.lower() in ("/quit", "/exit", "/q"):
                break

            try:
                send_message(peer_ip, peer_port, line, e2e=e2e)
                # Reprint as sent message (clean look)
                sys.stdout.write("\033[F" + CLEAR)   # go up one line, clear
                print(f"{DIM}[{_ts()}]{RESET} {GREEN}you{RESET} → {line}")
            except MessengerError as exc:
                _print_error(f"Send failed: {exc}")

    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
        print(f"\n{YELLOW}[*] Chat ended.{RESET}")
