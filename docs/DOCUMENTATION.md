# secure-messenger — Complete Project Documentation

**Version:** 2.0.0
**Author:** danshu3007-lang
**GitHub:** https://github.com/danshu3007-lang/secure-messenger
**License:** MIT

---

## Table of Contents

1. Abstract
2. Introduction — What problem does this solve?
3. Background — Key concepts explained simply
4. System Design — How it works
5. Architecture — The blueprint
6. Technology Stack — What we used and why
7. Security Design — How we protect your messages
8. Installation Guide — Step by step
9. Usage Guide — Every command explained
10. Experiments — What we tested and what happened
11. Results — What we proved
12. Limitations — What this does NOT do
13. Future Work — What can be added next
14. Conclusion
15. References
16. Glossary — Simple definitions of every technical term

---

## 1. Abstract

secure-messenger is a free, open-source, terminal-based messaging program for
Linux computers. It lets two people on the same network send text messages to
each other with strong encryption. No accounts are needed, no internet
connection is required, and no messages are ever saved anywhere. Everything is
deleted the moment it is read.

The program uses TLS 1.3 — the same security technology used by banks and
hospitals — to protect every message while it travels from one computer to
another. An optional second layer of AES-256-GCM encryption can be added on top
for even stronger protection.

This document explains how the program works, how to install and use it, and
what experiments were done to test and prove its security.

---

## 2. Introduction — What problem does this solve?

### The Problem

Imagine you are working in an office or a school lab. You need to quickly send a
password, a secret code, or a private note to a colleague sitting at another
computer. You could:

- Send an email — but emails are stored on servers forever
- Use WhatsApp — but it goes through the internet and WhatsApp's servers
- Walk over and whisper — but that is not always possible

None of these options are ideal. Emails and chat apps store your messages. Even
"deleted" messages often stay on company servers.

### The Solution

secure-messenger solves this by:

1. Sending the message directly from one computer to another (no middleman)
2. Encrypting the message so nobody can read it if they intercept it
3. Deleting the message the moment it is read (nothing saved anywhere)
4. Working entirely in the terminal with simple short commands

It is like passing a sealed, self-destructing note directly to someone's hand.

### Who is this for?

- System administrators and developers working on private networks
- Security students learning about encryption and networking
- Small teams needing quick, private communication on a local network
- Researchers and educators demonstrating secure communication concepts

---

## 3. Background — Key concepts explained simply

Before understanding how the program works, here are the key ideas explained
as simply as possible.

### 3.1 What is encryption?

Imagine you write a message on paper, then put it through a machine that
scrambles all the letters into random symbols. Only someone with the right
"key" can put it through the machine in reverse and read the original message.
That is encryption.

**Example:**
```
Original:  "Hello"
Encrypted: "x7Kp@#mQ9"
Decrypted: "Hello"   ← only possible with the correct key
```

### 3.2 What is TLS?

TLS stands for Transport Layer Security. It is a system that:
- Creates a secure "tunnel" between two computers
- Makes sure nobody in the middle can read your data
- Verifies that you are talking to the right computer (not an impostor)

TLS 1.3 is the newest and strongest version. Your bank's website uses it.
You can see it working — the padlock icon in your browser means TLS is active.

### 3.3 What is a certificate?

A certificate is like a digital ID card for a computer. It proves:
- "I am really the computer you want to talk to"
- "I was approved by a trusted authority"

When our receiver program starts, it shows its certificate. The sender checks
it before sending any message. If the certificate is fake or expired, the
sender refuses to connect.

### 3.4 What is a port?

A port is like a door number on a building. A computer has 65,535 doors. When
a program wants to receive connections, it opens one specific door and waits.
Our receiver opens door 8443 by default. The sender knocks on that door.

### 3.5 What is AES-256-GCM?

AES-256-GCM is an encryption algorithm — a mathematical recipe for scrambling
data. The "256" means it uses a 256-bit key (a number so large that guessing
it would take longer than the age of the universe). The "GCM" part also
detects if anyone has tampered with the message in transit.

### 3.6 What is stateless?

Stateless means the program has no memory. It does not remember previous
messages, does not keep a history, and does not store anything. Each message
is completely independent. After the message is read, it is gone forever.

---

## 4. System Design — How it works

### 4.1 The big picture

