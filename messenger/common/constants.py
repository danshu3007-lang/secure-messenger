# messenger/common/constants.py

DEFAULT_PORT = 8443
MAX_MESSAGE_BYTES = 4096       # Hard cap: 4 KB
RECV_TIMEOUT_SECONDS = 10
CONNECT_TIMEOUT_SECONDS = 5

# TLS 1.2 fallback ciphers (AEAD only — no CBC, no RC4, no NULL)
TLS12_CIPHERS = (
    "ECDHE-ECDSA-AES256-GCM-SHA384:"
    "ECDHE-RSA-AES256-GCM-SHA384:"
    "ECDHE-ECDSA-CHACHA20-POLY1305:"
    "ECDHE-RSA-CHACHA20-POLY1305"
)

# Cert paths — overridable via environment variable
import os

CERT_BASE   = os.environ.get("MESSENGER_CERT_DIR", "/etc/messenger/certs")
CA_CERT     = os.path.join(CERT_BASE, "ca.crt")
SERVER_CERT = os.path.join(CERT_BASE, "server.crt")
SERVER_KEY  = os.path.join(CERT_BASE, "server.key")
E2E_KEY     = os.path.join(CERT_BASE, "e2e.key")
