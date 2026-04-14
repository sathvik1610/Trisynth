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

# Check NASM - Must be installed globally for Linux or compiled locally
info "Checking for Assembler (nasm)..."
if command -v nasm &>/dev/null; then
    ok "nasm found globally"
else
    info "nasm not found globally. Building a local portable version from source (no sudo needed)..."
    mkdir -p "$SCRIPT_DIR/bin/linux"
    if [ ! -f "$SCRIPT_DIR/bin/linux/nasm" ]; then
        curl -sSL "https://www.nasm.us/pub/nasm/releasebuilds/2.16.01/nasm-2.16.01.tar.xz" -o nasm.tar.xz
        tar -xf nasm.tar.xz
        cd nasm-2.16.01 || exit
        ./configure > /dev/null
        make > /dev/null
        mv nasm "$SCRIPT_DIR/bin/linux/nasm"
        cd "$SCRIPT_DIR" || exit
        rm -rf nasm-2.16.01 nasm.tar.xz
    fi
    ok "Portable nasm compiled locally into $SCRIPT_DIR/bin/linux/nasm"
fi

# Ensure the nasm binary (pre-bundled or freshly compiled) is executable
if [ -f "$SCRIPT_DIR/bin/linux/nasm" ]; then
    chmod +x "$SCRIPT_DIR/bin/linux/nasm"
fi

chmod +x "$SCRIPT_DIR/trisynth"
ok "trisynth binary is ready to execute."

echo ""
echo "  Setup complete. Usage:"
echo "    ./trisynth file.tri"
echo "    ./trisynth file.tri --verbose"
echo ""