```
[Person A's computer]                    [Person B's computer]
      │                                          │
      │  types: chat 192.168.1.5                 │  types: chat 192.168.1.10
      │                                          │
      ▼                                          ▼
 ┌─────────┐    encrypted message over TLS  ┌─────────┐
 │  SENDER │ ─────────────────────────────► │RECEIVER │
 │  SIDE   │ ◄───────────────────────────── │  SIDE   │
 └─────────┘    encrypted message over TLS  └─────────┘
      │                                          │
   message                                    message
  appears                                     appears
  on screen                                  on screen
```

Both sides can send AND receive at the same time. This is the "two-way chat"
feature added in version 2.

### 4.2 What happens when you send a message — step by step

Let's trace exactly what happens when you type `"Hello"` and press Enter:

**Step 1 — You type the message**
The program reads what you typed.

**Step 2 — Message is validated**
The program checks:
- Is the message empty? (reject if so)
- Is it too long? (max 4096 bytes — about 4000 characters)

**Step 3 — TCP connection is opened**
The program opens a connection to the receiver's IP address and port.
TCP is the "pipe" through which data flows.

**Step 4 — TLS handshake**
Before any message is sent, the two computers do a "handshake":
- Sender says: "Hello, I want to talk securely"
- Receiver shows its certificate (ID card)
- Sender checks: "Is this certificate valid? Is it really who I expect?"
- Both sides agree on encryption keys using mathematics (no keys are sent!)
- A secure encrypted tunnel is now open

**Step 5 — Message is formatted**
The message is wrapped in a simple format:
```
[4 bytes: message length][JSON text: {"msg": "Hello"}]
```
The 4-byte length prefix prevents attackers from sending infinite data.

**Step 6 — Message travels through the TLS tunnel**
The message goes through the encrypted tunnel. Anyone watching the network
sees only random-looking bytes. They cannot read "Hello".

**Step 7 — Receiver decodes and prints**
The receiver unwraps the message, prints it to the terminal, and discards it.
Nothing is written to disk. Nothing is logged.

**Step 8 — Connection closes**
The connection is closed immediately. No state is kept.

---

## 5. Architecture — The Blueprint

### 5.1 Project folder structure explained

```
secure-messenger/
│
├── messenger/                   ← All the Python code lives here
│   │
│   ├── common/                  ← Code shared by everyone
│   │   ├── constants.py         ← Settings: ports, limits, cert paths
│   │   ├── exceptions.py        ← Custom error types
│   │   └── serializer.py        ← Converts messages to/from wire format
│   │
│   ├── crypto/                  ← Encryption code
│   │   └── e2e.py               ← AES-256-GCM encryption and key derivation
│   │
│   ├── sender/                  ← Code for sending messages
│   │   ├── cli.py               ← messenger-send command
│   │   ├── connection.py        ← Opens connection and sends message
│   │   └── tls_client.py        ← Sets up TLS encryption on sender side
│   │
│   ├── receiver/                ← Code for receiving messages
│   │   ├── cli.py               ← messenger-receive command
│   │   ├── server.py            ← Waits for connections, reads messages
│   │   └── tls_server.py        ← Sets up TLS encryption on receiver side
│   │
│   ├── shortcuts/               ← Short command aliases
│   │   ├── snd.py               ← `snd` command (short for messenger-send)
│   │   └── rcv.py               ← `rcv` command (short for messenger-receive)
│   │
│   └── chat/                    ← Two-way chat (NEW in v2)
│       ├── cli.py               ← `chat` command entry point
│       └── session.py           ← Runs sender + receiver simultaneously
│
├── certs/                       ← Certificate tools
│   ├── gen_certs.sh             ← Script to generate production certificates
│   └── README.md                ← Certificate management guide
│
├── systemd/                     ← Linux service management
│   └── messenger-receive.service ← Run receiver as background service
│
├── scripts/                     ← Build and install scripts
│   ├── build_deb.sh             ← Build a .deb Linux package
│   └── postinstall.sh           ← Runs after apt install
│
├── tests/                       ← Automated tests
│   ├── certs/                   ← Test certificates (for localhost only)
│   ├── unit/                    ← Tests for individual functions
│   └── integration/             ← Tests for the whole system together
│
├── docs/                        ← Documentation (you are reading this)
├── pyproject.toml               ← Package definition and install config
├── README.md                    ← Quick start guide
└── LICENSE                      ← MIT license
```

### 5.2 How the two-way chat works internally

