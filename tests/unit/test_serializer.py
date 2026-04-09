# tests/unit/test_serializer.py
import socket
import pytest

from messenger.common.serializer import encode_message, decode_message
from messenger.common.exceptions import MessageTooLargeError, InvalidMessageError


def _socketpair_roundtrip(wire: bytes) -> str:
    """Helper: send wire bytes through a real socketpair, decode on the other end."""
    a, b = socket.socketpair()
    try:
        a.sendall(wire)
        a.close()
        return decode_message(b)
    finally:
        b.close()


class TestEncodeMessage:
    def test_basic_string(self):
        wire = encode_message("Hello")
        assert len(wire) > 4  # length prefix + payload

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            encode_message("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            encode_message("   ")

    def test_oversized_message_raises(self):
        with pytest.raises(MessageTooLargeError):
            encode_message("A" * 5000)

    def test_unicode_message(self):
        msg = "नमस्ते 🔐"
        wire = encode_message(msg)
        assert len(wire) > 4


class TestDecodeMessage:
    def test_roundtrip_ascii(self):
        wire = encode_message("Hello, world!")
        result = _socketpair_roundtrip(wire)
        assert result == "Hello, world!"

    def test_roundtrip_unicode(self):
        msg = "Héllo Wörld — 안녕하세요"
        wire = encode_message(msg)
        result = _socketpair_roundtrip(wire)
        assert result == msg

    def test_malformed_json_raises(self):
        import struct
        garbage = b"not json at all"
        wire = struct.pack(">I", len(garbage)) + garbage
        a, b = socket.socketpair()
        a.sendall(wire)
        a.close()
        with pytest.raises(InvalidMessageError):
            decode_message(b)
        b.close()

    def test_zero_length_raises(self):
        import struct
        wire = struct.pack(">I", 0)
        a, b = socket.socketpair()
        a.sendall(wire)
        a.close()
        with pytest.raises(InvalidMessageError):
            decode_message(b)
        b.close()

    def test_empty_connection_raises(self):
        a, b = socket.socketpair()
        a.close()  # Close write end immediately
        with pytest.raises(InvalidMessageError):
            decode_message(b)
        b.close()
