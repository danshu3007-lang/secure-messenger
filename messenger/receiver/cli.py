# messenger/receiver/cli.py
"""
Entry point for: messenger-receive [port] [--mtls] [--local] [--e2e]
"""
import argparse
import sys

from .server import run_receiver
from ..common.constants import DEFAULT_PORT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="messenger-receive",
        description="Listen for and display secure, stateless messages.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  messenger-receive                  # Listen on default port 8443
  messenger-receive 9000             # Custom port
  messenger-receive --local          # 127.0.0.1 only
  messenger-receive --mtls           # Require client certs (mTLS)
  messenger-receive --e2e            # Expect AES-256-GCM encrypted payload
  messenger-receive 9000 --mtls --e2e
""",
    )
    parser.add_argument(
        "port",
        nargs="?",
        type=int,
        default=DEFAULT_PORT,
        help=f"TCP port to listen on (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--mtls",
        action="store_true",
        help="Enable mutual TLS: require clients to present a CA-signed cert.",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Bind to 127.0.0.1 only — reject connections from other machines.",
    )
    parser.add_argument(
        "--e2e",
        action="store_true",
        help=(
            "Expect AES-256-GCM encrypted payload (E2E layer). "
            "Requires the same key as the sender (run messenger-keygen)."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not (1 <= args.port <= 65535):
        print(f"[!] Invalid port: {args.port}. Must be 1–65535.", file=sys.stderr)
        sys.exit(1)

    try:
        run_receiver(
            port=args.port,
            mtls=args.mtls,
            local_only=args.local,
            e2e=args.e2e,
        )
    except PermissionError:
        print(
            f"[!] Cannot bind to port {args.port}. "
            "Ports < 1024 require root. Use --port 8443 or higher.",
            file=sys.stderr,
        )
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[!] Stopped.", file=sys.stderr)
        sys.exit(0)
