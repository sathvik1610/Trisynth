# Trisynth Compiler

**Trisynth** is a custom-built native compiler for **NanoC**, a minimal, statically typed, C-like language.  
It compiles NanoC source through every classical stage — Lexing → Parsing → Semantic Analysis → IR Generation → Optimization → Native Code (x86-64 & RISC-V) — exposing each phase's internal representation and error reporting.

> [!NOTE]
> Trisynth is built from scratch with no parser generators or LLVM. Design decisions favour *readability and correctness* over *performance and completeness*.

---

## Table of Contents

1. [Project Overview (Goals & Non-Goals)](#1-project-overview-goals--non-goals)
2. [Installation Procedure & Quick Start](#2-installation-procedure--quick-start)
3. [Documentation](#3-documentation)
4. [Developer Guide](#4-developer-guide)
5. [Test Suite](#5-test-suite)
6. [Limitations & Known Behaviors](#6-limitations--known-behaviors)
7. [Future Work](#7-future-work)
8. [Contributors](#8-contributors)

---

## 1. Project Overview (Goals & Non-Goals)

### Goals
- **Full pipeline visibility** — every compilation phase produces inspectable output (tokens, AST, IR, optimized IR, assembly).
- **Modularity** — each phase is a self-contained Python module with its own data structures.
- **Rigorous error reporting** — compile-time errors halt early with the exact line, column, and reason.
- **Test-driven correctness** — 98 automated tests cover all three compiler phases plus the IR interpreter.

### Non-Goals
- Not a replacement for GCC, Clang, or LLVM.
- No standard-library or system-call support beyond `print` and `readInt`.
- No dynamic memory allocation (`malloc`/`free`).
- No full C ABI compliance (simplified stack-machine model for x86-64 and RISC-V).

---

## 2. Installation Procedure & Quick Start

Trisynth compiles to native code, so it needs three tools: **Python 3.8+**, **NASM** (assembler) and **GCC** (linker). The easiest way to get all three is Linux or WSL (Windows Subsystem for Linux).

### Option A — Linux or Windows WSL (recommended)

**1. Install the tools (one time):**

```bash
sudo apt update && sudo apt install -y git python3 gcc nasm
```

**2. Get the code and run a program:**

```bash
git clone https://github.com/sathvik1610/Trisynth.git ~/Trisynth
cd ~/Trisynth
python3 src/main.py tests/FinalDemo/1_fibonacci.tri
```

Expected output: `Fibonacci of 10 is:55`

> **WSL users:** do not use a Windows path such as `/mnt/c/...` or `/mnt/d/...`. Clone into your Linux home directory (`~`) as shown above, otherwise file permissions break.
> Don't have WSL yet? Open PowerShell as Administrator, run `wsl --install`, restart, then open the **Ubuntu** app and follow the steps above.

### Option B — Windows native (no WSL)

1. Download `releases/Trisynth-Windows-Native.zip` from this repository and unzip it.
2. Double-click `setup.bat` (it downloads a portable NASM; MinGW `gcc` must be installed).
3. Open Command Prompt in that folder and run:

```cmd
trisynth.exe demo2_strength_reduction.tri
```

RISC-V output (`--arch riscv`) is not available on native Windows; use WSL for it.

### Option C — Prebuilt Linux binary (no Python needed)

```bash
unzip releases/Trisynth-Linux.zip -d ~/Trisynth
cd ~/Trisynth
bash setup.sh
./trisynth demo2_strength_reduction.tri
```

### Everyday usage

```bash
python3 src/main.py <file.tri> [flags]      # from source
./trisynth <file.tri> [flags]               # prebuilt binary
```

| Flag | Effect |
|---|---|
| *(none)* | Compile and run the program |
| `-v` / `--verbose` | Print every compilation phase |
| `--tokens` | Print lexer tokens and stop |
| `--ast` | Print the Abstract Syntax Tree and stop |
| `--ir` | Print the IR and each optimization pass, then stop |
| `--asm` | Print the generated x86-64 assembly and stop |
| `--arch x86` | Target x86-64 (default) |
| `--arch riscv` | Target RISC-V 64-bit (Linux/WSL only) |
| `--arch both` | Compile for both architectures |
| `--compare-asm` | Show x86-64 and RISC-V assembly side by side |
| `--benchmark` | Benchmark x86 vs RISC-V (needs QEMU) |
| `--demo` | Interactive REPL mode |

### Try the demos

All demo programs live in `tests/FinalDemo/`:

```bash
python3 src/main.py tests/FinalDemo/2_bubble_sort.tri
python3 src/main.py tests/FinalDemo/6_opt_const_fold_strength.tri --ir   # watch the optimizer work
python3 src/main.py tests/FinalDemo/8_final_showcase.tri --asm
```

### Sample program

```c
// Recursive factorial
int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

void main() {
    print(factorial(5));   // Output: 120
}
```

Save it as `hello.tri` and run `python3 src/main.py hello.tri`.

### Troubleshooting

| Problem | Fix |
|---|---|
| `No assembler toolchain found` | `nasm` or `gcc` is missing. Install them (Option A, step 1). |
| `Permission denied` in WSL | You are inside `/mnt/...`. Clone into `~` instead. |
| `python3: command not found` | `sudo apt install python3` |

For more detail see [INSTALL.md](INSTALL.md), [SETUP.md](SETUP.md) and the [Installation Manual](docs/deliverables/Installation_Manual.md).

---

## 3. Documentation

The full technical details of the Trisynth compiler and the NanoC language are documented extensively in the `docs/deliverables` directory. Please refer to the following documents:

### Language Reference Manual
Contains the complete lexical semantics, type system, operator rules, statement structures, function definitions, array implementations, and built-in I/O of the NanoC language.
- [Language Manual (PDF)](docs/deliverables/Language_Manual.pdf)
- [Language Manual (Markdown)](docs/deliverables/Language_Manual.md)

### Technical Documentation
Contains comprehensive architectural details covering the Lexer, Parser, Semantic Analyzer, IR Generator, Optimizer, and Backend (x86-64 & RISC-V), as well as the IR Instruction Set and error handling references.
- [Technical Documentation (PDF)](docs/deliverables/Technical_Documentation.pdf)
- [Technical Documentation (Markdown)](docs/deliverables/Technical_Documentation.md)

---

## 4. Developer Guide

If you want to modify Trisynth or understand its internals, you can run the raw Python source code directly without using the pre-compiled binaries.

### Prerequisites

Ensure you have Python 3.10+ installed. Clone the repository and install the required development dependencies:

```bash
git clone https://github.com/sathvik1610/Trisynth.git
cd Trisynth
pip install -r requirements.txt
```

If you plan to manually assemble and run the native machine code outputs (x86-64 or RISC-V), you will also need the respective external toolchains:

**Debian / Ubuntu / WSL:**
```bash
# For x86-64 assembly
sudo apt-get install nasm gcc

# For RISC-V emulation
sudo apt-get install qemu-user gcc-riscv64-linux-gnu
```

**Windows Native:**
- Install [NASM](https://www.nasm.us/) and add it to your PATH.
- Install [MinGW-w64 (GCC)](https://www.mingw-w64.org/) for linking.
*(Note: RISC-V emulation is only supported via WSL on Windows).*

### Running from Source

Instead of using the `./trisynth` binary via the release artifacts, execute the compiler through the main entry point to generate the `.asm` (x86) or `.s` (RISC-V) files. Then, use external assemblers to link and run them.

```bash
# 1. Compile NanoC code to Assembly
python src/main.py path/to/source.tri --asm

# 2a. Assemble and Link x86-64 (Linux/WSL)
nasm -f elf64 output.asm -o output.o
gcc -no-pie output.o -o program
./program

# 2b. Assemble and Link RISC-V (Linux/WSL)
riscv64-linux-gnu-gcc -static output_riscv.s -o program_riscv
qemu-riscv64 ./program_riscv

# Interactive REPL mode for quick testing without ASM
python src/main.py --demo
```

### Pipeline Debugging Flags

When making changes to specific phases of the compiler (like the Parser or the IR Generator), use debugging flags to visualize intermediate outputs:

- **Lexer Output**: `python src/main.py --tokens file.tri`
- **AST Output**: `python src/main.py --ast file.tri`
- **IR Output**: `python src/main.py --ir file.tri`
- **Assembly Output**: `python src/main.py --asm file.tri`
- **Full Execution Trace**: `python src/main.py -v file.tri`

*(Note: The `trisynth` binary supports these exact same flags.)*

### Modifying the Codebase

- **Frontend** (`src/frontend/`): Modify `lexer.py` to add new tokens or `parser.py` to change syntax grammar rules.
- **Semantics** (`src/semantic/`): Modify `analyzer.py` to apply new type checks or scoping rules.
- **IR Generation** (`src/ir/`): Update `ir_gen.py` and `instructions.py` to alter Three-Address Code generation behavior.
- **Optimization** (`src/optimization/`): Add or tweak new optimization passes here.
- **Backend** (`src/backend/`): Adjust the target assembly emission and stack-machine translations in `x86_allocator.py` or `riscv_allocator.py`.

---

## 5. Test Suite

The test suite lives in `tests/unit/` and is run with `pytest`. All 98 tests complete in under 0.2 seconds.

### Test Files

| File | Count | What It Tests |
|---|---|---|
| `test_lexer.py` | ~8 | Tokenization of all token types |
| `test_parser.py` | ~8 | AST structure from valid programs |
| `test_semantic.py` | ~12 | Core semantic rules (types, scopes) |
| `test_ir.py` | ~8 | IR instruction correctness |
| `test_optimizer.py` | ~9 | Constant folding, strength reduction, DCE |
| `test_arrays_and_recursion_errors.py` | **8** | Negative: array errors, bad types, missing returns |
| `test_arrays_and_recursion_valid.py` | **10** | Positive: valid programs produce correct output |
| `test_bug_hunter.py` | **35** | Deep negative: 4 Lexer + 10 Parser + 21 Semantic edge cases |

### Running Specific Tests
```bash
# Run only the bug hunter suite
python -m pytest tests/unit/test_bug_hunter.py -v

# Run tests matching a keyword
python -m pytest -k "array" -v

# Run a single test
python -m pytest tests/unit/test_bug_hunter.py::TestSemanticErrors::test_break_outside_loop -v

# Run with short traceback
python -m pytest --tb=short
```

### Test Design Philosophy
- **Negative tests** (`DID NOT RAISE` = bug): each test asserts that a specific invalid program raises a specific exception with a matching error message.
- **Positive tests**: each test runs the full pipeline and asserts that `PRINT` output matches the expected values exactly.
- **Bug Hunter tests** deliberately try edge cases that are easy to miss: single `&`/`\|`, unclosed comments, const-through-increment, relational-as-int, duplicate functions, wrong argument counts.

---

## 6. Limitations & Known Behaviors

### Language Limitations
| Limitation | Detail |
|---|---|
| No pointer arithmetic | No `*` (dereference) or `&` (address-of) operators |
| No structs or enums | Only primitive types and fixed-size int arrays |
| No switch statement | Use `if/else if/else` chains |
| No ternary operator | Use `if/else` instead |
| No function pointers | Functions are not first-class values |
| Float support minimal | `float` is a keyword but IR/backend treats float literals as int where possible |

### Runtime Behaviors
| Situation | Behavior |
|---|---|
| Array out-of-bounds | Undefined behavior — no runtime check |
| Integer overflow | Undefined behavior — follows Python int semantics in interpreter |
| Reading uninitialized local | Undefined — gets 0 in IR interpreter by default |
| Division by zero | Undefined — Python `ZeroDivisionError` in interpreter |
| Deep recursion | Limited by Python recursion depth in the IR interpreter |

### Compiler Behaviors
| Situation | Behavior |
|---|---|
| First error only | The compiler panics and halts at first error (no error recovery) |
| No warnings | Everything is either an error or silently accepted |
| `for` loop variable scoping | The loop-init variable is visible in the loop body and update clause |
| `++x` on const | Caught as "Cannot assign to const" — because `++x` desugars to `x = x + 1` |

---

## 7. Future Work

| Enhancement | Description |
|---|---|
| Array bounds checking | Insert `check_bounds` IR instructions before every `ALOAD`/`ASTORE` |
| SSA form | Convert IR to Static Single Assignment for more aggressive optimization |
| Control Flow Graph | Build a CFG to enable global dataflow analysis (live variable analysis, reaching definitions) |
| Register allocation | Implement Linear Scan or Graph Coloring to use CPU registers instead of stack for all variables |
| Structs | User-defined composite types |
| Error recovery | Continue past the first error to report multiple errors in one pass |
| Inlining | Inline small non-recursive functions at their call sites |
| Interprocedural constant propagation | Propagate constants across function boundaries |

---

## 8. Contributors

| Name | ID |
|---|---|
| V. Chitraksh | CS23B054 |
| P. Sathvik | CS23B042 |
| S. Danish Dada | CS23B047 |

---

*Trisynth — A Compiler Built to Be Read.*
