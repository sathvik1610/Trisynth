#!/bin/bash

# Usage: ./run.sh tests/full_test.tri
# Usage: ./run.sh tests/full_test.tri x86
# Usage: ./run.sh tests/full_test.tri riscv
# Usage: ./run.sh tests/full_test.tri both

FILE=$1
ARCH=${2:-both}   # second arg is just "x86", "riscv", or "both" — no --arch prefix

# Step 1 — Run compiler
python3 src/main.py "$FILE" --arch "$ARCH"

# Step 2 — Build and run x86
if [ "$ARCH" = "x86" ] || [ "$ARCH" = "both" ]; then
    echo ""
    echo "=== Running x86-64 ==="
    if [ -f "bin/linux/nasm" ]; then
        bin/linux/nasm -f elf64 output.asm -o output.o
    else
        nasm -f elf64 output.asm -o output.o
    fi
    gcc output.o -o program -no-pie
    ./program
fi

# Step 3 — Build and run RISC-V
if [ "$ARCH" = "riscv" ] || [ "$ARCH" = "both" ]; then
    echo ""
    echo "=== Running RISC-V ==="
    riscv64-linux-gnu-gcc output_riscv.s -o program_riscv -static 2>/dev/null
    qemu-riscv64-static ./program_riscv
fi