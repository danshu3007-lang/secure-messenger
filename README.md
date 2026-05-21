# secure-messenger

A **stateless, TLS-secured, terminal-based messenger** for Linux.  
No accounts. No servers. No databases. No message storage.  
One command to send, one to receive.

```bash
messenger-send 192.168.1.5 "Deploy ready"
```

---

## What this tool actually is

This is a **point-to-point terminal messaging utility** secured by TLS 1.3.
It is designed for LAN / closed-network use: DevOps alerts, admin notifications,
and private LAN communication where you control both endpoints.

It is **not** Signal, WhatsApp, or a general-purpose secure messenger.
It does not implement the Signal Protocol, Double Ratchet, or X3DH.
Those are the right tools for untrusted multi-party public internet messaging.
This tool is the right tool for direct, controlled, infrastructure-level messaging.

---

## Security model — honest breakdown

| Property | Status | How |
|---|---|---|
| Transport confidentiality | ✅ Real | TLS 1.3 with AES-256-GCM or ChaCha20-Poly1305 |
| Transport integrity | ✅ Real | TLS AEAD — any tampering breaks the connection |
| Transport authentication | ✅ Real | Server cert verified against your own CA |
| Client authentication | ✅ Optional | Mutual TLS (`--mtls`) — server rejects unknown clients |
| Payload encryption (E2E layer) | ✅ Real | AES-256-GCM with per-message HKDF-derived keys |
| Message authentication | ✅ Real | GCM tag — bit-flip in ciphertext causes decryption failure |
| No message storage | ✅ Real | Messages printed once to terminal, then discarded |
| No message content in logs | ✅ Real (with `--quiet`) | Use `--quiet` flag when running as a systemd service |
| Forward secrecy (TLS layer) | ✅ Real | TLS 1.3 ephemeral key exchange |
| Forward secrecy (E2E layer) | ❌ Not implemented | PSK is static; compromise of key decrypts all recorded traffic |
| Identity verification | ⚠️ Manual | Cert fingerprint must be verified out-of-band |
| Anonymity | ❌ Not provided | Source/destination IPs are visible on the network |
| Metadata protection | ❌ Not provided | Connection timing and packet sizes are visible |
| Signal-level E2E | ❌ Not claimed | No Double Ratchet, no X3DH, no ratcheting forward secrecy |

### The E2E encryption layer — what it does and does not do

When you use `--e2e`, messages are encrypted with **AES-256-GCM** inside the
TLS channel. This gives you a second layer of encryption: even if TLS were
somehow broken, the payload stays encrypted.

The key model is **Pre-Shared Key (PSK)**. Both endpoints share a 32-byte
secret that you copy out-of-band (in person, via QR code, or secure file copy).
The PSK is never transmitted over the network.

Each message uses a **unique per-message key** derived from the PSK and a
fresh random nonce via HKDF-SHA256. This means:
- Two identical messages produce completely different ciphertext.
- Knowing one derived key does not reveal the PSK or other derived keys.

**Known limitation:** If an attacker obtains the PSK file, they can decrypt all
recorded traffic. This is a fundamental property of symmetric PSK systems.
The roadmap item is to replace PSK with ECDH ephemeral key agreement, which
would provide session-level forward secrecy.

---

## Requirements

- Linux (Ubuntu 22.04+ / Debian 12+)
- Python 3.11+
- OpenSSL (for cert generation)

---

## Installation

### From .deb package (recommended)

```bash
sudo apt install ./messenger_1.0.0_amd64.deb
```

### From source

```bash
git clone https://github.com/yourorg/secure-messenger
cd secure-messenger
pip install -e ".[dev]"

# Generate test certs
bash tests/certs/gen_test_certs.sh
```

---

## Quick start

### 1. Generate certificates (first time only)

On the **receiver machine**:

```bash
sudo bash certs/gen_certs.sh /etc/messenger/certs 192.168.1.5
```

Copy `ca.crt` to all sender machines:

```bash
scp /etc/messenger/certs/ca.crt user@sender-host:/etc/messenger/certs/ca.crt
```

### 2. Start the receiver

```bash
messenger-receive                    # TLS only, default port 8443
messenger-receive 9000               # Custom port
messenger-receive --local            # 127.0.0.1 only
messenger-receive --mtls             # Require client certificates
messenger-receive --e2e              # Expect AES-256-GCM encrypted payload
messenger-receive --e2e --quiet      # E2E + suppress display (safe for systemd)
```

### 3. Send a message

```bash
messenger-send 192.168.1.5 "Hello"
messenger-send 192.168.1.5 "Secret" --port 9000
messenger-send 192.168.1.5 "E2E message" --e2e
```

---

## End-to-end encryption (optional, on top of TLS)

E2E adds AES-256-GCM encryption **inside** the TLS channel.

```bash
# Generate a shared key on one machine
messenger-keygen
# Output: /etc/messenger/certs/e2e.key

# Copy to the other machine OUT-OF-BAND — never over the network
scp /etc/messenger/certs/e2e.key user@receiver:/etc/messenger/certs/e2e.key

# Send with E2E
messenger-send 192.168.1.5 "Ultra secret" --e2e

# Receive with E2E
messenger-receive --e2e
```

