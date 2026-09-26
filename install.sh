#!/usr/bin/env bash
# TokenJar Linux & macOS 1-Click Installer
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Farukes/TokenJar/main/install.sh | bash

set -e

REPO="Farukes/TokenJar"
INSTALL_DIR="$HOME/.local/bin"
EXE_PATH="$INSTALL_DIR/tokenjar"

echo "============================================================"
echo "🍯 Installing TokenJar Native Engine for Linux / macOS..."
echo "============================================================"

# 1. Detect OS and Architecture
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
  Linux)
    case "$ARCH" in
      x86_64) ASSET_NAME="tokenjar-linux-x64.tar.gz" ;;
      *) echo "❌ Unsupported architecture: $ARCH on Linux"; exit 1 ;;
    esac
    ;;
  Darwin)
    case "$ARCH" in
      arm64) ASSET_NAME="tokenjar-darwin-arm64.tar.gz" ;;
      x86_64) ASSET_NAME="tokenjar-darwin-x64.tar.gz" ;;
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
    ;;
esac

echo ""
echo "✨ TokenJar has been successfully installed!"
echo "============================================================"

if [ -f "$EXE_PATH" ]; then
    echo "🔌 Auto-configuring MCP server across detected AI assistants..."
    "$EXE_PATH" on --global || true
    "$EXE_PATH" status || true
else
    echo "Please restart your terminal to start using 'tokenjar'."
fi
