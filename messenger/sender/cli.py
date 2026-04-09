# messenger/sender/cli.py
"""
Entry point for: messenger-send <host> <message> [--port N] [--e2e]
"""
import argparse
import ipaddress
import sys

from .connection import send_message
from ..common.constants import DEFAULT_PORT
from ..common.exceptions import MessengerError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="messenger-send",
        description="Send a secure, stateless message to a receiver.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  messenger-send 192.168.1.5 "Hello, world!"
  messenger-send 192.168.1.5 "Secret" --port 9000 --e2e
  messenger-send receiver.local "Deploy ready"
""",
    )
    parser.add_argument(
        "host",
        help="Receiver IP address or hostname (e.g. 192.168.1.5)",
    )
    parser.add_argument(
        "message",
        help='The message to send (use quotes for spaces: "Hello world")',
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=DEFAULT_PORT,
        metavar="PORT",
        help=f"Receiver port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--e2e",
        action="store_true",
        help=(
            "Enable end-to-end AES-256-GCM encryption on top of TLS. "
            "Both sides must share the same key (run messenger-keygen first)."
        ),
    )
    return parser.parse_args()


def validate_host(host: str) -> None:
    """Accept either a valid IP address or a plausible hostname."""
    try:
        ipaddress.ip_address(host)
        return  # valid IP
    except ValueError:
        pass
    # Allow simple hostnames / FQDNs
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.")
    if not all(c in allowed for c in host):
        print(f"[!] Invalid host: {host!r}", file=sys.stderr)
        sys.exit(1)


def validate_port(port: int) -> None:
    if not (1 <= port <= 65535):
        print(f"[!] Invalid port: {port}. Must be 1–65535.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    args = parse_args()

    validate_host(args.host)
    validate_port(args.port)

    if not args.message.strip():
        print("[!] Message cannot be empty.", file=sys.stderr)
        sys.exit(1)

    try:
        send_message(args.host, args.port, args.message, e2e=args.e2e)
        e2e_note = " (E2E encrypted)" if args.e2e else ""
        print(f"[✓] Message sent securely{e2e_note} to {args.host}:{args.port}")
    except MessengerError as e:
        print(f"[✗] {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[!] Aborted.", file=sys.stderr)
        sys.exit(130)
