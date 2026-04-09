<div align="center">

<img src="https://img.shields.io/badge/TLS-1.3-00d4aa?style=flat-square&logo=lock&logoColor=white" alt="TLS 1.3"/>
<img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/License-MIT-f59e0b?style=flat-square" alt="MIT"/>
<img src="https://img.shields.io/badge/Platform-Linux-FCC624?style=flat-square&logo=linux&logoColor=black" alt="Linux"/>
<img src="https://img.shields.io/badge/Tests-23%20passing-22c55e?style=flat-square" alt="Tests"/>

<br/><br/>

```
 ___  ___  ___  ___  ___  ___  ___     ___  ___  ___  ___  ___  ___  ___  ___ 
███████╗███████╗ ██████╗██╗   ██╗██████╗ ███████╗
██╔════╝██╔════╝██╔════╝██║   ██║██╔══██╗██╔════╝
███████╗█████╗  ██║     ██║   ██║██████╔╝█████╗  
╚════██║██╔══╝  ██║     ██║   ██║██╔══██╗██╔══╝  
███████║███████╗╚██████╗╚██████╔╝██║  ██║███████╗
╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝
███╗   ███╗███████╗███████╗███████╗███████╗███╗   ██╗ ██████╗ ███████╗██████╗ 
████╗ ████║██╔════╝██╔════╝██╔════╝██╔════╝████╗  ██║██╔════╝ ██╔════╝██╔══██╗
██╔████╔██║█████╗  ███████╗███████╗█████╗  ██╔██╗ ██║██║  ███╗█████╗  ██████╔╝
██║╚██╔╝██║██╔══╝  ╚════██║╚════██║██╔══╝  ██║╚██╗██║██║   ██║██╔══╝  ██╔══██╗
██║ ╚═╝ ██║███████╗███████║███████║███████╗██║ ╚████║╚██████╔╝███████╗██║  ██║
╚═╝     ╚═╝╚══════╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
```

# 🔐 secure-messenger

**A stateless, TLS 1.3 encrypted terminal messenger for Linux.**  
No accounts. No servers. No databases. No history. Just encryption.

