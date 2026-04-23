# Trisynth Compiler

**Trisynth** is a custom-built native compiler for **NanoC**, a minimal C-like language designed as a complete, pedagogically clear compiler construction reference.  
It compiles NanoC source through every classical stage — Lexing → Parsing → Semantic Analysis → IR Generation → Optimization → Native Code (x86-64 & RISC-V) — exposing each phase's internal representation and error reporting.

> [!NOTE]
> **Academic Disclaimer**: Trisynth is built to demonstrate compiler theory. Design decisions consistently choose *readability and correctness* over *performance and completeness*.

---

## Table of Contents

1. [Project Overview (Goals & Non-Goals)](#1-project-overview-goals--non-goals)
2. [Installation Procedure & Quick Start](#2-installation-procedure--quick-start)
3. [Documentation](#3-documentation)
4. [Test Suite](#4-test-suite)
5. [Limitations & Known Behaviors](#5-limitations--known-behaviors)
6. [Future Work](#6-future-work)
7. [Contributors](#7-contributors)

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

Trisynth provides cross-platform support for Linux, Windows with WSL, and native Windows. For detailed, step-by-step setup instructions and troubleshooting, please refer to our **Installation Manuals**:

- [Installation Manual (PDF)](docs/deliverables/Installation_Manual.pdf)
- [Installation Manual (Markdown)](docs/deliverables/Installation_Manual.md)

Alternatively, see the [INSTALL.md](INSTALL.md) and [SETUP.md](SETUP.md) quick guides.

### Step 1 — Download the Right Release

| Platform | Download |
|---|---|
| Linux | `Trisynth-Linux.zip` |
| Windows with WSL | `Trisynth-Windows-WSL.zip` |
| Windows (no WSL) | `Trisynth-Windows-Native.zip` |

### Step 2 — Setup

**Linux / WSL:**
```bash
# ⚠️ WSL users: extract to your Linux home directory, NOT /mnt/c/...
unzip Trisynth-Windows-WSL.zip -d ~/Trisynth
cd ~/Trisynth
bash setup.sh
```

**Windows Native:**
```
Double-click setup.bat
```

### Step 3 — Compile and Run

**Linux / WSL:**
```bash
./trisynth demo2_strength_reduction.tri
./trisynth demo4_array.tri
./trisynth yourfile.tri
```

**Windows Native:**
```cmd
trisynth.exe yourfile.tri
```

### Compilation Flags

| Flag | Effect |
|---|---|
| *(none)* | Compile and run silently |
| `-v` / `--verbose` | Print all pipeline phases |
| `--tokens` | Print tokens and stop |
| `--ast` | Print AST and stop |
| `--ir` | Print IR + optimization passes and stop |
| `--asm` | Print generated assembly and stop |
| `--arch x86` | Target x86-64 (default) |
| `--arch riscv` | Target RISC-V 64-bit (Linux/WSL only) |
| `--arch both` | Compile both architectures |
| `--compare-asm` | Show x86 and RISC-V assembly side by side |
| `--benchmark` | Benchmark x86 vs RISC-V (QEMU) |
| `--demo` | Interactive REPL mode |

### Sample Program
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

## 4. Test Suite

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

## 5. Limitations & Known Behaviors

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

## 6. Future Work

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

## 7. Contributors

| Name | ID |
|---|---|
| V. Chitraksh | CS23B054 |
| P. Sathvik | CS23B042 |
| S. Danish Dada | CS23B047 |

---

*Trisynth — A Compiler Built to Be Read.*