The `chat` command is the most interesting part. Here is how it achieves
two-way communication:

```
Your terminal
│
├── [Main thread]      ← reads your keyboard input → sends to peer
│
└── [Background thread] ← listens on your port → prints incoming messages
```

Two things run simultaneously:
1. The **main thread** sits in a loop waiting for you to type. When you press
   Enter, it sends your message to the peer's IP and port.
2. The **listener thread** runs silently in the background, waiting for
   incoming connections. When the peer sends you a message, this thread
   receives it and prints it on your screen.

Both threads share the same terminal window. When an incoming message arrives,
it is inserted above your current input line, so your typing is not disrupted.

---

## 6. Technology Stack — What we used and why

| Component | Technology | Why we chose it |
|---|---|---|
| Programming language | Python 3.11+ | Clear, readable, excellent security libraries |
| Networking | `socket` (Python stdlib) | Direct control, no hidden abstraction |
| TLS encryption | `ssl` (Python stdlib) | Wraps OpenSSL — industry standard |
| E2E encryption | `cryptography` (PyCA) | Best Python crypto library, actively maintained |
| CLI interface | `argparse` (Python stdlib) | No extra dependencies needed |
| Wire format | JSON + 4-byte length prefix | Human-readable, safe, simple to audit |
| Certificate generation | `openssl` command line | Available on every Linux system |
| Package format | `pyproject.toml` + `fpm` | Modern Python standard |
| Service management | systemd | Native Linux service manager |
| Testing | `pytest` | Industry standard Python test framework |

### Why Python and not Rust or Go?

Python was chosen because:
- The code is easy to read and audit for security flaws
- Python's `ssl` module directly wraps OpenSSL, which is the same library
  used by most of the internet
- It runs on any Linux system without compilation
- The security properties come from the libraries (OpenSSL, cryptography),
  not the language — so Python is not a weakness here

For a future high-security embedded version, Rust with `rustls` would be ideal.

---

## 7. Security Design — How we protect your messages

### 7.1 The threat model

A threat model asks: "Who might attack us, and how?"

**Threats we protect against:**

| Threat | Attack scenario | Our protection |
|---|---|---|
| Eavesdropping | Someone captures network packets with Wireshark | TLS 1.3 encrypts all data |
| Tampering | Someone modifies the message in transit | GCM authentication tag detects changes |
| Replay attack | Someone records and resends old messages | Random nonce makes each message unique |
| Fake receiver | Attacker pretends to be the receiver | Certificate verification rejects impostors |
| Fake sender | Attacker pretends to be the sender | Optional mTLS requires sender certificate |
| Message storage | Messages stored and later leaked | No disk writes anywhere |
| Memory leaks | Keys left in RAM | Short-lived variables, no caching |

**Threats we do NOT protect against:**

| Threat | Why not protected |
|---|---|
| IP address visibility | TCP/IP always shows source and destination IPs |
| Timing analysis | Network observers can see when connections happen |
| Packet size inference | Encrypted packets still have visible sizes |
| Physical access | If someone has your keyboard, nothing helps |

### 7.2 TLS 1.3 configuration

We configure TLS with maximum strictness:

```
Minimum TLS version:  1.3  (TLS 1.0, 1.1, 1.2 not accepted)
Allowed ciphers:      AES-256-GCM, ChaCha20-Poly1305 (AEAD only)
Compression:          DISABLED (prevents CRIME attack)
Certificate check:    REQUIRED (no anonymous connections)
Key exchange:         Ephemeral (new keys every session = forward secrecy)
```

**Forward secrecy** means: even if someone records all your encrypted traffic
today and steals your keys next year, they still cannot decrypt old messages.
Each session uses freshly generated temporary keys.

### 7.3 Certificate verification

When the sender connects to the receiver:

1. Receiver presents its certificate ("Here is my ID")
2. Sender checks: "Was this signed by my trusted CA?" (Certificate Authority)
3. Sender checks: "Is the IP address in the certificate correct?"
4. Sender checks: "Has the certificate expired?"
5. Only if all checks pass does communication proceed

If any check fails, the connection is immediately dropped with an error message.

### 7.4 End-to-end encryption (optional second layer)

```
Without --e2e:
  [Your message] → [TLS encrypts] → network → [TLS decrypts] → [Printed]

With --e2e:
  [Your message] → [AES-256-GCM encrypts] → [TLS encrypts] → network
               → [TLS decrypts] → [AES-256-GCM decrypts] → [Printed]
```

