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

Trisynth prioritizes **semantic correctness** and **conservative optimization** over aggressive performance tuning. The compiler avoids transformations needing data-flow analysis, CFG construction, or SSA form.

### Implemented Optimizations

**1. Scope-Aware Constant Folding & Propagation**
*   Evaluates arithmetic expressions with **compile-time constant operands**.
*   **Scope Sensitivity**: Inner-scope variables may be folded independently of outer shadowed variables. (No global propagation).
*   **Constraints**: Works only when all operands are literals within the basic block. No algebraic simplification (e.g. `x+y-y` is not simplified).

**2. Dead Code Elimination (DCE)**
*   Removes computations whose results are never used.
*   **Conservative**: Only unused compiler-generated temporaries (`tX`) are guaranteed removed. Instructions with side effects (`PRINT`, `CALL`, `ASTORE`, `RETURN`) are strictly preserved.

**3. Strength Reduction**
*   Replaces expensive arithmetic with cheaper operations:
    *   Multiplication by powers of two (`i * 4` → `i << 2`)
    *   Division by powers of two (`k / 2` → `k >> 1`)
    *   Zero Multiplication (`x * 0` → `0`)
*   **Assumptions**: Integer arithmetic, non-negative operands (logical shift behavior for unsigned).

### Safety Guard: Control Flow Isolation
To prevent unsafe transformations without a CFG:
*   **Loop Safety**: Loop induction variables are never folded or removed. Loops are effectively "black boxes" to the constant propagator.
*   **Branch Preservation**: `while(true)` is lowered to `JMP_IF_FALSE 1 ...` but termination relies entirely on explicit `break`. No static termination analysis is performed.

---

## 5. Limitations & Trade-offs (Detailed)

This section explicitly lists what is *not* supported and why, to manage expectations.

### A. Language Features
*   **Arrays**: 
    *   Must have compile-time fixed size (`int x[10]`).
    *   No dynamic arrays.
    *   Passed by reference logic in IR (pointer), but syntax is restricted.
*   **Structs/Classes**: No user-defined types.
*   **Floating Point**: `float` is a keyword but backend support is limited to integer logic currently.
*   **Numeric Literals**: All integer literals are treated as **base-10**. Leading zeros do not imply octal.

### B. Safety & Runtime
*   **No Bounds Checking**: Accessing `arr[100]` for a size-10 array **will compile**. At runtime, this leads to undefined behavior.
*   **No Garbage Collection**: Stack allocation only.
*   **No Null Safety**: Uninitialized reads are undefined.
*   **Error Handling**: The compiler operates in "panic mode" — it halts execution at the **first** error.

### C. Backend & IR Structural Limits
*   **Dual Architecture Support**: x86-64 (Implemented) and RISC-V (Planned).
*   **Execution Model**: Stack-Machine. All variables live on the stack. No register allocation.
    *   **x86-64**: Uses `rbp` frame pointer. Arguments passed on stack (Right-to-Left). System V ABI aligned.
*   **Linear IR**: Not SSA-based. Redundant jumps may exist (no jump threading).
*   **No Function Optimization**: No inlining, no interprocedural analysis. Recursive functions are opaque boundaries.
*   **Instruction Set**: Simplified set (ADD, SUB, JMP, ALOAD, **LSHIFT**, **RSHIFT**, etc.).

> [!WARNING]
> **ABI & Runtime Limitations**:
> The x86-64 backend follows a simplified stack-machine model for clarity. It does not fully implement the System V ABI, by design.
> *   **Stack Alignment**: Alignment before external calls (e.g., `printf`) is not strictly enforced during argument pushing.
> *   **Registers**: Callee-saved registers (e.g., `rbx`) are utilized as temporaries but not preserved/restored.
>
> These trade-offs were chosen to keep the backend readable and focus on IR lowering. The design is correct for the educational scope but should be extended for full ABI compliance in production use.

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
Run the `pytest` suite verification (38 Tests covering all phases).
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
