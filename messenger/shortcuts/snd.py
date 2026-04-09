# messenger/shortcuts/snd.py
"""
Short command: snd <ip> "<message>"
Alias for messenger-send with minimal typing.

Usage:
    snd 192.168.1.5 "hello"
    snd 192.168.1.5 "hello" -p 9000
    snd 192.168.1.5 "hello" --e2e
"""
import argparse
import ipaddress
import sys

from ..sender.connection import send_message
from ..common.constants import DEFAULT_PORT
from ..common.exceptions import MessengerError


def main():
    parser = argparse.ArgumentParser(
        prog="snd",
        description="Send a secure message.  snd <ip> \"<message>\"",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  snd 192.168.1.5 "hello"
  snd 192.168.1.5 "hello" -p 9000
  snd 192.168.1.5 "hello" --e2e
""",
    )
    parser.add_argument("host",    help="Receiver IP (e.g. 192.168.1.5)")
    parser.add_argument("message", help='Message to send (use quotes)')
    parser.add_argument("-p", "--port", type=int, default=DEFAULT_PORT,
                        metavar="PORT", help=f"Port (default: {DEFAULT_PORT})")
    parser.add_argument("--e2e", action="store_true",
                        help="AES-256-GCM end-to-end encryption")

    args = parser.parse_args()

    if not args.message.strip():
        print("[!] Message cannot be empty.", file=sys.stderr)
        sys.exit(1)

    try:
        send_message(args.host, args.port, args.message, e2e=args.e2e)
        print(f"[✓] → {args.host}:{args.port}  \"{args.message}\"")
    except MessengerError as e:
        print(f"[✗] {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[!] Aborted.")
        sys.exit(130)