---

## Mutual TLS (mTLS)

mTLS means the server verifies the client's certificate too.
Only clients with a cert signed by your CA can connect.

```bash
# Generate a client cert (signed by your CA)
openssl genrsa -out /etc/messenger/certs/client.key 4096
openssl req -new -key /etc/messenger/certs/client.key \
    -out /etc/messenger/certs/client.csr \
    -subj "/CN=messenger-client/O=SecureMessenger/C=IN"
openssl x509 -req -days 365 \
    -in /etc/messenger/certs/client.csr \
    -CA /etc/messenger/certs/ca.crt \
    -CAkey /etc/messenger/certs/ca.key \
    -CAcreateserial \
    -out /etc/messenger/certs/client.crt

# Start receiver in mTLS mode
messenger-receive --mtls

# Sender presents its cert automatically if present in MESSENGER_CERT_DIR
```

---

## Running as a systemd service

```bash
sudo cp systemd/messenger-receive.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now messenger-receive

# View logs (metadata only — no message content)
sudo journalctl -u messenger-receive -f
```

The service file uses `--quiet` by default. In quiet mode:
- Connection metadata (IP, port, connect/disconnect) goes to journald.
- Message content is **never printed** and never enters journald.

If you remove `--quiet` and run with `StandardOutput=journal`, message content
**will** appear in journald. The `--quiet` flag exists precisely to prevent this.

For fully ephemeral operation with zero metadata: run interactively in a
terminal session, not as a service.

---

## Logging behaviour — explicit table

| Run mode | What reaches journald |
|---|---|
| systemd service, `--quiet` (default) | Connection metadata only. No message content. |
| systemd service, no `--quiet` | Connection metadata AND message content. |
| Interactive terminal | Nothing (terminal output is not persisted). |

---

## Running tests

```bash
pip install pytest cryptography
bash tests/certs/gen_test_certs.sh
MESSENGER_CERT_DIR=tests/certs pytest tests/ -v
```

---

## Project structure

```
secure-messenger/
├── messenger/
│   ├── common/
│   │   ├── constants.py      # Ports, limits, cipher list, cert paths
│   │   ├── exceptions.py     # Custom error types
│   │   └── serializer.py     # JSON + 4-byte length-prefix wire format
│   ├── crypto/
│   │   └── e2e.py            # AES-256-GCM + per-message HKDF key derivation
│   ├── sender/
│   │   ├── cli.py            # messenger-send entry point
│   │   ├── connection.py     # Connect → encrypt → send → close
│   │   └── tls_client.py     # TLS 1.3 + IP SAN verification
│   └── receiver/
│       ├── cli.py            # messenger-receive entry point (--quiet flag)
│       ├── server.py         # Accept loop → display → discard
│       └── tls_server.py     # TLS 1.3 server context + optional mTLS
├── certs/
│   ├── gen_certs.sh          # Production cert generation
│   └── README.md             # PKI & cert management guide
├── systemd/
│   └── messenger-receive.service   # Uses --quiet by default
├── scripts/
│   ├── build_deb.sh
│   └── postinstall.sh
├── tests/
│   ├── certs/gen_test_certs.sh
│   ├── unit/
│   │   ├── test_serializer.py
│   │   └── test_e2e_crypto.py
│   └── integration/
│       └── test_end_to_end.py
└── pyproject.toml
```

---

## Known limitations and roadmap

| Limitation | Impact | Roadmap |
|---|---|---|
| PSK-based E2E — no session forward secrecy | PSK compromise decrypts all recorded traffic | Replace with ECDH ephemeral key exchange |
| Direct IP only — fails behind NAT | LAN use only | Relay server or STUN/TURN |
| Source/destination IPs visible | Network observer sees who talks to whom | Route through Tor (future) |
| No message routing or addressing | One sender, one receiver | DHT mesh layer (future) |
| No replay protection in E2E layer | Captured ciphertext could be resent | Add sequence numbers or nonce log |
| Self-signed CA | Trust must be established manually | Optional: integrate with a real CA |

---

## Security questions answered directly

**Is this end-to-end encrypted?**  
When using `--e2e`: yes, with AES-256-GCM and per-message derived keys. The TLS
layer also provides encryption and authentication independently.

**Can the operator read messages?**  
By default (without `--quiet`): yes, messages print to the terminal of whoever
runs the receiver. With `--quiet`: no content is displayed or logged anywhere.
This tool is designed for use cases where the person running the receiver IS the
intended recipient.

**Does this have forward secrecy?**  
At the TLS layer: yes (TLS 1.3 ephemeral key exchange). At the E2E layer: no.
If the PSK is compromised, past recorded traffic can be decrypted.

**Is this Signal-level security?**  
No. Signal uses the Double Ratchet protocol with X3DH key agreement. That
provides post-compromise security, strong forward secrecy, and deniable
authentication. This tool provides transport security and authenticated
symmetric encryption. Those are different things, and this project does not
claim otherwise.

**Should I use this for sensitive communications over the public internet?**  
No. This tool is designed for LAN / closed-network use between trusted machines
where you control both endpoints. For public internet use between parties who
don't share infrastructure, use Signal.

---

## License

MIT — see `LICENSE` for details.
