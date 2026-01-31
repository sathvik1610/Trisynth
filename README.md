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
*   **Control Flow**: `if/else`, `while`, `for`, `break`, `continue`. (Note: No `switch` or `goto`).
*   **Functions**: Recursive, pass-by-value, no overloading. Supports **Hoisting** (Forward Declarations).
*   **Data Structures**: 
    *   **Arrays**: Fixed-size homogeneous arrays (e.g., `int arr[10]`). 
    *   *Constraint*: No pointers, no dynamic allocation (`malloc`).
*   **Safety**:
    *   **Immutable Constants**: `const` keyword strictly enforced.
    *   **Operators**: `++`, `--` provided as valid syntax sugar.

#### Intermediate Representation (IR)
*   **Design**: Linear Three-Address Code (TAC).
*   **Trade-off**: We chose linear IR over SSA (Static Single Assignment) to reduce implementation complexity while still allowing for fundamental optimizations.

---

## 4. Optimization Strategy & Design Philosophy

Trisynth implements **conservative, semantics-preserving optimizations** over a linear Intermediate Representation (IR). The goal is to demonstrate classical compiler techniques while avoiding transformations that require complex control-flow or interprocedural analysis.

### Implemented Optimizations

**1. Constant Folding & Propagation**

* Evaluates arithmetic expressions with **compile-time constant operands**.
* Example:
  ```
  (10 * 10 + 44) / 12 → 12
  ```
* Folding is performed **only when all operands are literals**.
* **Constant Propagation**: Substitutes known constant values across basic blocks (safely guarded by labels).
* No algebraic simplification involving variables (e.g., `x + 0`).

**2. Dead Code Elimination (DCE)**

* Removes computations whose results are never used.
* Primarily targets **compiler-generated temporaries (`tX`)**.
* Instructions with side effects (`PRINT`, `CALL`, `ASTORE`, `RETURN`) are never removed.

### Optimization Constraints (Very Important)

To ensure correctness, the optimizer enforces strict safety rules:

* No optimizations are applied across loop boundaries (Basic Block Isolation).
* Loop induction variables are never folded or removed.
* Branch conditions are preserved unless provably constant within the block.
* Memory operations (`ALOAD`, `ASTORE`) are treated as side-effecting.
* No instruction referenced by a jump or label is removed.

These constraints prevent unsafe transformations in the absence of a Control Flow Graph (CFG).

---

## 5. Limitations & Trade-offs (Detailed)

This section explicitly lists what is *not* supported and why, to manage expectations.

### A. Language Features
*   **Arrays**: 
    *   Must have compile-time fixed size (`int x[10]`).
    *   No dynamic arrays.
    *   No pointer arithmetic (`*(p+1)` is not supported).
    *   Passed by reference logic in IR (pointer), but syntax is restricted.
*   **Structs/Classes**: No user-defined types.
*   **Floating Point**: `float` is a reserved keyword but full backend support is limited to integer arithmetic in this phase.

### B. Safety & Runtime
*   **No Bounds Checking**: Accessing `arr[100]` for a size-10 array **will compile** and generate an `ASTORE` instruction. At runtime, this leads to undefined behavior (memory corruption). We rely on the programmer to check bounds.
*   **No Garbage Collection**: Stack allocation only.
*   **No Null Safety**: Variables are generally initialized, but uninitialized reads are undefined.
*   **Error Handling**: The compiler operates in "panic mode" — it halts execution at the **first** syntax or semantic error encountered.

### C. Backend & Optimization Details
*   **Instruction Set**: Simplified set (ADD, SUB, JMP, ALOAD, ASTORE, etc.).
*   **Global DCE**: Not implemented. Unused function definitions are *not* stripped from the output.
*   **Register Allocation**: Simple strategy (spilling to stack) rather than graph-coloring allocation.
*   **Built-ins**: 
    *   `print(expr)`: Output integer to stdout.
    *   `readInt()`: Input integer from stdin (stubbed in analysis).

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
*   **Runtime Bounds Checks**: Injecting `check_bounds` instructions before `ALOAD`/`ASTORE`.
*   **SSA Conversion**: For more aggressive optimizations.
*   **Control Flow Graph (CFG)**: To enable global data-flow analysis.
*   **Register Allocation**: Implementing Linear Scan or Graph Coloring.

---

## Contributors

* V. Chitraksh (CS23B054)
* P. Sathvik (CS23B042)
* S. Danish Dada (CS23B047)
