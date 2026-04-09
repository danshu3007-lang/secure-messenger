#!/bin/bash
# tests/certs/gen_test_certs.sh
# Generates self-signed test certs for localhost / 127.0.0.1.
# Run this ONCE before running the integration tests.
#
# Usage:
#   bash tests/certs/gen_test_certs.sh

set -euo pipefail

CERT_DIR="$(dirname "$0")"
echo "[*] Generating TEST certificates in: $CERT_DIR"

# CA
openssl genrsa -out "$CERT_DIR/ca.key" 2048 2>/dev/null
openssl req -new -x509 -days 3650 \
    -key "$CERT_DIR/ca.key" \
    -out "$CERT_DIR/ca.crt" \
    -subj "/CN=TestMessengerCA/O=Test/C=IN" \
    2>/dev/null

# Server key + CSR
openssl genrsa -out "$CERT_DIR/server.key" 2048 2>/dev/null

EXT=$(mktemp)
cat > "$EXT" <<EOF
[SAN]
subjectAltName=IP:127.0.0.1,DNS:localhost
EOF

openssl req -new \
    -key "$CERT_DIR/server.key" \
    -out "$CERT_DIR/server.csr" \
    -subj "/CN=localhost/O=Test/C=IN" \
    2>/dev/null

openssl x509 -req -days 365 \
    -in "$CERT_DIR/server.csr" \
    -CA "$CERT_DIR/ca.crt" \
    -CAkey "$CERT_DIR/ca.key" \
    -CAcreateserial \
    -extfile "$EXT" \
    -extensions SAN \
    -out "$CERT_DIR/server.crt" \
    2>/dev/null

rm -f "$EXT" "$CERT_DIR/server.csr"
chmod 600 "$CERT_DIR/ca.key" "$CERT_DIR/server.key"
chmod 644 "$CERT_DIR/ca.crt" "$CERT_DIR/server.crt"

echo "[✓] Test certificates ready:"
ls -lh "$CERT_DIR"/*.crt "$CERT_DIR"/*.key
echo ""
echo "Run tests with:"
echo "  MESSENGER_CERT_DIR=tests/certs pytest tests/ -v"