The E2E layer uses:
- **AES-256-GCM**: encrypts and authenticates the message
- **HKDF-SHA256**: derives the actual encryption key from your shared secret
  (best practice — never use the raw key directly)
- **Random 96-bit nonce**: ensures each encrypted message looks completely
  different even if the content is identical

### 7.5 What "stateless" means in practice

The code deliberately avoids:
- Writing to any file
- Storing messages in any database
- Keeping messages in memory after printing
- Logging message content (only connection metadata is logged)

The systemd service is configured with `PrivateTmp=yes` and
`MemoryDenyWriteExecute=yes` to add OS-level enforcement of this.

---

## 8. Installation Guide — Step by Step

### 8.1 Prerequisites

Check that you have everything needed:

```bash
python3 --version   # needs 3.11 or newer
git --version       # any version
openssl version     # any version
```

### 8.2 Get the code

```bash
git clone https://github.com/danshu3007-lang/secure-messenger
cd secure-messenger
```

### 8.3 Set up Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

You will see `(.venv)` at the start of your terminal prompt. This means the
virtual environment is active.

### 8.4 Install the package

```bash
pip install .
```

Important: Use `pip install .` NOT `pip install -e .`
The `-e` (editable) flag has a known compatibility bug with Python 3.14.

### 8.5 Generate test certificates

Certificates are like ID cards. The receiver needs one so the sender can
verify it is talking to the right computer.

```bash
bash tests/certs/gen_test_certs.sh
```

This creates test certificates valid for `127.0.0.1` (your own computer).
For use on a real network, see Section 10.3.

### 8.6 Verify installation

```bash
snd --help      # should show send command options
rcv --help      # should show receive command options
chat --help     # should show chat command options
```

If you see `command not found`, you forgot to activate the virtual environment:
```bash
source .venv/bin/activate
```

---

## 9. Usage Guide — Every Command Explained

### 9.1 `chat` — Two-way live chat

This is the main command. Both people use it. Both can send and receive.

**Same machine (testing):**

Open Terminal 1:
```bash
source .venv/bin/activate
MESSENGER_CERT_DIR=tests/certs chat 127.0.0.1 -lp 8443 -pp 8444
```

Open Terminal 2:
```bash
source .venv/bin/activate
MESSENGER_CERT_DIR=tests/certs chat 127.0.0.1 -lp 8444 -pp 8443
```

Now type in either terminal and press Enter. You will see the message appear
in the other terminal with a timestamp.

**Important:** Both sides MUST be running before you send the first message.
If you send before the other side is ready, you will get "Connection refused"
— just try again.

**Two different machines on a LAN:**
```bash
# Machine A (IP: 192.168.1.5):
MESSENGER_CERT_DIR=/etc/messenger/certs chat 192.168.1.10

# Machine B (IP: 192.168.1.10):
MESSENGER_CERT_DIR=/etc/messenger/certs chat 192.168.1.5
```

**Exit chat:** Type `/quit` and press Enter, or press Ctrl+C.

---

### 9.2 `snd` — Send one message

Use this when you just want to send a single message without starting a chat.

```bash
snd 192.168.1.5 "Hello!"
snd 192.168.1.5 "Hello!" -p 9000        # different port
snd 192.168.1.5 "Hello!" --e2e           # with extra encryption
```

The receiver must be running `rcv` before you send.

---

### 9.3 `rcv` — Listen for messages

Use this when you want to receive messages (but not send back).

```bash
rcv                # listen on port 8443
rcv 9000           # listen on port 9000
rcv --local        # only accept connections from this same computer
rcv --mtls         # only accept connections from clients with valid certificates
rcv --e2e          # expect AES-256-GCM encrypted messages
```

Press Ctrl+C to stop.

---

### 9.4 `messenger-keygen` — Generate encryption key

This generates the shared key needed for E2E encryption.

```bash
messenger-keygen
```

This creates a key file at `/etc/messenger/certs/e2e.key`. You must:
1. Copy this file to the other computer's `/etc/messenger/certs/e2e.key`
2. Do this via USB stick, QR code, or other physical means
3. NEVER send the key file over the network (that would defeat the purpose)

---

### 9.5 Understanding ports

Think of ports as apartment numbers. You need to tell your peer:
"I am in apartment 8443 — send your messages there."

