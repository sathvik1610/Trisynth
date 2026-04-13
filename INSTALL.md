# Trisynth Compiler - Installation Guide

The Trisynth compiler relies on perfectly standalone, isolated executables, requiring zero global Python installations.

## Windows (Native)
1. Unzip the `Trisynth-Windows-Native` folder entirely.
2. Double-click on `setup.bat`. This will download a local, portable version of `nasm` strictly into your internal `bin/` directory, avoiding any global system conflicts.
> **Note:** RISC-V compilation is unsupported on native Windows. For RISC-V support, use WSL instead.

## Linux and WSL (Windows Subsystem for Linux)
1. Unzip the `Trisynth` folder.
2. Run `bash setup.sh`. Just like Windows, it checks for standard `gcc` and then safely downloads a portable local `nasm` into the `bin/` folder without requiring `sudo` or global packages.

---

## 🚀 Usage

Run the compiler via the bundled binary inside the folder.

**Windows:**
```cmd
.\trisynth.exe path/to/file.tri [FLAGS]
```

**Linux / WSL:**
```bash
./trisynth path/to/file.tri [FLAGS]
```

## 🚩 Available Flags

**Execution Modes**
- `--arch {x86, riscv, both}`: Target architecture (Default: `x86`).
- `--demo`: Interactive demo mode.
- `--benchmark`: Compile, natively execute, and compare execution performance between x86 and RISC-V (QEMU emulation).
- `--compare-asm`: Compile to both architectures and print raw assembly code side-by-side.

**Output & Trace Logging**
- `-v` or `--verbose`: Print comprehensive compilation traces across all phases.

**Debug Steps (Halting execution early)**
- `--tokens`: Output lexer tokens and halt.
- `--ast`: Output AST generation and halt.
- `--ir`: Output Intermediate Representation and halt.
- `--asm`: Output x86-64 assembly instructions and halt.
