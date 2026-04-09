# Certificate Management

## Development (self-signed)

Generate test certificates for localhost:

```bash
bash tests/certs/gen_test_certs.sh
```

Generate production self-signed certs for a specific IP:

```bash
sudo bash certs/gen_certs.sh /etc/messenger/certs 192.168.1.5
```

## Production (real PKI)

Replace the generated files with certs from your PKI:

| File | Description |
|---|---|
| `ca.crt` | Your CA's public cert (distribute to all senders) |
| `server.crt` | Server certificate signed by your CA |
| `server.key` | Server private key — keep secret, chmod 600 |

### Using Let's Encrypt (if receiver has a DNS name)

```bash
sudo certbot certonly --standalone -d messenger.example.com
sudo cp /etc/letsencrypt/live/messenger.example.com/fullchain.pem \
        /etc/messenger/certs/server.crt
sudo cp /etc/letsencrypt/live/messenger.example.com/privkey.pem \
        /etc/messenger/certs/server.key
# ca.crt = Let's Encrypt root — already trusted by most systems
```

### Using HashiCorp Vault PKI

```bash
vault write pki/issue/messenger \
    common_name="messenger-receiver" \
    ip_sans="192.168.1.5" \
    ttl="8760h"
```

## Distributing the CA cert to senders

Senders need `ca.crt` to verify the receiver's identity:

```bash
scp /etc/messenger/certs/ca.crt user@sender-host:/etc/messenger/certs/ca.crt
```

## Security notes

- **Never** commit `*.key` files to git (see `.gitignore`)
- Private keys must be `chmod 600` and owned by the messenger user
- Rotate server certs annually (or use short-lived certs via Vault)