In `chat` mode:
- Your `-lp` (listen port) is YOUR apartment number
- Your `-pp` (peer port) is THEIR apartment number
- These must be swapped between the two sides

```
Person A runs:  chat 192.168.1.10 -lp 8443 -pp 8444
Person B runs:  chat 192.168.1.5  -lp 8444 -pp 8443
                                   ^^^^          ^^^^
                         A listens on 8443  B listens on 8444
                         A sends to 8444    B sends to 8443
```

---

## 10. Experiments — What we tested and what happened

### Experiment 1: Basic message sending

**Goal:** Verify that messages can be sent and received correctly.

**Method:**
- Ran `rcv` in Terminal 1
- Ran `snd 127.0.0.1 "Hello"` in Terminal 2
- Observed output in Terminal 1

**Result:** ✅ "Hello" appeared in Terminal 1 immediately.

**What this proves:** The basic TCP + TLS connection pipeline works correctly.

---

### Experiment 2: TLS certificate verification

**Goal:** Verify that the sender rejects connections when the certificate is wrong.

**Method:**
- Started receiver with test certificates
- Pointed sender to a different CA certificate (wrong trust)
- Attempted to send a message

**Result:** ✅ Sender rejected the connection with:
`[✗] Certificate verification failed — CERTIFICATE_VERIFY_FAILED`

**What this proves:** You cannot be tricked into sending to a fake receiver.
The certificate check is working.

---

### Experiment 3: Message size enforcement

**Goal:** Verify that oversized messages are rejected (DoS protection).

**Method:**
- Attempted to send a message of 5000 characters (limit is 4096)

**Result:** ✅ Rejected at sender with:
`[✗] Message too large: 5013 bytes (max 4096)`

**What this proves:** An attacker cannot crash the receiver by sending a
gigantic message.

---

### Experiment 4: Two-way live chat

**Goal:** Verify that both sides can send and receive simultaneously.

**Method:**
- Started `chat` in two terminals on the same machine
- Sent messages from Terminal 1 to Terminal 2
- Sent messages from Terminal 2 to Terminal 1
- Alternated rapidly

**Result:** ✅ All messages delivered correctly in both directions.
Timestamps accurate. No messages dropped or corrupted.

**What this proves:** The listener thread and input thread run independently
without blocking or interfering with each other.

---

### Experiment 5: Unit tests — all 23 pass

**Goal:** Verify that every individual component works correctly.

**Method:**
```bash
MESSENGER_CERT_DIR=tests/certs pytest tests/unit/ -v
```

**Result:**
```
tests/unit/test_e2e_crypto.py::TestKeyDerivation::test_derive_key_length   PASSED
tests/unit/test_e2e_crypto.py::TestKeyDerivation::test_same_psk_same_key   PASSED
tests/unit/test_e2e_crypto.py::TestKeyDerivation::test_different_context_different_key PASSED
tests/unit/test_e2e_crypto.py::TestEncryptDecrypt::test_roundtrip           PASSED
tests/unit/test_e2e_crypto.py::TestEncryptDecrypt::test_unicode_roundtrip   PASSED
tests/unit/test_e2e_crypto.py::TestEncryptDecrypt::test_ciphertext_different_each_time PASSED
tests/unit/test_e2e_crypto.py::TestEncryptDecrypt::test_ciphertext_longer_than_nonce   PASSED
tests/unit/test_e2e_crypto.py::TestEncryptDecrypt::test_wrong_key_raises    PASSED
tests/unit/test_e2e_crypto.py::TestEncryptDecrypt::test_tampered_ciphertext_raises     PASSED
tests/unit/test_e2e_crypto.py::TestEncryptDecrypt::test_truncated_ciphertext_raises    PASSED
tests/unit/test_e2e_crypto.py::TestEncryptDecrypt::test_empty_bytes_raises  PASSED
tests/unit/test_e2e_crypto.py::TestGeneratePsk::test_generates_file         PASSED
tests/unit/test_e2e_crypto.py::TestGeneratePsk::test_file_permissions       PASSED
tests/unit/test_serializer.py::TestEncodeMessage::test_basic_string         PASSED
tests/unit/test_serializer.py::TestEncodeMessage::test_empty_string_raises  PASSED
tests/unit/test_serializer.py::TestEncodeMessage::test_whitespace_only_raises PASSED
tests/unit/test_serializer.py::TestEncodeMessage::test_oversized_message_raises PASSED
tests/unit/test_serializer.py::TestEncodeMessage::test_unicode_message      PASSED
tests/unit/test_serializer.py::TestDecodeMessage::test_roundtrip_ascii      PASSED
tests/unit/test_serializer.py::TestDecodeMessage::test_roundtrip_unicode    PASSED
tests/unit/test_serializer.py::TestDecodeMessage::test_malformed_json_raises PASSED
tests/unit/test_serializer.py::TestDecodeMessage::test_zero_length_raises   PASSED
tests/unit/test_serializer.py::TestDecodeMessage::test_empty_connection_raises PASSED

============================== 23 passed in 0.40s ==============================
```

