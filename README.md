# 🔐 secure-messenger

> A stateless, TLS 1.3 encrypted, terminal-based messenger for Linux.
> No accounts. No servers. No databases. No message history. Just secure communication.

```
chat 192.168.1.5        ← two-way live chat
snd  192.168.1.5 "hi"  ← send one message
rcv                     ← listen for messages
```

---

## What is this?

secure-messenger lets two people on the same network send encrypted messages
through their terminal. Every message is protected by TLS 1.3 (the same
encryption your bank uses). Nothing is ever saved to disk.

**Think of it like a walkie-talkie — but encrypted and running in your terminal.**

---

## Requirements

- Linux (Arch, Ubuntu, Debian, etc.)
- Python 3.11 or newer
- OpenSSL (already installed on most Linux systems)

---

## Installation

### Step 1 — Clone the repo

```bash
git clone https://github.com/danshu3007-lang/secure-messenger
cd secure-messenger
```

### Step 2 — Create a virtual environment and install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

> Note: Use `pip install .` not `pip install -e .`
> Editable installs have a known bug with Python 3.14 + setuptools.

### Step 3 — Generate test certificates

```bash
bash tests/certs/gen_test_certs.sh
```

### Step 4 — Verify it works

```bash
snd --help
rcv --help
chat --help
```

---

## Quick Start — Test on your own machine (2 terminals)

**Terminal 1:**
```bash
source .venv/bin/activate
MESSENGER_CERT_DIR=tests/certs chat 127.0.0.1 -lp 8443 -pp 8444
```

**Terminal 2:**
```bash
source .venv/bin/activate
MESSENGER_CERT_DIR=tests/certs chat 127.0.0.1 -lp 8444 -pp 8443
```

Type in either terminal and press Enter. Messages appear on the other side instantly.

---

## Commands

### `chat` — Two-way live chat *(new in v2)*

Both people can send and receive at the same time.

```bash
# Two machines on same network:
# Machine A:
chat 192.168.1.10

# Machine B:
chat 192.168.1.5

# Same machine, two terminals (testing):
# Terminal 1:
chat 127.0.0.1 -lp 8443 -pp 8444
# Terminal 2:
chat 127.0.0.1 -lp 8444 -pp 8443

# With extra E2E encryption:
chat 192.168.1.10 --e2e
```

| Flag | Default | Meaning |
|---|---|---|
| `-lp PORT` | 8444 | Port YOU listen on |
| `-pp PORT` | 8443 | Port your PEER listens on |
| `--e2e` | off | AES-256-GCM extra encryption |

---

### `snd` — Send one message

```bash
snd 192.168.1.5 "hello"
snd 192.168.1.5 "hello" -p 9000
snd 192.168.1.5 "hello" --e2e
```

---

### `rcv` — Listen for messages

```bash
rcv                # listen on port 8443
rcv 9000           # custom port
rcv --e2e          # expect encrypted messages
rcv --local        # localhost only
rcv --mtls         # require client certificates
```

---

### `messenger-keygen` — Generate E2E key

```bash
messenger-keygen
# Copy the key file to the other machine via USB/QR — never over the network
```

---

## Using on a real LAN

**Receiver machine:**
```bash
sudo bash certs/gen_certs.sh /etc/messenger/certs 192.168.1.5
scp /etc/messenger/certs/ca.crt user@192.168.1.10:/etc/messenger/certs/ca.crt
rcv
```

**Sender machine:**
```bash
snd 192.168.1.5 "Hello!"
# or two-way:
chat 192.168.1.5
```

---

## Running tests

```bash
bash tests/certs/gen_test_certs.sh
MESSENGER_CERT_DIR=tests/certs pytest tests/unit/ -v
# Expected: 23 passed
```

---

## Project structure

```
secure-messenger/
├── messenger/
│   ├── common/       ← shared code: constants, exceptions, wire format
│   ├── crypto/       ← AES-256-GCM end-to-end encryption
│   ├── sender/       ← messenger-send / snd
│   ├── receiver/     ← messenger-receive / rcv
│   ├── shortcuts/    ← short aliases: snd, rcv
│   └── chat/         ← two-way live chat
├── certs/            ← certificate generation scripts
├── systemd/          ← background service unit file
├── scripts/          ← build and packaging scripts
├── tests/            ← unit + integration tests
├── docs/             ← full project documentation
└── pyproject.toml    ← package definition
```

---

## Security model

| Property | How |
|---|---|
| Confidentiality | TLS 1.3 — AES-256-GCM or ChaCha20 |
| Integrity | GCM authentication tag — any tampering detected |
| Forward secrecy | TLS 1.3 ephemeral key exchange |
| No storage | Messages printed once, never saved |
| Optional E2E | AES-256-GCM second layer on top of TLS |
| No weak ciphers | SSLv2/3, TLS 1.0/1.1 all disabled |

**Not protected:** IP addresses, connection timing, packet sizes.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `command not found` | Run `source .venv/bin/activate` |
| `Connection refused` | Start the receiver BEFORE sending |
| `Certificate error` | Copy `ca.crt` from receiver to sender |
| `pip install -e .` fails | Use `pip install .` (no `-e` flag) |

---

## License

MIT

---

## Version history

| Version | Changes |
|---|---|
| v2.0.0 | Two-way `chat` command, short aliases `snd`/`rcv`, Python 3.14 fix |
| v1.0.0 | Initial release: TLS 1.3, E2E crypto, `messenger-send`/`messenger-receive` |
