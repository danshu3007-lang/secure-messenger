# Security Architecture & Threat Model

This document explains exactly how `secure-messenger` works cryptographically,
what it protects against, and what it does not protect against.
Nothing is hidden. Every claim below maps directly to source code you can read.

---

## What this tool is

`secure-messenger` is a **point-to-point, LAN-oriented, TLS-secured terminal
messaging utility** with an optional AES-256-GCM payload encryption layer.

It is designed for:
- DevOps alerts between machines you control
- Admin notifications on a closed network
- Situations where both endpoints are trusted and managed by the same operator

It is **not** designed for:
- Anonymous communication
- Public internet messaging between strangers
- Replacing Signal, SimpleX, or Threema

---

## Cryptographic stack — line by line

### Transport layer (always active)

| Property | Implementation | Source file |
|---|---|---|
| Protocol | TLS 1.3 only — 1.2 and below rejected | `tls_server.py`, `tls_client.py` |
| Ciphers | AES-256-GCM, ChaCha20-Poly1305 (AEAD only) | `constants.py` → `TLS12_CIPHERS` |
| Compression | Disabled (`OP_NO_COMPRESSION`) | `tls_server.py` line 35 |
| Legacy versions | SSLv2, SSLv3, TLS 1.0, TLS 1.1 all blocked | `tls_server.py` lines 30–34 |
| Server auth | Server cert verified against our own CA | `tls_client.py` → `CERT_REQUIRED` |
| IP SAN check | Manual IP SAN verification for raw IP targets | `tls_client.py` → `_verify_ip_in_san()` |
| Forward secrecy | TLS 1.3 ephemeral key exchange (built-in) | TLS 1.3 spec — no static key used |
| CRIME attack | Compression disabled — CRIME impossible | `OP_NO_COMPRESSION` |

### E2E payload layer (optional — `--e2e` flag)

| Property | Implementation | Source file |
|---|---|---|
| Cipher | AES-256-GCM (AEAD) | `e2e.py` → `AESGCM(key)` |
| Nonce | 96-bit random per message (`os.urandom(12)`) | `e2e.py` → `encrypt_message()` |
| Key derivation | HKDF-SHA256(PSK, salt=nonce, info=context) | `e2e.py` → `derive_message_key()` |
| Key diversity | Every message uses a different derived key | nonce-as-salt in HKDF |
| Authentication | GCM tag — any tampering causes decryption failure | `e2e.py` → `InvalidTag` handler |
| Key storage | File, chmod 600, never transmitted over network | `e2e.py` → `generate_psk()` |
| Key size | 256 bits (32 bytes), enforced strictly | `e2e.py` → `load_psk()` |
| Wire format | `[12-byte nonce][ciphertext+16-byte GCM tag]` | `e2e.py` → encrypt/decrypt |

### Wire protocol

| Property | Implementation | Source file |
|---|---|---|
| Framing | 4-byte big-endian length prefix + JSON | `serializer.py` |
| Max message | 4096 bytes hard cap | `constants.py` → `MAX_MESSAGE_BYTES` |
| Read-forever attack | Prevented by length cap | `serializer.py` → `decode_message()` |
| Encoding | UTF-8 throughout | `serializer.py` |

---

## Threat model

### Threats we defend against

**1. Network eavesdropping**
An attacker capturing packets on the network sees only TLS ciphertext.
With `--e2e`, the payload is also AES-256-GCM encrypted inside TLS.
Breaking this requires breaking TLS 1.3 — no known practical attack exists.

**2. Message tampering**
AES-GCM's authentication tag detects any modification to the ciphertext.
A flipped bit causes decryption to fail and raises `E2EKeyError`.
This is proven in `tests/unit/test_e2e_crypto.py → test_bit_flip_in_ciphertext_raises`.

**3. Impersonation (server)**
The client verifies the server certificate against a CA you control.
An attacker cannot present a fake certificate without your CA private key.
For raw IP connections, we manually verify the IP appears in the cert's SAN field.

**4. Impersonation (client)**
With `--mtls`, the server rejects any client that does not present a certificate
signed by your CA. Strangers cannot connect even if they know the IP and port.

**5. Weak cipher downgrade**
Only TLS 1.3 is accepted. TLS 1.2 and below are blocked at the socket level.
If a client offers only TLS 1.2, the connection is rejected before any data flows.

**6. CRIME attack**
TLS compression is disabled. CRIME requires compression — impossible here.

