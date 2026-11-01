# Trisynth Compiler

**Trisynth** is a native compiler, written in Python, for a small statically typed, C-like language (source files use the `.tri` extension; the language is also referred to as NanoC).
It compiles source through the classical stages — Lexing → Parsing → Semantic Analysis → IR Generation → Optimization → Assembly (x86-64 and RISC-V) — and can print each stage's internal representation.

> [!NOTE]
> Trisynth is built from scratch with no parser generators, no LLVM and no third-party runtime dependencies (only the Python standard library). Design decisions favour *readability and correctness* over *performance and completeness*. See [Design Choices](#6-design-choices) and [Known Limitations](#7-known-limitations--behaviors).

---

## Table of Contents

1. [Project Overview (Goals & Non-Goals)](#1-project-overview-goals--non-goals)
2. [Installation Procedure & Quick Start](#2-installation-procedure--quick-start)
3. [Documentation](#3-documentation)
4. [Developer Guide](#4-developer-guide)
5. [Test Suite](#5-test-suite)
6. [Design Choices](#6-design-choices)
7. [Known Limitations & Behaviors](#7-known-limitations--behaviors)
8. [Future Work](#8-future-work)
9. [Contributors](#9-contributors)

---

## 1. Project Overview (Goals & Non-Goals)

### What the language supports
- Types: `int` (signed 64-bit), `bool`, `string` (literals only), and fixed-size arrays of these; `void` for functions.
- Functions with parameters and return values, including recursion and mutual recursion; arrays are passed to functions by reference.
- `if` / `else if` / `else`, `while`, `for`, `break`, `continue`, `return`.
- `const` variables and `const` arrays.
- Operators: `+ - * / %`, `<< >>`, `< > <= >= == !=`, `&& || !` (short-circuit), prefix `++` / `--`, assignment.
- Built-ins: `print(...)` and `readInt()`.

### Goals
- **Full pipeline visibility** — every compilation phase produces inspectable output (tokens, AST, IR, optimized IR after each pass, assembly).
- **Modularity** — each phase is a self-contained Python module with its own data structures.
- **Early, readable errors** — compilation stops at the first error. Lexer and parser errors give a line and column; semantic errors give the reason only (no position).
- **Test-driven correctness** — 186 automated tests cover the lexer, parser, semantic analyzer, IR generator, every optimization pass, and native x86-64 execution.

### Non-Goals
- Not a replacement for GCC, Clang, or LLVM.
- No standard-library or system-call support beyond `print` and `readInt` (both implemented with libc `printf` / `scanf`).
- No dynamic memory allocation (`malloc`/`free`).
- No full C ABI compliance (simplified stack-machine model for x86-64 and RISC-V).

---

## 2. Installation Procedure & Quick Start

Compiling to native code needs **Python 3** (developed and tested with 3.12), **NASM** (assembler) and **GCC** (linker). RISC-V output additionally needs `riscv64-linux-gnu-gcc` and `qemu-riscv64`.

### Option A — Linux or Windows WSL (recommended)

```bash
sudo apt update && sudo apt install -y git python3 gcc nasm
git clone https://github.com/sathvik1610/Trisynth.git ~/Trisynth
cd ~/Trisynth
python3 src/main.py tests/FinalDemo/1_fibonacci.tri
```

Expected output: `Fibonacci of 10 is:55`

> Cloning into your Linux home directory (`~`) is recommended because it is faster and avoids permission problems with bundled binaries. Running from a Windows-mounted path such as `/mnt/d/...` also works when `nasm` and `gcc` are installed inside WSL.

### Option B — Windows PowerShell with WSL (no Linux shell needed)

If Python is installed on Windows and WSL has `nasm` and `gcc`, run the compiler from PowerShell:

```powershell
python src\main.py tests\FinalDemo\1_fibonacci.tri
```

The compiler detects `wsl nasm` and automatically assembles, links and runs inside WSL. The detection call has a 5-second timeout, so if you see `No assembler toolchain found` on a cold start, run `wsl -e true` once and try again.

### Option C — Windows native (no WSL)

`nasm` **and** `gcc` (for example MinGW-w64) must both be on your `PATH`; the compiler looks them up by name and does not search the `bin\windows` folder created by `setup.bat`. RISC-V execution is not available on native Windows.

```cmd
python src\main.py tests\FinalDemo\1_fibonacci.tri
```

### Option D — Prebuilt binaries

`releases/` contains PyInstaller builds (`Trisynth-Linux.zip`, `Trisynth-Windows-WSL.zip`, `Trisynth-Windows-Native.zip`) with `setup.sh` / `setup.bat`. They are a snapshot from 14 April 2026 and do **not** include later source changes; prefer running from source. See [INSTALL.md](INSTALL.md) and [SETUP.md](SETUP.md).

### Everyday usage

```bash
python3 src/main.py <file.tri> [flags]
```

Only files ending in `.tri` are accepted (anything else is rejected with an error).

| Flag | Effect |
|---|---|
| *(none)* | Compile, assemble, link and run the program (x86-64) |
| `-v` / `--verbose` | Print every compilation phase, then run the program |
| `--tokens` | Print lexer tokens and stop |
| `--ast` | Print the Abstract Syntax Tree and stop |
| `--ir` | Print the IR and the IR after each optimization pass, then stop |
| `--asm` | Print the generated assembly for the selected `--arch` and stop |
| `--arch x86` | Target x86-64 (default) |
| `--arch riscv` | Target RISC-V 64-bit (needs Linux/WSL, `riscv64-linux-gnu-gcc` and `qemu-riscv64` to run) |
| `--arch both` | Run both targets |
| `--compare-asm` | Print the x86-64 and RISC-V assembly one after the other and stop |
| `--benchmark` | Run x86-64 natively and RISC-V under QEMU and compare timings (needs WSL/Linux with QEMU) |
| `--demo` | Read source code from standard input (finish with Ctrl+D, or Ctrl+Z then Enter on Windows) and compile it. This is also the mode used when no file is given. |

### What the compiler writes and how it reports errors
- **Output files:** every successful compile writes `output.asm` and `output_riscv.s` into the **current directory** — both backends always run, whatever `--arch` is — and a normal run also creates `output.o` and the executable (`program`, or `program.exe` on native Windows). Run the compiler from a scratch directory to keep your tree clean.
- **Error format:** lexer and parser errors are printed as `Error: ...`; semantic errors as `   Failed: ...`.
- **Exit status:** the compiler always exits with status 0, even after a compile error, and does not propagate the compiled program's own exit code.

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
| `No assembler toolchain found` | `nasm` or `gcc` is missing (or WSL was asleep: run `wsl -e true` and retry). Install them as in Option A. |
| `Fatal Compiler Error: Unrecognized file extension` | Rename the file to end in `.tri`. The old samples in `examples/` use `.nc` and also contain global variables, so they do not compile as they are. |
| `Permission denied` for a bundled `nasm` | You are on a Windows-mounted path; use a system `nasm` (`sudo apt install nasm`) or clone into `~`. |
| `python3: command not found` | `sudo apt install python3` |

---

## 3. Documentation

- [Language Manual](Language_Manual.md) — lexical rules, types, operators, statements, functions, arrays and built-ins of the language.
- [Project Report](Project_Report.md) — architecture of every stage, the IR instruction set, the optimizer and the backends.
- `docs/deliverables/` — copies of the manuals plus the installation manual, generated by `build_deliverables.py`. The `.pdf` files next to them are snapshots that are **not** regenerated by the build script and may lag behind the Markdown.

---

## 4. Developer Guide

If you want to modify Trisynth or understand its internals, run the Python source directly.

### Prerequisites

```bash
git clone https://github.com/sathvik1610/Trisynth.git
cd Trisynth
pip install -r requirements.txt     # installs pytest only
```

For native output you also need the external toolchains:

**Debian / Ubuntu / WSL:**
```bash
# x86-64 assembly
sudo apt-get install nasm gcc

# RISC-V emulation
sudo apt-get install qemu-user gcc-riscv64-linux-gnu
```

**Windows native:** install [NASM](https://www.nasm.us/) and [MinGW-w64 (GCC)](https://www.mingw-w64.org/) and put both on `PATH`. RISC-V execution works only through WSL.

### Running by hand

```bash
# 1. Compile to assembly (this also writes output.asm and output_riscv.s)
python src/main.py path/to/source.tri --asm

# 2a. Assemble and link x86-64 (Linux/WSL)
nasm -f elf64 output.asm -o output.o
gcc -no-pie output.o -o program
./program

# 2b. Assemble and link RISC-V (Linux/WSL)
riscv64-linux-gnu-gcc -static output_riscv.s -o program_riscv
qemu-riscv64 ./program_riscv
```

### Pipeline debugging flags

- **Lexer output**: `python src/main.py file.tri --tokens`
- **AST output**: `python src/main.py file.tri --ast`
- **IR and each optimization pass**: `python src/main.py file.tri --ir`
- **Assembly**: `python src/main.py file.tri --asm`
- **Everything, then run**: `python src/main.py file.tri -v`

### Where to change what

| Area | Files |
|---|---|
| Tokens and keywords | `src/frontend/token_type.py`, `src/frontend/lexer.py` |
| Grammar and AST | `src/frontend/parser.py`, `src/frontend/ast.py` |
| Type checks and scoping | `src/semantic/analyzer.py`, `src/semantic/symbol_table.py` |
| IR instruction set and lowering | `src/ir/instructions.py`, `src/ir/ir_gen.py` |
| Optimization passes | `src/optimization/` (pass order is set in `process_source` in `src/main.py`) |
| x86-64 backend | `src/backend/codegen_x86.py` |
| RISC-V backend | `src/backend/riscv/codegen_riscv.py` |
| Shared stack-slot allocator | `src/backend/common/stack_frame.py` |
| CLI, toolchain detection, debug interpreter | `src/main.py` |

---

## 5. Test Suite

The suite lives in `tests/unit/` and is run with `pytest` from the repository root. It has 186 tests and finishes in a few seconds.

| File | Tests | What it covers |
|---|---|---|
| `test_01_lexer.py` | 6 | Keywords and identifiers, operators, array brackets, invalid characters, `float`/`uint32` as plain identifiers, float literals rejected |
| `test_02_parser.py` | 9 | Assignment, operator precedence, control structures, array declarations, syntax errors, const arrays, nested function rejection, calling a non-function |
| `test_03_semantic.py` | 11 | Undeclared variables, type mismatches, missing returns, argument counts, const reassignment, const arrays, `float`/`uint32` rejected, global variables rejected |
| `test_04_ir_gen.py` | 4 | IR for arithmetic, `if`, functions and arrays |
| `test_compiler_pipeline.py` | 1 | Source → optimized IR through every stage |
| `test_opt_01_strength_reduction.py` | 6 | Multiplication/division reduction rules |
| `test_opt_02_cse.py` | 5 | Common subexpression elimination, commutativity, invalidation on redefinition, reset at control flow |
| `test_opt_03_copy_propagation.py` | 4 | Copy propagation, invalidation, reset at control flow |
| `test_opt_04_constant_folding.py` | 6 | Constant folding and branch folding |
| `test_opt_05_dce.py` | 3 | Unused variable removal, unreachable code, dead labels |
| `test_opt_06_arithmetic_semantics.py` | 128 | 64-bit wraparound, truncating division/modulo, signed division by powers of two; optimized vs unoptimized IR against a reference evaluator; native x86-64 runs |
| `test_string_literals.py` | 3 | String literals, escapes, multiple string outputs |

The native x86-64 tests in `test_opt_06_arithmetic_semantics.py` assemble and run real programs. They need `nasm` and `gcc` (through WSL on Windows) and are skipped when those are unavailable. The RISC-V backend is not executed by any automated test.

The sample programs in `tests/programs/`, `tests/FinalDemo/` and `tests/demo1`–`demo7_*.tri` are **not** run by `pytest`; they are for manual demonstration (`python src/main.py <file> [--ir]`).

```bash
python -m pytest tests -q                               # everything
python -m pytest tests/unit/test_opt_06_arithmetic_semantics.py -v
python -m pytest -k "const" -v                          # by keyword
```

### Test design
- **Per-stage unit tests** feed small inputs to one stage and assert on its output or on the raised error message.
- **Semantics regression tests** run the same program through the unoptimized and the optimized IR on a reference evaluator that implements the hardware rules (signed 64-bit wraparound, division truncating toward zero, arithmetic right shift) and compare both with known C results, including `INT_MIN`/`INT_MAX`, negative operands and overflow.

---

## 6. Design Choices

These are deliberate scope and design decisions, not accidents. Each lists what the code does and why it is reasonable for this project.

### Architecture
| Choice | What the code does | Why |
|---|---|---|
| Hand-written lexer and parser | A regex-driven lexer and a recursive-descent parser; no PLY/ANTLR/yacc | Full control of the AST and error messages, and no dependencies |
| Python standard library only | The only dependency is `pytest` for tests | Runs anywhere Python runs; compile speed is irrelevant for small programs |
| Staged pipeline | Lexer → Parser → Semantic analyzer → IR generator → Optimizer → Code generator, each stage separate | Each stage can be tested and inspected on its own (`--tokens`, `--ast`, `--ir`, `--asm`) |
| Linear three-address IR | A flat list of `Instruction(opcode, arg1, arg2, result)` with labels and jumps; no CFG, no SSA | Simple to generate, read and optimize; both backends consume the same IR |
| Assembly text as output | The backends write NASM (x86-64) and GNU `as` (RISC-V) text; NASM/GCC assemble, link and run it | No assembler, object-file writer or linker to implement |
| Stack-only code generation | Every variable and temporary lives in an 8-byte stack slot (`StackFrame`); no register allocation | Correctness and simplicity over speed |
| libc for I/O | `print` and `readInt` call `printf` / `scanf` | No system-call layer needed |
| Two backends | x86-64 and RISC-V share the IR and `StackFrame`; both are always generated on every compile | Shows the IR is target independent |

### Language
| Choice | What the code does | Why |
|---|---|---|
| `int` is signed 64-bit two's complement | Overflow wraps; `/` and `%` truncate toward zero; `>>` is arithmetic | Matches what the hardware does; the optimizer is written to preserve exactly this |
| **No postfix `x++` / `x--`** | Only prefix `++x` / `--x` exist. The parser rewrites `++x` into `x = x + 1`, whose value is the *new* value | Postfix must yield the *old* value and so needs an extra temporary; loops and statements do not need it |
| No compound assignment (`+=`, `-=` ...) | `x += 1` is a syntax error | Kept the operator set small; write `x = x + 1` |
| No bitwise `& \| ^ ~` | Only `<<` and `>>`; a single `&` or `\|` is a lexical error | Shifts are needed for strength reduction; the rest was out of scope |
| `float`, `uint32`, `char` are not usable | `float` and `uint32` are ordinary identifiers; `char` is a reserved word that the analyzer rejects (the parser has no rule for character literals) | The backends only lower integer-sized values |
| No global variables | Rejected with an error (see below) | The backends keep every variable in a function's stack frame and emit no global storage, so a global would silently give wrong results |
| No nested functions | Rejected by the parser | The IR and backends are flat: one function body per `FUNC_START` |
| Functions may be used before they are defined | The analyzer registers all functions first | Allows mutual recursion without forward declarations |
| `const` | Variables must be initialized; assignment and `++`/`--` on a `const` variable, and assignment to an element of a `const` array, are errors | Compile-time protection only (`++a[i]` on a `const` array is not checked) |
| Conditions | `if` and `while` accept `bool` or `int`; a `for` condition must be `bool` | As implemented in the analyzer |
| Short-circuit `&&` / `\|\|` | The right operand is not evaluated when the left decides the result | Standard C behaviour |
| Strings | Literals only (no concatenation, comparison or indexing); `print` of a string does not append a newline, `print` of an `int` or `bool` does | Strings exist to make demo output readable |
| Arrays | Fixed size given by an integer literal; passed to functions by reference; elements are not initialized; no bounds checking | Raw, C-like memory model |

### Optimizer
| Choice | What the code does |
|---|---|
| Six passes in a fixed order | Strength reduction → CSE → copy propagation → constant folding → CSE again → dead code elimination, run **once** in `process_source` |
| Fixed-point driver is unused by the compiler | `Optimizer` in `src/optimization/optimizer.py` repeats the passes up to 10 times until nothing changes, but only the tests use it |
| Hardware semantics in folding | Folding wraps to 64 bits, divides like C, and leaves division by zero, `INT_MIN / -1` and out-of-range shift counts to run time |
| Signed division by `2^k` | Expanded to `(x + (x < 0 ? 2^k - 1 : 0)) >> k` (a bare shift would round the wrong way for negative numbers); constant dividends are left to constant folding |

### Error handling
| Choice | What the code does |
|---|---|
| First error only | Each stage raises a plain exception at the first problem; there is no recovery and no warnings |
| Positions | Lexer errors and most parser errors give `line:column`; semantic errors do not |
| Exit status | Always 0 |

---

## 7. Known Limitations & Behaviors

### Language limitations
| Limitation | Detail |
|---|---|
| No postfix `++`/`--`, no `+=` and friends | See [Design Choices](#6-design-choices) |
| No bitwise `& \| ^ ~` | Only `<<` and `>>` |
| No `float`, `uint32` or usable `char` | See [Design Choices](#6-design-choices) |
| No global variables or global arrays | `int g = 5;` at file level fails with `E002 Semantic Error: Global variable 'g' is not supported` |
| No nested functions | Rejected by the parser |
| No pointers, structs, enums, `switch`, ternary operator or function pointers | Not part of the language |
| Array size must be an integer literal | `int a[n];` is a syntax error |
| No string operations | Only declaring, copying, passing and printing strings. `==` and `!=` are accepted but compare addresses, not characters; every other operator on a string is an error |
| `const` array protection is partial | Assigning to an element is rejected, but `++a[i]` / `--a[i]` on a `const` array is accepted |
| `main` is required | Missing entry point is error `E004` |
| Return checking is syntactic | A non-void function must contain a `return` the analyzer can see on every path (a return in the block, or an `if`/`else` whose branches both return). A `return` inside a loop does not count, so `while (true) { return 1; }` is rejected |

### Runtime behaviors
| Situation | Behavior |
|---|---|
| Array out-of-bounds | Undefined — no runtime check |
| Uninitialized locals and array elements | Undefined — whatever is on the stack |
| Integer overflow | Wraps around (signed 64-bit two's complement); folded constants follow the same rule |
| Integer literal outside the 64-bit range | Not rejected: the value is silently truncated to 64 bits and NASM prints a `numeric constant ... does not fit in 64 bits` warning |
| Division or modulo by zero | Traps at run time (SIGFPE on x86-64); never constant-folded. `INT_MIN / -1` also traps on x86-64 |
| `print` | `int` and `bool` print followed by a newline (`bool` shows `1`/`0`); a string prints with no newline |
| Deep recursion | Limited by the native process stack |
| Input and output when the compiler runs the program | Output is captured and shown after the program finishes, and standard input is not reliably forwarded (`readInt` returned 0 when run through the compiler under Windows + WSL). To give a program input, assemble it and run `./program` yourself |

### Compiler behaviors
| Situation | Behavior |
|---|---|
| First error only | The compiler stops at the first error (no error recovery) |
| Exit status | Always 0, even after a compile error |
| Output files | `output.asm`, `output_riscv.s` (and `output.o`, `program`) are written to the current directory |
| `for` loop variable scoping | The loop-init variable is visible in the loop body and update clause, and not after the loop |
| `++x` on a `const` | Caught as "Cannot assign to const" because `++x` is rewritten to `x = x + 1` |
| Optimization | One sweep of six passes; no global (CFG-based) analysis |
| RISC-V | Generated for every program, but not executed by the automated tests |
| Debug interpreter | `IRInterpreter` in `src/main.py` is a standalone helper that uses Python integer semantics; the compile path does not call it |

---

## 8. Future Work

| Enhancement | Description |
|---|---|
| Postfix `++`/`--` and compound assignment | Parse them and lower postfix through a temporary holding the old value |
| Global variables | Emit `.data`/`.bss` storage in both backends and address it from every function |
| Array bounds checking | Insert checks before every `ALOAD`/`ASTORE` |
| `char` and `float` | Add literals, type checking and lowering |
| Control Flow Graph and SSA | Enable global data-flow analysis and more aggressive optimization |
| Register allocation | Linear scan or graph coloring instead of stack slots for every variable |
| Error recovery | Continue past the first error to report several in one run |
| Diagnostics | Source positions in semantic errors and a non-zero exit status on failure |
| Fixed-point optimization | Use the existing repeat-until-stable `Optimizer` driver in the compiler |
| Inlining and interprocedural constant propagation | Across function boundaries |

---

## 9. Contributors

| Name | ID |
|---|---|
| V. Chitraksh | CS23B054 |
| P. Sathvik | CS23B042 |
| S. Danish Dada | CS23B047 |

---

*Trisynth — A Compiler Built to Be Read.*