**What this proves:** Every encryption, decryption, encoding, and decoding
function works correctly, including all error cases.

---

### Experiment 6: E2E encryption validation

**Goal:** Verify that a tampered message is detected and rejected.

**Method:**
- Encrypted a message with AES-256-GCM
- Manually flipped one byte in the ciphertext
- Attempted to decrypt the tampered ciphertext

**Result:** ✅ Rejected with:
`E2EKeyError: message was tampered with, or you are using the wrong key`

**What this proves:** GCM authentication detects any modification to the
encrypted data. An attacker cannot modify messages without being detected.

---

## 11. Results — What we proved

| Claim | Experimental proof | Status |
|---|---|---|
| Messages are encrypted in transit | Certificate test showed rejection of wrong cert | ✅ Proven |
| Tampered messages are detected | GCM tag test showed rejection of flipped byte | ✅ Proven |
| Oversized messages are blocked | Size limit test showed rejection at 5000 bytes | ✅ Proven |
| Two-way communication works | Live chat test showed bidirectional messaging | ✅ Proven |
| No messages stored to disk | Code review: no file write operations anywhere | ✅ Verified |
| TLS 1.3 enforced | Config review: minimum_version = TLSv1_3 | ✅ Verified |
| 23 unit tests pass | pytest output: 23 passed, 0 failed | ✅ Proven |

---

## 12. Limitations — What this does NOT do

### 12.1 Not anonymous

Your IP address is visible to anyone watching the network. If you need
complete anonymity, this tool is not enough. Tools like Tor-based messengers
are designed for that purpose.

### 12.2 Not internet-routable (without extra setup)

By default, this only works on a local network (LAN). If the receiver is
behind a home router and you are outside, the connection will fail unless:
- Port forwarding is configured on the router, OR
- A relay server is used

### 12.3 No message routing

There is no concept of "send to username" or "send to a group". You must
know the exact IP address of the person you want to reach.

### 12.4 No offline messaging

If the receiver is not running, the message is lost. There is no queue,
no retry mechanism, and no "deliver when online" feature.

### 12.5 Metadata is visible

Even though message content is encrypted, a network observer can see:
- That a connection happened between two IP addresses
- When it happened
- Roughly how large the message was (from packet size)

---

## 13. Future Work — What can be added next

### Phase 3: ECDH key exchange
Replace the pre-shared key (PSK) approach with Elliptic Curve Diffie-Hellman
(ECDH). This means no key file needs to be copied — keys are negotiated
automatically and securely over the network.

### Phase 4: Relay server
Add a simple relay server so the tool works through NAT and firewalls. Both
peers connect to the relay, which forwards encrypted messages without being
able to read them.

### Phase 5: NAT traversal
Add STUN/TURN protocol support so peers can find each other on the internet
without a relay, using "hole punching" techniques.

### Phase 6: Named identities
Add a system where users have names (like "alice", "bob") instead of IP
addresses. A simple DNS-like lookup maps names to IPs.

### Phase 7: Group chat
Allow more than two people to chat simultaneously using a multicast or
hub-and-spoke architecture.

### Phase 8: Rust rewrite
Rewrite the core (TLS + crypto + socket) in Rust for maximum performance
and memory safety. Rust's `rustls` + `tokio` + `ring` is the ideal stack
for a production-hardened version.

---

## 14. Conclusion

secure-messenger demonstrates that it is possible to build a genuinely secure,
easy-to-use messaging tool with a small amount of well-written code.

The key lessons from this project are:

