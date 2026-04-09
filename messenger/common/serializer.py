# messenger/common/serializer.py
"""
Wire format:
  [4 bytes big-endian length][JSON UTF-8 payload]

Why length-prefix: prevents read-forever attacks.
Why JSON: human-auditable, no binary parser attack surface.
"""
import json
import struct

from .constants import MAX_MESSAGE_BYTES
from .exceptions import MessageTooLargeError, InvalidMessageError


def encode_message(text: str) -> bytes:
    """Serialize a text message to wire format."""
    if not text or not text.strip():
        raise ValueError("Message must be non-empty.")
    payload = json.dumps({"msg": text}, ensure_ascii=False).encode("utf-8")
    if len(payload) > MAX_MESSAGE_BYTES:
        raise MessageTooLargeError(
            f"Message too large: {len(payload)} bytes "
            f"(max {MAX_MESSAGE_BYTES})."
        )
    length_prefix = struct.pack(">I", len(payload))  # 4-byte big-endian
    return length_prefix + payload


def decode_message(sock) -> str:
    """
    Read exactly one length-prefixed message from a socket.
    Raises on malformed data, oversized messages, or closed connections.
    """
    raw_len = _recv_exactly(sock, 4)
    if not raw_len:
        raise InvalidMessageError("Connection closed before length header.")

    (msg_len,) = struct.unpack(">I", raw_len)

    if msg_len == 0:
        raise InvalidMessageError("Zero-length message received.")
    if msg_len > MAX_MESSAGE_BYTES:
        raise MessageTooLargeError(
            f"Incoming message claims {msg_len} bytes — "
            f"exceeds limit {MAX_MESSAGE_BYTES}. Dropping."
        )

    raw_payload = _recv_exactly(sock, msg_len)
    if not raw_payload:
        raise InvalidMessageError("Connection closed mid-message.")

    try:
        data = json.loads(raw_payload.decode("utf-8"))
        return data["msg"]
    except (json.JSONDecodeError, KeyError) as e:
        raise InvalidMessageError(f"Malformed message payload: {e}") from e


def _recv_exactly(sock, n: int) -> bytes:
    """Read exactly n bytes from socket. Returns b'' on clean close."""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return b""
        buf.extend(chunk)
    return bytes(buf)
