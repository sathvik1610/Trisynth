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