**7. Oversized message / read-forever attack**
The wire protocol uses a 4-byte length prefix. Messages above 4096 bytes are
rejected before reading. A malformed or infinite stream cannot exhaust memory.

**8. Daemon privilege escalation**
The systemd service runs as a dedicated unprivileged `messenger` user with:
`NoNewPrivileges`, `ProtectSystem=strict`, `MemoryDenyWriteExecute`,
`PrivateTmp`, `RestrictNamespaces`, `SystemCallFilter=@system-service`.
A compromised process cannot escalate to root or access other users' data.

**9. Message content in system logs**
The `--quiet` flag (default in the systemd service) prevents message content
from ever being printed to stdout, ensuring journald never receives it.

---

### Threats we do NOT defend against — stated honestly

**1. PSK compromise → past traffic decryptable**
The E2E layer uses a Pre-Shared Key. If an attacker steals the PSK file,
they can decrypt all previously recorded traffic.
This is a known, documented limitation of symmetric PSK systems.
*Roadmap: replace with ECDH ephemeral key exchange for session-level forward secrecy.*

**2. Endpoint compromise**
If an attacker has root on either machine, they can read messages as they are
displayed. No messenger — including Signal — protects against full endpoint
compromise. This is outside scope by design.

**3. Network metadata / traffic analysis**
Source IP, destination IP, connection timing, and approximate message size are
visible to a network observer. This tool makes no anonymity claims.
*For anonymity: route through Tor.*

**4. Replay attacks on the E2E layer**
AES-GCM nonces are random and not tracked in a seen-nonce database.
A captured ciphertext packet could be replayed.
*Roadmap: add sequence numbers or a nonce log.*

**5. Multi-party messaging**
This tool is point-to-point. There is no group messaging, routing, or relay.

**6. Key rotation**
There is no automated PSK rotation. Rotation is manual.

---

## What the code does NOT do — clearing up common "fake security" checklist items

The reviewer raised a generic checklist. Here is how each point maps to this codebase:

| Claim | Reality in this code |
|---|---|
| "Server sees plaintext" | With `--e2e`: server receives hex-encoded AES-GCM ciphertext. Plaintext only exists after local decryption. Without `--e2e`: TLS only — the receiver IS the intended recipient by design. |
| "Hardcoded keys" | Zero hardcoded keys. PSK is generated by `messenger-keygen` using `os.urandom(32)`. |
| "Static IV / nonce reuse" | Nonce is `os.urandom(12)` per message. Reuse probability is astronomically low (birthday bound at ~2^48 messages). |
| "AES ECB mode" | AES-GCM mode only. ECB is not used anywhere. |
| "Homemade crypto" | No custom cryptography. Uses Python `cryptography` library (pyca/cryptography) — the standard audited library. |
| "No authentication" | AES-GCM is authenticated encryption. Every message has a 16-byte GCM tag. Tampered messages are rejected. |
| "JWT misuse" | No JWT anywhere in this codebase. |
| "Plaintext server-side" | Receiver IS the endpoint. Operator reads their own messages. This is not a relay architecture. |
| "No certificate validation" | `CERT_REQUIRED` + IP SAN verification in `tls_client.py`. |
| "No key pinning" | The CA is your own self-generated CA. You pin by controlling the CA entirely. |
| "Manual crypto implementation" | Zero manual crypto. HKDF and AESGCM come from pyca/cryptography. |

---

## Libraries used

| Library | Version | Purpose | Audit status |
|---|---|---|---|
| `cryptography` (pyca) | ≥41.0 | AES-GCM, HKDF, TLS | Widely audited, used by pip, AWS, Mozilla |
| Python `ssl` module | stdlib | TLS 1.3 socket layer | Wraps OpenSSL |
| OpenSSL | system | Underlying TLS | Continuously audited |

No custom cryptographic primitives are implemented.

---

## Scope statement

This tool is suitable for:
- Trusted LAN environments
- Operator-to-operator messaging where both ends are controlled by the same person or team
- Infrastructure alerting and admin notifications

This tool is not suitable for:
- Communicating with untrusted parties over the public internet
- Anonymity-required use cases
- Regulated data (HIPAA, GDPR sensitive data) without additional controls
- Replacing a purpose-built secure messenger for consumer use

---

## Reporting security issues

If you find a real vulnerability, please open a GitHub issue marked `[SECURITY]`
or email the maintainer directly. We will respond within 48 hours.