**Security does not have to be complicated.** By using well-audited libraries
(Python's `ssl` module wrapping OpenSSL, and the `cryptography` library),
we get strong security without implementing any cryptography ourselves. This
is the right approach — never write your own crypto.

**Simplicity is a security feature.** The program does one thing: send a
message securely. It has no database, no accounts, no persistent state. This
means there is much less that can go wrong.

**Layered security is stronger.** TLS 1.3 already provides excellent
protection. The optional AES-256-GCM E2E layer adds a second independent
layer — so even a theoretical future weakness in TLS would not expose messages.

**Testing proves security properties.** The 23 unit tests verify not just
that the happy path works, but that attacks are correctly rejected: wrong keys,
tampered messages, oversized inputs, and empty data all produce the right
errors.

This project can serve as a foundation for learning about network security,
cryptography, and secure system design. Every concept used here — TLS, AES-GCM,
HKDF, certificate verification — is used in real-world production systems at
banks, hospitals, and government agencies.

---

## 15. References

1. **TLS 1.3 Specification** — RFC 8446
   https://tools.ietf.org/html/rfc8446

2. **AES-GCM Specification** — NIST SP 800-38D
   https://csrc.nist.gov/publications/detail/sp/800-38d/final

3. **HKDF — HMAC-based Key Derivation Function** — RFC 5869
   https://tools.ietf.org/html/rfc5869

4. **Python ssl module documentation**
   https://docs.python.org/3/library/ssl.html

5. **PyCA cryptography library**
   https://cryptography.io/en/latest/

6. **OpenSSL documentation**
   https://www.openssl.org/docs/

7. **OWASP Transport Layer Security Cheat Sheet**
   https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html

8. **systemd security hardening**
   https://www.freedesktop.org/software/systemd/man/systemd.exec.html

9. **Python socket programming**
   https://docs.python.org/3/library/socket.html

10. **pytest documentation**
    https://docs.pytest.org/en/stable/

---

## 16. Glossary — Simple definitions of every technical term

| Term | Simple definition |
|---|---|
| **AES** | Advanced Encryption Standard — a recipe for scrambling data, used worldwide |
| **AES-256-GCM** | AES with a 256-bit key and GCM authentication — very strong encryption |
| **Authentication** | Proving that a message has not been modified and came from who you think |
| **CA (Certificate Authority)** | A trusted party that signs certificates, like a notary public |
| **Certificate** | A digital ID card for a computer, signed by a CA |
| **Cipher** | A mathematical algorithm for encrypting data |
| **Ciphertext** | Data after encryption — looks like random garbage |
| **CLI** | Command Line Interface — programs you use by typing commands |
| **Decryption** | Converting scrambled data back to readable form using a key |
| **E2E** | End-to-end encryption — data is encrypted from sender all the way to receiver |
| **Encryption** | Converting readable data into scrambled form using a key |
| **Forward secrecy** | Old messages stay safe even if current keys are stolen later |
| **GCM** | Galois/Counter Mode — adds authentication on top of AES encryption |
| **HKDF** | Hash-based Key Derivation Function — safely derives keys from a secret |
| **IP address** | A unique number identifying a computer on a network (like 192.168.1.5) |
| **Key** | A secret value used by an encryption algorithm |
| **LAN** | Local Area Network — computers connected in the same home or office |
| **mTLS** | Mutual TLS — both sender and receiver verify each other's certificates |
| **Nonce** | A random number used once — prevents the same message looking the same twice |
| **OpenSSL** | A widely-used open-source library implementing TLS and cryptography |
| **PKI** | Public Key Infrastructure — the system of certificates and CAs |
| **Plaintext** | Data before encryption — readable |
| **Port** | A numbered "door" on a computer that a program listens on |
| **PSK** | Pre-Shared Key — a secret both sides agree on before communication |
| **Replay attack** | Recording a message and sending it again later |
| **RFC** | Request for Comments — official internet standards documents |
| **SAN** | Subject Alternative Name — the list of IPs/hostnames a certificate is valid for |
| **Socket** | A programming interface for network connections |
| **SSL** | Secure Sockets Layer — the old name for TLS (now deprecated) |
| **Stateless** | No memory, no storage, no history — each operation is independent |
| **systemd** | Linux's system and service manager |
| **TCP** | Transmission Control Protocol — reliable data delivery over networks |
| **TLS** | Transport Layer Security — the protocol that encrypts internet connections |
| **TLS handshake** | The negotiation that happens before secure communication begins |
| **venv** | Virtual environment — isolated Python installation for a project |
| **Wire format** | The exact byte structure of data sent over the network |
