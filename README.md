# secure-messenger

Send encrypted text messages between two Linux computers on the same network.
No accounts. No internet required. Nothing is saved anywhere.

---

## What this actually does

You run one command on Computer A to listen. You run one command on Computer B
to send. The message travels encrypted. It appears on Computer A's screen.
Then it's gone — not saved, not logged, not stored anywhere.

That's it. That's the whole thing.

```
Computer B                          Computer A
────────────────────────────────────────────────────
messenger-send 192.168.1.5 "hello"  messenger-receive
                                    
                                    ┌─ MESSAGE ──────
                                    │  hello
                                    └────────────────
```

---

## What it is good for

- Sending a quick alert from one server to another on your home or office network
- Notifying yourself when a script finishes running
- Private messages between two computers you own and control
- Learning how TLS encryption and sockets work by reading clean Python code

## What it is NOT good for

- Chatting with friends over the internet — use Signal for that
- Group messaging — this is one sender, one receiver only
- Hiding who is talking to whom — IP addresses are still visible
- Replacing WhatsApp, Telegram, or any normal chat app

---

## How the encryption works — in plain words

Every message is protected by two layers:

**Layer 1 — TLS 1.3** (always on)
This is the same encryption your bank uses. The message is scrambled before
it leaves Computer B and only Computer A can unscramble it. Nobody on the
network in between can read it.

**Layer 2 — AES-256-GCM** (optional, use `--e2e`)
A second scramble on top of the first, using a secret key that only you have.
Even if someone broke TLS (extremely unlikely), they still cannot read the message.

**What encryption does NOT protect:**
- An attacker can still see that Computer B sent something to Computer A
- They can see the approximate size and timing of messages
- They cannot read the content

---

## Install

```bash
git clone https://github.com/yourname/secure-messenger
cd secure-messenger
pip install -e .
```

Check it worked:
```bash
messenger-send --help
messenger-receive --help
```

---

## First-time setup — certificates

Before using it for the first time, you need to generate certificates.
These prove to the sender that they are talking to the right computer.

On the **receiving computer**, run this once:
```bash
sudo bash certs/gen_certs.sh /etc/messenger/certs YOUR_IP_ADDRESS
```

Replace `YOUR_IP_ADDRESS` with the actual IP of your receiving computer.
To find your IP, run: `ip addr | grep 192`

Then copy the CA certificate to the **sending computer**:
```bash
scp /etc/messenger/certs/ca.crt youruser@SENDER_IP:/etc/messenger/certs/ca.crt
```

You only do this once.

---

## Basic usage — two computers, same network

**On Computer A (the receiver) — run this first:**
```bash
messenger-receive
```

You will see:
```
[*] Listening on 0.0.0.0:8443  [TLS only]
[*] Press Ctrl+C to stop.
```

**On Computer B (the sender):**
```bash
messenger-send 192.168.1.5 "hello from computer B"
```

Replace `192.168.1.5` with the actual IP of Computer A.

You will see on Computer B:
```
[✓] Message sent securely to 192.168.1.5:8443
```

And on Computer A:
```
[+] Connection from 192.168.1.5:54321
┌─ MESSAGE from 192.168.1.5 ─────
│  hello from computer B
└────────────────────────────────
```

---

## Optional: double encryption with --e2e

This adds a second layer of encryption on top of TLS using a key only you have.

**Step 1 — Generate a shared key on one computer:**
```bash
messenger-keygen
```

This creates `/etc/messenger/certs/e2e.key`

**Step 2 — Copy it to the other computer:**
```bash
scp /etc/messenger/certs/e2e.key youruser@OTHER_IP:/etc/messenger/certs/e2e.key
```

**Step 3 — Use --e2e on both sides:**
```bash
# Receiver
messenger-receive --e2e

# Sender
messenger-send 192.168.1.5 "secret message" --e2e
```

**Important:** Both sides must use `--e2e` or neither side should. Mixing them
causes a decryption error.

---

## Optional: only allow known senders with --mtls

Without `--mtls`, anyone on your network who has your CA certificate can
send you a message. With `--mtls`, only senders with a certificate you
personally signed can connect.

```bash
# Start receiver — only accept known senders
messenger-receive --mtls
```

See `certs/README.md` for how to create client certificates.

---

## Run on a custom port

Default port is 8443. Change it like this:

```bash
messenger-receive 9000
messenger-send 192.168.1.5 "hello" --port 9000
```

---

## Honest limitations

| What doesn't work | Why |
|---|---|
| Internet / public network use | Designed for LAN only, no NAT traversal |
| Hiding who talks to whom | IP addresses are always visible |
| If key file is stolen | Past messages can be decrypted (PSK limitation) |
| Multiple receivers | One sender → one receiver only |
| Works on Windows or Mac | Linux only |
| Automatic key rotation | Manual only |

---

## Running tests

```bash
pip install pytest
bash tests/certs/gen_test_certs.sh
MESSENGER_CERT_DIR=tests/certs pytest tests/ -v
```

---

## Requirements

- Linux (Ubuntu 22.04+ or Arch or any modern distro)
- Python 3.11 or newer
- OpenSSL installed (it is on most Linux systems by default)

---

## License

MIT — see `LICENSE`
