# messenger/chat/cli.py
"""
Entry point for: chat <peer-ip> [options]

Both sides run this same command.
Each side listens on their own port and sends to the peer's port.

Example — two machines:
  Machine A (192.168.1.5):   chat 192.168.1.10 -lp 8443 -pp 8444
  Machine B (192.168.1.10):  chat 192.168.1.5  -lp 8444 -pp 8443

Same machine (two terminals for testing):
  Terminal 1:  chat 127.0.0.1 -lp 8443 -pp 8444
  Terminal 2:  chat 127.0.0.1 -lp 8444 -pp 8443
"""
import argparse
import sys

from .session import run_chat
from ..common.constants import DEFAULT_PORT


def main():
    parser = argparse.ArgumentParser(
        prog="chat",
        description="Two-way secure terminal chat.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
How to use (two machines):
  Machine A:  chat 192.168.1.10
  Machine B:  chat 192.168.1.5

Same machine (two terminals):
  Terminal 1:  chat 127.0.0.1 -lp 8443 -pp 8444
  Terminal 2:  chat 127.0.0.1 -lp 8444 -pp 8443

With E2E encryption:
  chat 192.168.1.10 --e2e
""",
    )
    parser.add_argument(
        "peer_ip",
        help="IP address of the person you want to chat with",
    )
    parser.add_argument(
        "-lp", "--listen-port",
        type=int,
        default=DEFAULT_PORT + 1,
        metavar="PORT",
        help=f"Port YOU listen on (default: {DEFAULT_PORT + 1}). "
             "Tell your peer to send to this port.",
    )
    parser.add_argument(
        "-pp", "--peer-port",
        type=int,
        default=DEFAULT_PORT,
        metavar="PORT",
        help=f"Port your PEER listens on (default: {DEFAULT_PORT}). "
             "Ask your peer what port they're on.",
    )
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="Enable AES-256-GCM end-to-end encryption (both sides need same key).",
    )

    args = parser.parse_args()

    if args.listen_port == args.peer_port:
        print("[!] Your listen port and peer port must be different.", file=sys.stderr)
        sys.exit(1)

    try:
        run_chat(
            peer_ip=args.peer_ip,
            peer_port=args.peer_port,
            my_port=args.listen_port,
            e2e=args.e2e,
        )
    except KeyboardInterrupt:
        print("\n[*] Bye.")
        sys.exit(0)
