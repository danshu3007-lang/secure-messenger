# messenger/shortcuts/rcv.py
"""
Short command: rcv [port]
Alias for messenger-receive with minimal typing.

Usage:
    rcv
    rcv 9000
    rcv --e2e
"""
import argparse
import sys

from ..receiver.server import run_receiver
from ..common.constants import DEFAULT_PORT


def main():
    parser = argparse.ArgumentParser(
        prog="rcv",
        description="Listen for secure messages.  rcv [port]",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rcv                # listen on port 8443
  rcv 9000           # custom port
  rcv --e2e          # expect encrypted messages
  rcv --local        # localhost only
""",
    )
    parser.add_argument("port", nargs="?", type=int, default=DEFAULT_PORT,
                        help=f"Port (default: {DEFAULT_PORT})")
    parser.add_argument("--e2e",   action="store_true")
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--mtls",  action="store_true")

    args = parser.parse_args()

    try:
        run_receiver(port=args.port, mtls=args.mtls,
                     local_only=args.local, e2e=args.e2e)
    except PermissionError:
        print(f"[!] Cannot bind port {args.port} — use port >= 1024.",
              file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[!] Stopped.")
        sys.exit(0)
