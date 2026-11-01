# Trisynth Compiler — Setup Guide

Quick reference for getting Trisynth running. See [INSTALL.md](INSTALL.md) for details.

---

## From source (recommended)

```bash
sudo apt install -y python3 gcc nasm        # Linux or inside WSL
python3 src/main.py file.tri
```

On Windows with WSL you can run `python src\main.py file.tri` from PowerShell; the compiler uses WSL's `nasm` and `gcc` automatically.

---

## Prebuilt binary (snapshot from 14 April 2026)

### Linux / Windows WSL

Extract into your Linux home directory (not `/mnt/c/...`):

```bash
cd ~
unzip /mnt/c/Users/<YourName>/Downloads/Trisynth-Linux.zip -d Trisynth
cd Trisynth
bash setup.sh
./trisynth file.tri
```

### Windows native

```cmd
setup.bat
trisynth.exe file.tri
```

RISC-V (`--arch riscv`) is not available on native Windows. On native Windows the compiler needs `nasm` and `gcc` on `PATH`.

---

## What `setup.sh` does

| Step | Action |
|---|---|
| Check gcc | Verifies the linker is available |
| nasm | Uses a system `nasm` if present; otherwise uses (or builds) `bin/linux/nasm` |
| Permissions | Runs `chmod +x` on `trisynth` and `bin/linux/nasm` |

Setup is safe to run multiple times.

---

## Requirements

| Platform | Requirements |
|---|---|
| Linux / WSL | `gcc` and `nasm` (`sudo apt install gcc nasm`); Python 3 when running from source |
| Windows native | `nasm` and `gcc` (MinGW-w64) on `PATH` |

---

## Demo files

| File | What it demonstrates |
|---|---|
| `tests/demo1_dead_code.tri` | Dead code elimination |
| `tests/demo2_strength_reduction.tri` | Strength reduction (multiply → shift) |
| `tests/demo4_array.tri` | Array declaration and access |

The release zips ship these three files in their root folder; from a source checkout they are in `tests/`. More demos are in `tests/FinalDemo/` and `tests/demo*.tri`.
