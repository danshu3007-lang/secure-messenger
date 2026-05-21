# messenger/receiver/cli.py
"""
messenger-receive  — CLI entry point for the receiver.
"""
import argparse
import sys

from .server import run_receiver
from ..common.constants import DEFAULT_PORT
from ..common.exceptions import MessengerError


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="messenger-receive",
        description="Receive a secure message over TLS.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  messenger-receive                      # Listen on default port 8443
  messenger-receive 9000                 # Custom port
  messenger-receive --local              # Loopback only (127.0.0.1)
  messenger-receive --mtls               # Require client certificate
  messenger-receive --e2e                # Decrypt AES-256-GCM payload
  messenger-receive --e2e --quiet        # E2E + suppress message display
                                         # (safe under systemd — no content
                                         #  enters journald)
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
        "--local",
        action="store_true",
        help="Bind to 127.0.0.1 only (loopback, no LAN exposure)",
    )
    parser.add_argument(
        "--mtls",
        action="store_true",
        help="Require mutual TLS: client must present a valid certificate",
    )
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="Decrypt the AES-256-GCM payload layer (requires shared e2e.key)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help=(
            "Suppress message content display. "
            "Only metadata (IP, connection events) is printed. "
            "Use this when running as a systemd service to prevent "
            "message content from entering journald."
        ),
    )

    args = parser.parse_args()

    try:
        run_receiver(
            port=args.port,
            mtls=args.mtls,
            local_only=args.local,
            e2e=args.e2e,
            quiet=args.quiet,
        )
    except MessengerError as exc:
        print(f"[!] {exc}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(
            f"[!] Permission denied binding to port {args.port}. "
            "Try a port > 1024 or run with sudo.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
