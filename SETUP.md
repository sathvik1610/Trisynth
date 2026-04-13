# Trisynth Compiler — Setup Guide

## Linux
```bash
bash setup.sh
./trisynth file.tri
```

## WSL (Windows Subsystem for Linux)
Open your WSL terminal, navigate to the project folder, then:
```bash
bash setup.sh
./trisynth file.tri
```
WSL setup is identical to Linux and includes full RISC-V support.

## Native Windows
Double-click `setup.bat` (or right-click → Run as Administrator).
```
trisynth.bat file.tri
```
> ⚠️ RISC-V compilation (`--arch riscv`) is not available on native Windows.
> Install WSL for full support: https://aka.ms/wslinstall

---

## What setup does
| Step | Linux / WSL | Native Windows |
|------|------------|----------------|
| System packages | `apt` installs nasm, gcc, riscv64 toolchain, qemu | winget installs NASM + MSYS2/MinGW |
| Python venv | `.venv/` created | `.venv\` created |
| Python deps | Installed from `requirements.txt` | Installed from `requirements.txt` |
| Launcher | `./trisynth` shell script | `trisynth.bat` batch file |

Setup scripts are **idempotent** — safe to re-run.

---

## Requirements
- **Linux / WSL**: `python3`, `sudo` apt access
- **Windows**: Python 3.x from python.org, winget (comes with Windows 10 1709+ / 11)