[**Quick Start**](#quick-start) · [**Commands**](#commands) · [**Security Model**](#security-model) · [**Docs**](docs/)

</div>

---

## What is this?

`secure-messenger` lets two people on the same network exchange encrypted messages directly from their terminal. Every message is wrapped in **TLS 1.3** — the same protocol your bank uses — and nothing is ever written to disk.

> 💡 **Think of it like a walkie-talkie, but encrypted and running in your terminal.**

```bash
chat 192.168.1.5        # two-way live chat
snd  192.168.1.5 "hi"  # fire-and-forget one message
rcv                     # listen for incoming messages
```

---

## Why does this exist?

Sometimes you need to send a message across a LAN without cloud services, accounts, logs, or third-party servers. This tool gives you encrypted communication that lives entirely on your machines and disappears when you close the terminal.

**Perfect for:** sysadmins, security researchers, privacy-conscious users, CTF players, or anyone on an air-gapped or semi-trusted network.

---

## Features

- 🔒 **TLS 1.3** — AES-256-GCM or ChaCha20 transport encryption
- 🛡️ **Optional E2E layer** — AES-256-GCM on top of TLS for double encryption
- 💬 **Two-way chat** — full-duplex live chat with `chat`
- 📨 **Fire-and-forget** — send a single message with `snd`
- 👂 **Listener mode** — wait for messages with `rcv`
- 🔑 **mTLS support** — mutual TLS client authentication
- 🚫 **Zero persistence** — nothing written to disk, ever
- 🐧 **Linux native** — systemd service unit included
- ✅ **23 unit tests** — reliable and tested

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.11 or newer |
| OpenSSL | Any modern version (pre-installed on most Linux) |
| OS | Linux (Arch, Ubuntu, Debian, etc.) |

---

## Quick Start

### 1 — Clone

```bash
git clone https://github.com/danshu3007-lang/secure-messenger
cd secure-messenger
```

### 2 — Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

> ⚠️ Use `pip install .` — not `pip install -e .`  
> Editable installs have a known bug with Python 3.14 + setuptools.

### 3 — Generate test certificates

```bash
bash tests/certs/gen_test_certs.sh
```

### 4 — Verify

```bash
snd --help
rcv --help
chat --help
```

---

## Test it locally (2 terminals)

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

Type in either terminal and press Enter. Messages appear on the other side instantly. Press `Ctrl+C` to quit.

---

## Commands

### `chat` — Two-way live chat

```bash
# Two machines on the same network
# Machine A:
chat 192.168.1.10

# Machine B:
chat 192.168.1.5

# Same machine, two terminals (for testing)
chat 127.0.0.1 -lp 8443 -pp 8444   # Terminal 1
chat 127.0.0.1 -lp 8444 -pp 8443   # Terminal 2

# With extra E2E encryption
chat 192.168.1.10 --e2e
```

| Flag | Default | Description |
|---|---|---|
| `-lp PORT` | 8444 | Port you listen on |
| `-pp PORT` | 8443 | Port your peer listens on |
| `--e2e` | off | Enable AES-256-GCM second layer |

---

### `snd` — Send one message

```bash
snd 192.168.1.5 "hello"
snd 192.168.1.5 "hello" -p 9000   # custom port
snd 192.168.1.5 "hello" --e2e     # E2E encrypted
```

---

### `rcv` — Listen for messages

```bash
rcv                  # port 8443
rcv 9000             # custom port
rcv --e2e            # expect E2E encrypted messages
rcv --local          # localhost only
rcv --mtls           # require client certificates
```

---

### `messenger-keygen` — Generate an E2E key

```bash
messenger-keygen
```

> 🔑 Copy the key file to the other machine via USB or QR code. **Never send it over the network.**

---

## Real LAN Usage

**On the receiver machine:**
```bash
sudo bash certs/gen_certs.sh /etc/messenger/certs 192.168.1.5
scp /etc/messenger/certs/ca.crt user@192.168.1.10:/etc/messenger/certs/ca.crt
rcv
```

**On the sender machine:**
```bash
snd 192.168.1.5 "Hello!"
# or start two-way chat:
chat 192.168.1.5
```

---

## Security Model

| Property | Implementation |
|---|---|
| **Confidentiality** | TLS 1.3 — AES-256-GCM or ChaCha20 |
| **Integrity** | GCM authentication tag — tampering is detected |
| **Forward secrecy** | TLS 1.3 ephemeral key exchange |
| **No storage** | Messages printed once, never saved |
| **Optional E2E** | AES-256-GCM second layer on top of TLS |
| **No weak ciphers** | SSLv2/3, TLS 1.0/1.1 disabled |

**What this does NOT protect:** IP addresses, connection timing, or packet sizes. Use a VPN or Tor if metadata privacy is also required.

---

## Running Tests

```bash
bash tests/certs/gen_test_certs.sh
MESSENGER_CERT_DIR=tests/certs pytest tests/unit/ -v
# Expected: 23 passed
```

---

## Project Structure

```
secure-messenger/
├── messenger/
│   ├── common/       # shared constants, exceptions, wire format
│   ├── crypto/       # AES-256-GCM end-to-end encryption
│   ├── sender/       # snd command
│   ├── receiver/     # rcv command
│   ├── shortcuts/    # short command aliases
│   └── chat/         # two-way live chat
├── certs/            # certificate generation scripts
├── systemd/          # background service unit file
├── scripts/          # build and packaging helpers
├── tests/            # unit tests
├── docs/             # full documentation
└── pyproject.toml    # package definition
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `command not found` | Run `source .venv/bin/activate` first |
| `Connection refused` | Start `rcv` before running `snd` or `chat` |
| `Certificate error` | Copy `ca.crt` from receiver machine to sender |
| `pip install -e .` fails | Use `pip install .` (without the `-e` flag) |

---

## Version History

| Version | Changes |
|---|---|
| **v2.0.0** | Two-way `chat` command, short aliases `snd`/`rcv`, Python 3.14 fix |
| **v1.0.0** | Initial release: TLS 1.3, E2E crypto, `messenger-send`/`messenger-receive` |

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR.

---

## License

[MIT](LICENSE) © 2025 danshu3007-lang
