#!/bin/bash
# certs/gen_certs.sh
# Generates a self-signed CA + server certificate for production use.
# For development/testing, use tests/certs/gen_test_certs.sh instead.
#
# Usage:
#   sudo bash certs/gen_certs.sh [/etc/messenger/certs] [server-ip-or-hostname]
#
# Example:
#   sudo bash certs/gen_certs.sh /etc/messenger/certs 192.168.1.5

set -euo pipefail

CERT_DIR="${1:-/etc/messenger/certs}"
SERVER_IP="${2:-127.0.0.1}"

echo "[*] Generating certificates in: $CERT_DIR"
echo "[*] Server IP/hostname:          $SERVER_IP"
echo ""

mkdir -p "$CERT_DIR"
chmod 750 "$CERT_DIR"

# ── 1. Certificate Authority ──────────────────────────────────────────────────
echo "[1/4] Generating CA private key (4096-bit RSA)..."
openssl genrsa -out "$CERT_DIR/ca.key" 4096 2>/dev/null

echo "[2/4] Generating CA self-signed certificate (10-year validity)..."
openssl req -new -x509 -days 3650 \
    -key "$CERT_DIR/ca.key" \
    -out "$CERT_DIR/ca.crt" \
    -subj "/CN=MessengerCA/O=SecureMessenger/C=IN" \
    2>/dev/null

# ── 2. Server Certificate ─────────────────────────────────────────────────────
echo "[3/4] Generating server private key (4096-bit RSA)..."
openssl genrsa -out "$CERT_DIR/server.key" 4096 2>/dev/null

echo "[4/4] Generating server certificate signed by CA (1-year validity)..."

# Build SAN extension with the target IP or hostname
if [[ "$SERVER_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    SAN_VALUE="IP:${SERVER_IP},IP:127.0.0.1"
else
    SAN_VALUE="DNS:${SERVER_IP},DNS:localhost,IP:127.0.0.1"
fi

SAN_CONF=$(mktemp)
cat > "$SAN_CONF" <<EOF
[req]
distinguished_name = req_distinguished_name
req_extensions     = v3_req
prompt             = no

[req_distinguished_name]
CN = messenger-receiver
O  = SecureMessenger
C  = IN

[v3_req]
subjectAltName = ${SAN_VALUE}
EOF

openssl req -new \
    -key "$CERT_DIR/server.key" \
    -out "$CERT_DIR/server.csr" \
    -config "$SAN_CONF" \
    2>/dev/null

EXT_CONF=$(mktemp)
cat > "$EXT_CONF" <<EOF
[SAN]
subjectAltName = ${SAN_VALUE}
EOF

openssl x509 -req -days 365 \
    -in "$CERT_DIR/server.csr" \
    -CA "$CERT_DIR/ca.crt" \
    -CAkey "$CERT_DIR/ca.key" \
    -CAcreateserial \
    -extfile "$EXT_CONF" \
    -extensions SAN \
    -out "$CERT_DIR/server.crt" \
    2>/dev/null

rm -f "$SAN_CONF" "$EXT_CONF" "$CERT_DIR/server.csr"

# ── 3. Permissions ────────────────────────────────────────────────────────────
chmod 600 "$CERT_DIR/ca.key" "$CERT_DIR/server.key"
chmod 644 "$CERT_DIR/ca.crt" "$CERT_DIR/server.crt"

echo ""
echo "[✓] Done! Files written to $CERT_DIR:"
ls -lh "$CERT_DIR"
echo ""
echo "  NOTE: These are self-signed certificates."
echo "  For production: replace ca.crt/server.crt/server.key with"
echo "  certs from your internal PKI or Let's Encrypt."
echo ""
echo "  Distribute ca.crt to all SENDER machines so they can verify"
echo "  the receiver's identity:"
echo "    scp $CERT_DIR/ca.crt user@sender-host:/etc/messenger/certs/ca.crt"
