# Trisynth Compiler — Installation Guide

Trisynth ships as a **self-contained binary**. No Python installation required.

---

## 📦 Which release do I download?

| Your System | Download |
|---|---|
| Linux (Ubuntu, Debian, etc.) | `Trisynth-Linux.zip` |
| Windows with WSL | `Trisynth-Windows-WSL.zip` |
| Windows (native, no WSL) | `Trisynth-Windows-Native.zip` |

---

## 🐧 Linux

```bash
unzip Trisynth-Linux.zip -d ~/Trisynth
cd ~/Trisynth
bash setup.sh
```

> ⚠️ **Important:** Extract into your **home directory** (e.g. `~/Trisynth`), not a Windows-mounted path like `/mnt/c/...`.  
> The setup script needs Linux filesystem permissions to work correctly.

What `setup.sh` does:
- Checks for `gcc` (required for linking)
- Uses the pre-bundled `bin/linux/nasm` assembler (no download needed)
- Sets execute permissions on `trisynth` and `nasm`

Run your first program:
```bash
./trisynth demo2_strength_reduction.tri
```

---

## 🪟 Windows WSL (Recommended for Windows)

1. Open your **WSL terminal** (Ubuntu, Debian, etc.)
2. Extract into your Linux home directory — **not** `/mnt/c/...`:

```bash
# From inside WSL:
cd ~
unzip /mnt/c/Users/<YourName>/Downloads/Trisynth-Windows-WSL.zip -d Trisynth
cd Trisynth
bash setup.sh
./trisynth demo2_strength_reduction.tri
```

> ⚠️ **Do not run from `/mnt/c/...`** — Windows-mounted filesystems block the `chmod` and file permission operations that the setup needs.

---

## 🪟 Windows Native (No WSL)

1. Unzip `Trisynth-Windows-Native.zip`
2. Double-click `setup.bat` (or right-click → **Run as Administrator**)
3. Run:

```cmd
trisynth.exe demo2_strength_reduction.tri
```

> ⚠️ RISC-V compilation (`--arch riscv`) is **not available** on native Windows. Use WSL for full support.

---

## 🚩 All Available Flags

```
./trisynth file.tri [FLAGS]
```

| Flag | Description |
|---|---|
| *(none)* | Compile and run (default) |
| `-v` / `--verbose` | Print all compilation phases in detail |
| `--tokens` | Print lexer tokens and stop |
| `--ast` | Print Abstract Syntax Tree and stop |
| `--ir` | Print IR + all optimization passes and stop |
| `--asm` | Print generated x86-64 assembly and stop |
| `--arch x86` | Target x86-64 (default) |
| `--arch riscv` | Target RISC-V 64-bit (Linux/WSL only) |
| `--arch both` | Compile for both architectures |
| `--compare-asm` | Show x86-64 and RISC-V assembly side by side |
| `--benchmark` | Compile and benchmark x86 vs RISC-V (QEMU) |
| `--demo` | Interactive REPL mode |

---

## ✅ Verifying Your Installation

```bash
./trisynth demo4_array.tri
# Expected output: numbers printed to terminal, no errors
```


---

# Trisynth Compiler — Setup Guide

Quick reference for getting Trisynth running on your system.

---

## Linux

```bash
unzip Trisynth-Linux.zip -d ~/Trisynth
cd ~/Trisynth
bash setup.sh
./trisynth file.tri
```

---

## Windows WSL

> ⚠️ **Must extract to your Linux home directory** — NOT `/mnt/c/...`

```bash
# Inside WSL terminal:
cd ~
unzip /mnt/c/Users/<YourName>/Downloads/Trisynth-Windows-WSL.zip -d Trisynth
cd Trisynth
bash setup.sh
./trisynth file.tri
```

Full RISC-V support is available on WSL.

---

## Windows Native

Double-click `setup.bat`, then:

```cmd
trisynth.exe file.tri
```

> ⚠️ RISC-V (`--arch riscv`) is not supported on native Windows.

---

## What `setup.sh` does

| Step | Action |
|---|---|
| Check gcc | Verifies the linker is available |
| nasm | Uses the pre-bundled `bin/linux/nasm` (no internet needed) |
| Permissions | Runs `chmod +x` on `trisynth` and `bin/linux/nasm` |

Setup is **idempotent** — safe to run multiple times.

---

## Requirements

| Platform | Requirements |
|---|---|
| Linux / WSL | `gcc` (`sudo apt install build-essential`) |
| Windows Native | None — `setup.bat` handles everything |

---

## Demo Files Included

| File | What it demonstrates |
|---|---|
| `demo1_dead_code.tri` | Dead code elimination optimization |
| `demo2_strength_reduction.tri` | Strength reduction (multiply → shift) |
| `demo4_array.tri` | Array declaration and access |
