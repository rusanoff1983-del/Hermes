#!/usr/bin/env bash
set -e

echo "========================================================"
echo " Installing Hermes Antigravity Direct Plugin"
echo "========================================================"

TARGET_DIR="${HERMES_HOME:-$HOME/.hermes}/plugins/antigravity-direct"
mkdir -p "$TARGET_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[*] Copying plugin files to $TARGET_DIR..."
cp "$SCRIPT_DIR/plugin.yaml" "$TARGET_DIR/"
cp "$SCRIPT_DIR/__init__.py" "$TARGET_DIR/"
cp "$SCRIPT_DIR/direct.py" "$TARGET_DIR/"
cp "$SCRIPT_DIR/wire.mjs" "$TARGET_DIR/"
cp "$SCRIPT_DIR/package.json" "$TARGET_DIR/"

cd "$TARGET_DIR"
echo "[*] Installing Node.js dependencies..."
npm install --no-audit --no-fund

echo ""
echo "========================================================"
echo " Plugin successfully installed!"
echo ""
echo " Next steps:"
echo "  1. Authenticate via browser:"
echo "       hermes auth add antigravity-direct"
echo ""
echo "  2. Run a chat session:"
echo "       hermes chat --provider antigravity-direct -m gemini-3.7-flash-medium"
echo "========================================================"
