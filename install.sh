#!/usr/bin/env bash
# Token-Saver Linux & macOS 1-Click Installer
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Farukes/Token-Saver/main/install.sh | bash

set -e

REPO="Farukes/Token-Saver"
INSTALL_DIR="$HOME/.local/bin"
EXE_PATH="$INSTALL_DIR/token-saver"

echo "============================================================"
echo "🔋 Installing Token-Saver Native Engine for Linux / macOS..."
echo "============================================================"

# 1. Detect OS and Architecture
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
  Linux)
    case "$ARCH" in
      x86_64) ASSET_NAME="token-saver-linux-x64.tar.gz" ;;
      *) echo "❌ Unsupported architecture: $ARCH on Linux"; exit 1 ;;
    esac
    ;;
  Darwin)
    case "$ARCH" in
      arm64) ASSET_NAME="token-saver-darwin-arm64.tar.gz" ;;
      x86_64) ASSET_NAME="token-saver-darwin-x64.tar.gz" ;;
      *) echo "❌ Unsupported architecture: $ARCH on macOS"; exit 1 ;;
    esac
    ;;
  *)
    echo "❌ Unsupported operating system: $OS"; exit 1 ;;
esac

# 2. Ensure install directory exists
mkdir -p "$INSTALL_DIR"

# 3. Determine download URL
DOWNLOAD_URL="https://github.com/$REPO/releases/latest/download/$ASSET_NAME"
TEMP_DIR="$(mktemp -d)"
ARCHIVE_PATH="$TEMP_DIR/$ASSET_NAME"

echo "📥 Downloading $ASSET_NAME from $DOWNLOAD_URL..."
curl -fsSL "$DOWNLOAD_URL" -o "$ARCHIVE_PATH"

echo "📦 Extracting into $INSTALL_DIR..."
tar -xzf "$ARCHIVE_PATH" -C "$INSTALL_DIR"
chmod +x "$EXE_PATH"
rm -rf "$TEMP_DIR"

# 4. Check PATH
case ":$PATH:" in
  *":$INSTALL_DIR:"*) ;;
  *)
    echo "⚠️ Note: $INSTALL_DIR is not in your PATH."
    echo "   Add the following line to your ~/.bashrc or ~/.zshrc:"
    echo "     export PATH=\"$INSTALL_DIR:\$PATH\""
    export PATH="$INSTALL_DIR:$PATH"
    ;;
esac

echo ""
echo "✨ Token-Saver has been successfully installed!"
echo "============================================================"
"$EXE_PATH" status || true
