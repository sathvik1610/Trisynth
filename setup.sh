#!/usr/bin/env bash

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}  ✅ $1${NC}"; }
fail() { echo -e "${RED}  ❌ $1${NC}"; }
info() { echo -e "${YELLOW}  ➜  $1${NC}"; }

echo ""
echo "  Trisynth Compiler — Local Setup"
echo "  ==============================="

# Detect WSL
if grep -qiE "(microsoft|wsl)" /proc/version 2>/dev/null; then
    ok "Platform: Windows WSL"
else
    ok "Platform: Linux"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check GCC (Always standard on Linux systems) 
info "Checking for standard linker (gcc)..."
if command -v gcc &>/dev/null; then
    ok "gcc found"
else
    fail "gcc not found locally! Please install standard build essentials if possible."
fi

# Check NASM - If not found, download portable local version
info "Checking for Assembler (nasm)..."
if command -v nasm &>/dev/null; then
    ok "nasm found globally"
else
    info "nasm not found globally. Downloading a portable local version..."
    mkdir -p "$SCRIPT_DIR/bin/linux"
    if [ ! -f "$SCRIPT_DIR/bin/linux/nasm" ]; then
        curl -sSL "https://www.nasm.us/pub/nasm/releasebuilds/2.16.01/linux/nasm-2.16.01-linux.zip" -o nasm.zip
        unzip -q -j nasm.zip "nasm-2.16.01/nasm" -d "$SCRIPT_DIR/bin/linux"
        chmod +x "$SCRIPT_DIR/bin/linux/nasm"
        rm nasm.zip
    fi
    ok "Portable nasm downloaded into $SCRIPT_DIR/bin/linux/nasm"
fi

chmod +x trisynth
ok "trisynth binary is ready to execute."

echo ""
echo "  Setup complete. Usage:"
echo "    ./trisynth file.tri"
echo "    ./trisynth file.tri --verbose"
echo ""
