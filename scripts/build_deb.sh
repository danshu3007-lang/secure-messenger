#!/bin/bash
# scripts/build_deb.sh
# Builds a .deb package for secure-messenger.
#
# Prerequisites:
#   sudo apt install python3-pip python3-build ruby ruby-dev rubygems -y
#   sudo gem install fpm
#
# Usage:
#   bash scripts/build_deb.sh

set -euo pipefail

VERSION="1.0.0"
PACKAGE_NAME="messenger"
OUTPUT_DIR="dist"

echo "[*] Building secure-messenger v${VERSION} .deb package"
echo ""

# 1. Clean previous builds
rm -rf "$OUTPUT_DIR" build *.egg-info
mkdir -p "$OUTPUT_DIR"

# 2. Build Python wheel
echo "[1/4] Building Python wheel..."
python3 -m build --wheel --outdir "$OUTPUT_DIR"

# 3. Install wheel into staging area
echo "[2/4] Installing into staging directory..."
STAGING=$(mktemp -d)
pip3 install \
    --target "$STAGING/usr/lib/python3/dist-packages" \
    --no-deps \
    "$OUTPUT_DIR"/*.whl

# 4. Copy extra files into staging
echo "[3/4] Copying extras (certs script, systemd unit, docs)..."
mkdir -p "$STAGING/usr/share/messenger"
mkdir -p "$STAGING/usr/share/doc/messenger"
mkdir -p "$STAGING/etc/messenger/certs"

cp certs/gen_certs.sh         "$STAGING/usr/share/messenger/gen_certs.sh"
cp systemd/messenger-receive.service \
                              "$STAGING/usr/share/messenger/messenger-receive.service"
cp README.md                  "$STAGING/usr/share/doc/messenger/README.md"

chmod +x "$STAGING/usr/share/messenger/gen_certs.sh"

# 5. Build .deb with fpm
echo "[4/4] Building .deb with fpm..."
fpm \
    -s dir \
    -t deb \
    -n "$PACKAGE_NAME" \
    -v "$VERSION" \
    --description "Stateless TLS-secured terminal messenger for Linux" \
    --url "https://github.com/yourorg/secure-messenger" \
    --maintainer "you@example.com" \
    --license "MIT" \
    --architecture amd64 \
    --depends "python3 (>= 3.11)" \
    --depends "python3-cryptography" \
    --depends "openssl" \
    --after-install scripts/postinstall.sh \
    --package "$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_amd64.deb" \
    -C "$STAGING" \
    .

rm -rf "$STAGING"

echo ""
echo "[✓] Package built: $OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_amd64.deb"
echo ""
echo "Install with:"
echo "  sudo apt install ./$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_amd64.deb"
