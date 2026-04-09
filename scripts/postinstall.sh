#!/bin/bash
# scripts/postinstall.sh
# Runs automatically after: sudo apt install ./messenger.deb
set -euo pipefail

CERT_DIR="/etc/messenger/certs"

echo ""
echo "══════════════════════════════════════════════"
echo "  secure-messenger post-install setup"
echo "══════════════════════════════════════════════"

# Create cert directory with secure permissions
mkdir -p "$CERT_DIR"
chmod 750 "$CERT_DIR"

# Generate self-signed dev certs if none exist
if [ ! -f "$CERT_DIR/server.crt" ]; then
    echo ""
    echo "[*] No certificates found. Generating self-signed development certs..."
    echo "[*] Replace these with real PKI certs before production use."
    echo ""
    bash /usr/share/messenger/gen_certs.sh "$CERT_DIR" "127.0.0.1"
fi

# Install systemd unit if systemd is available
if command -v systemctl &>/dev/null; then
    if [ ! -f /etc/systemd/system/messenger-receive.service ]; then
        cp /usr/share/messenger/messenger-receive.service \
           /etc/systemd/system/messenger-receive.service
        systemctl daemon-reload
        echo "[✓] systemd unit installed."
        echo "    Enable with: sudo systemctl enable --now messenger-receive"
    fi
fi

# Create dedicated system user if it doesn't exist
if ! id "messenger" &>/dev/null; then
    useradd --system --no-create-home \
            --shell /usr/sbin/nologin \
            --comment "Secure Messenger daemon" \
            messenger
    echo "[✓] System user 'messenger' created."
fi

# Set ownership
chown -R messenger:messenger "$CERT_DIR"

echo ""
echo "[✓] Installation complete!"
echo ""
echo "  Quick start:"
echo "    Receiver:  messenger-receive"
echo "    Sender:    messenger-send <receiver-ip> \"Your message\""
echo ""
echo "  Full docs: /usr/share/doc/messenger/README.md"
echo "══════════════════════════════════════════════"
