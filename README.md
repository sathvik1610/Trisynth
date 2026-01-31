# Trisynth Compiler

**Trisynth** is a custom-built native compiler for **NanoC**, a minimal C-like programming language designed for educational purposes.  
This project focuses on demonstrating the complete compiler pipeline, from source code analysis to native code generation.

> [!NOTE]
> **Academic Disclaimer**: Trisynth is a pedagogical compiler built as part of an academic project. Design decisions prioritize understandability and correctness over completeness and performance.

---

## 1. Project Scope & Intent

The primary goals of Trisynth are:
*   **Educational**: To serve as a clear reference implementation for compiler construction concepts.
*   **Full Pipeline**: To demonstrate every stage from Lexing -> Parsing -> Semantics -> IR -> Optimization -> CodeGen.
*   **Modularity**: To keep each phase distinct and testable (e.g., Lexer and Parser are independent modules).
*   **Transparency**: To favor readable algorithms (e.g., recursive descent) over complex, highly optimized ones.

---

## 2. Non-Goals

To maintain focus and manage complexity, explicitly **we are NOT aiming for**:
*   A replacement for GCC or LLVM.
*   Real-world performance benchmarks.
*   Compilation of large-scale or safety-critical software.
*   Full C standard compatibility (ABI or syntax).

---

## 3. Architecture & Implementation

Trisynth follows a classical multi-pass architecture:

```
Source Code (NanoC) -> Lexer -> Parser -> AST -> Semantic Analyzer -> IR Gen -> Optimizer -> CodeGen -> Assembly
```

### Key Components

#### Language Design (NanoC)
*   **Type System**: Statically typed (`int`, `bool`, `void`) with no implicit conversions.
*   **Control Flow**: `if/else`, `while`, but no `switch` or `goto` to simplify CFG construction.
*   **Functions**: Recursive, pass-by-value, no overloading.

#### Intermediate Representation (IR)
*   **Design**: Linear Three-Address Code (TAC).
*   **Trade-off**: We chose linear IR over SSA (Static Single Assignment) to reduce implementation complexity while still allowing for fundamental optimizations.

#### Optimization Strategy
We implement conservative, local optimizations to ensure semantic safety:
*   **Constant Folding**: Folds literal expressions (e.g., `1 + 2` -> `3`). Does *not* fold variables to avoid complexity.
*   **Dead Code Elimination**: Iteratively removes instructions defining unused temporary variables. User variables are generally preserved to maintain observability unless strict local conditions are met.

---

## 4. Limitations & Trade-offs

### Memory & Runtime
*   **No Heap**: No `malloc`/`free`. Stack allocation only.
*   **No Garbage Collection**: Not needed for the current scope.
*   **Safety**: No runtime bounds checking or overflow protection.

### IR & Backend
*   **Instruction Set**: Simplified set (ADD, SUB, JMP, etc.) sufficient for NanoC but not exhaustive.
*   **Register Allocation**: Simple strategy (spilling to stack) rather than graph-coloring allocation.

### Error Handling
*   **Panic Mode**: Compilation stops at the first critical error.
*   **Diagnostics**: Focus on location (line/col) rather than recovery suggestions.

### Security
*   **Constraint**: The compiler is not hardened against malformed inputs and provides no sandboxing for generated code.

---

## 5. Technology Stack

- **Implementation Language:** Python 3 (Chosen for readability and rapid prototyping).
- **Target Architectures:** x86-64 / RISC-V.
- **Assembler:** NASM or GNU Assembler (GAS).
- **Operating System:** Linux / Windows (Cross-platform python logic).

---

## 6. How to Run

### Interactive Mode
Run the compiler shell to type code and see all phases (Tokens -> AST -> Semantics -> IR -> Optimization).
```bash
python -m src.main
```

### File Mode
Compile a source file.
```bash
python -m src.main path/to/source.nc
```

### Automated Tests
Run the `pytest` suite verification.
```bash
python -m pytest
```

---

## 7. Future Work

While not in the current scope, future extensions could include:
*   **SSA Conversion**: For more aggressive optimizations.
*   **Control Flow Graph (CFG)**: To enable global data-flow analysis.
*   **Register Allocation**: Implementing Linear Scan or Graph Coloring.
*   **New Backends**: Support for LLVM IR output.

---

## Contributors

* V. Chitraksh (CS23B054)
* P. Sathvik (CS23B042)
* S. Danish Dada (CS23B047)
