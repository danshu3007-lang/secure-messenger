# secure-messenger

A **stateless, TLS-secured, terminal-based messenger** for Linux.  
No accounts. No servers. No databases. No message storage.  
One command to send, one to receive — everything else is discarded.

```
messenger-send 192.168.1.5 "Deploy ready"
```

---

## Security model

| Property | How |
|---|---|
| Confidentiality | TLS 1.3 (AES-256-GCM / ChaCha20-Poly1305) |
| Integrity | TLS + optional AES-256-GCM E2E layer |
| Authentication | Server cert verified against CA; optional mTLS |
| No storage | Messages are printed once to stdout, then discarded |
| No logging | Only connection metadata (IP, port) is printed |
| Forward secrecy | TLS 1.3 ephemeral key exchange |

**What is NOT protected:** source/destination IPs, connection timing, packet sizes.  
This tool is suitable for LAN / closed networks. It is not anonymous.

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

Or from a private apt repository:

```bash
echo "deb [trusted=yes] https://your.repo.example.com/apt stable main" \
  | sudo tee /etc/apt/sources.list.d/messenger.list
sudo apt update && sudo apt install messenger
```

### From source (development)

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
messenger-receive              # Listen on default port 8443
messenger-receive 9000         # Custom port
messenger-receive --local      # 127.0.0.1 only
messenger-receive --mtls       # Require client certificates (mTLS)
messenger-receive --e2e        # Expect AES-256-GCM encrypted payload
```

### 3. Send a message

```bash
messenger-send 192.168.1.5 "Hello, secure world!"
messenger-send 192.168.1.5 "Secret" --port 9000
messenger-send 192.168.1.5 "E2E message" --e2e
```

---

## End-to-end encryption (optional layer on top of TLS)

E2E adds AES-256-GCM encryption **inside** the TLS channel.  
Even if TLS were broken, the payload stays opaque.

**Both sides must share the same 32-byte key.**

```bash
# On one machine: generate the key
messenger-keygen
# Key written to /etc/messenger/certs/e2e.key

# Copy it to the other machine OUT-OF-BAND (never over the network)
scp /etc/messenger/certs/e2e.key user@receiver-host:/etc/messenger/certs/e2e.key

# Send with E2E:
messenger-send 192.168.1.5 "Ultra secret" --e2e

# Receive with E2E:
messenger-receive --e2e
```

---

## Mutual TLS (mTLS)

In mTLS mode the server verifies the client's certificate too.  
Only clients with a cert signed by your CA can connect.

```bash
# Generate a client cert (signed by same CA):
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

# Start receiver in mTLS mode:
messenger-receive --mtls

# Sender automatically presents its cert if present in MESSENGER_CERT_DIR
```

---

## Run as a systemd service

```bash
sudo cp systemd/messenger-receive.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now messenger-receive

# View logs (metadata only — not message content if you redirect stdout)
sudo journalctl -u messenger-receive -f
```

> **Note:** When running as a systemd service, messages printed to stdout
> appear in journald. For zero-trace operation, run the receiver
> interactively in a terminal session instead.

---

## Running tests

```bash
# Install dev dependencies
pip install pytest cryptography

# Generate test certs (once)
bash tests/certs/gen_test_certs.sh

# Run all tests
MESSENGER_CERT_DIR=tests/certs pytest tests/ -v

# Unit tests only (no certs needed)
pytest tests/unit/ -v

# Integration tests
MESSENGER_CERT_DIR=tests/certs pytest tests/integration/ -v
```

---

## Building the .deb package

```bash
# Install build tools
sudo apt install python3-pip python3-build ruby ruby-dev rubygems -y
sudo gem install fpm

# Build
bash scripts/build_deb.sh

# Install
sudo apt install ./dist/messenger_1.0.0_amd64.deb
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
│   │   └── e2e.py            # AES-256-GCM + HKDF key derivation
│   ├── sender/
│   │   ├── cli.py            # messenger-send entry point
│   │   ├── connection.py     # Connect → send → close
│   │   └── tls_client.py     # TLS 1.3 client context + IP SAN verification
│   └── receiver/
│       ├── cli.py            # messenger-receive entry point
│       ├── server.py         # Accept loop → print → discard
│       └── tls_server.py     # TLS 1.3 server context + optional mTLS
├── certs/
│   ├── gen_certs.sh          # Production cert generation
│   └── README.md             # PKI & cert management guide
├── systemd/
│   └── messenger-receive.service
├── scripts/
│   ├── build_deb.sh          # Build the .deb package
│   └── postinstall.sh        # Runs after apt install
├── tests/
│   ├── certs/
│   │   └── gen_test_certs.sh # Generate test certs for 127.0.0.1
│   ├── unit/
│   │   ├── test_serializer.py
│   │   └── test_e2e_crypto.py
│   └── integration/
│       └── test_end_to_end.py
└── pyproject.toml
```

---

## Limitations & roadmap

| Limitation | Workaround / Future |
|---|---|
| Direct IP only — fails behind NAT | Add a relay server or STUN/TURN |
| Source IP visible to network observers | Route through Tor (future) |
| No message routing / addressing | Add a DHT mesh layer (future) |
| Pre-shared key exchange is manual | Replace with ECDH over TLS (future) |

---

## License

MIT — see `LICENSE` for details.
