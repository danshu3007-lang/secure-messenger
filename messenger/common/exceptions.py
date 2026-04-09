# messenger/common/exceptions.py


class MessengerError(Exception):
    """Base error — all messenger errors inherit from this."""


class TLSHandshakeError(MessengerError):
    """TLS handshake failed: bad cert, expired, or wrong CA."""


class ConnectionRefusedError(MessengerError):
    """No receiver is listening at the target."""


class MessageTooLargeError(MessengerError):
    """Message exceeds MAX_MESSAGE_BYTES."""


class InvalidMessageError(MessengerError):
    """Malformed or non-JSON message received."""


class CertificateError(MessengerError):
    """Certificate validation failed."""


class E2EKeyError(MessengerError):
    """E2E key missing, wrong size, or decryption failed."""
