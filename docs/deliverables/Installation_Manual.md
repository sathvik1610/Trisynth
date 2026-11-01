# Trisynth Compiler — Installation Guide

There are two ways to run Trisynth:

1. **From source (recommended)** — needs Python 3, NASM and GCC. This always runs the latest code.
2. **Prebuilt binary** — the zips in `releases/` contain a PyInstaller build and need no Python. They are a snapshot from **14 April 2026** and do not include later source changes.

---

## From source

### Linux or Windows WSL

```bash
sudo apt update && sudo apt install -y git python3 gcc nasm
git clone https://github.com/sathvik1610/Trisynth.git ~/Trisynth
cd ~/Trisynth
python3 src/main.py tests/FinalDemo/1_fibonacci.tri
```

Expected output: `Fibonacci of 10 is:55`

Cloning into your Linux home directory is recommended (faster, and avoids permission problems with bundled binaries). Running from a Windows-mounted path such as `/mnt/d/...` also works when `nasm` and `gcc` are installed inside WSL.

### Windows PowerShell with WSL

With Python installed on Windows and `nasm` + `gcc` installed inside WSL, run from PowerShell:

```powershell
python src\main.py tests\FinalDemo\1_fibonacci.tri
```

The compiler detects `wsl nasm` and assembles, links and runs inside WSL. The detection has a 5-second timeout; if you see `No assembler toolchain found`, run `wsl -e true` once and try again.

### Windows native (no WSL)

`nasm` **and** `gcc` (for example MinGW-w64) must both be on your `PATH`. The compiler looks them up by name; it does not search the `bin\windows` folder that `setup.bat` creates, so add that folder to `PATH` if you use the portable NASM it downloads. RISC-V execution is not available on native Windows.

### RISC-V (Linux or WSL only)

```bash
sudo apt install qemu-user gcc-riscv64-linux-gnu
python3 src/main.py tests/FinalDemo/1_fibonacci.tri --arch riscv
```

---

## Prebuilt binaries (`releases/`)

| Your system | Download |
|---|---|
| Linux | `Trisynth-Linux.zip` |
| Windows with WSL | `Trisynth-Windows-WSL.zip` |
| Windows native | `Trisynth-Windows-Native.zip` |

**Linux / WSL** — extract into your Linux home directory (not a Windows-mounted path), then run the setup script:

```bash
unzip Trisynth-Linux.zip -d ~/Trisynth
cd ~/Trisynth
bash setup.sh
./trisynth demo2_strength_reduction.tri
```

`setup.sh` checks for `gcc`, checks for a system `nasm` (if there is none and `bin/linux/nasm` is also missing it builds NASM from source), and makes `trisynth` and `bin/linux/nasm` executable.

**Windows native**

```cmd
setup.bat
trisynth.exe demo2_strength_reduction.tri
```

`setup.bat` checks for `gcc` (warning only) and downloads a portable NASM into `bin\windows\` if no `nasm` is on `PATH`.

---

## Flags

```
python3 src/main.py <file.tri> [FLAGS]      # from source
./trisynth <file.tri> [FLAGS]               # prebuilt binary
```

| Flag | Description |
|---|---|
| *(none)* | Compile, assemble, link and run (x86-64) |
| `-v` / `--verbose` | Print all compilation phases, then run |
| `--tokens` | Print lexer tokens and stop |
| `--ast` | Print the Abstract Syntax Tree and stop |
| `--ir` | Print the IR and the IR after each optimization pass, then stop |
| `--asm` | Print the generated assembly for the selected `--arch` and stop |
| `--arch x86` | Target x86-64 (default) |
| `--arch riscv` | Target RISC-V 64-bit (Linux/WSL, needs `riscv64-linux-gnu-gcc` and `qemu-riscv64`) |
| `--arch both` | Run both targets |
| `--compare-asm` | Print the x86-64 and RISC-V assembly and stop |
| `--benchmark` | Run x86-64 natively and RISC-V under QEMU and compare timings |
| `--demo` | Read source from standard input and compile it (also used when no file is given) |

Only files ending in `.tri` are accepted. Every successful compile writes `output.asm` and `output_riscv.s` (and a normal run also `output.o` and `program` / `program.exe`) into the **current directory**.

---

## Verifying your installation

```bash
python3 src/main.py tests/FinalDemo/4_array_sum.tri
# Expected: Sum of array elements is:210
python3 -m pytest tests -q
# Expected: 186 passed (the native x86-64 tests are skipped without nasm/gcc)
```


---

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
