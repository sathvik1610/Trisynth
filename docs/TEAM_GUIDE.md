# Trisynth Compiler — Viva & Architecture Guide

Welcome to the Trisynth internal guide. This document breaks down the compiler's entire pipeline. It is designed to be **simple, crisp, and technical**, providing the exact concepts you need to explain **how** and **why** the compiler works during a viva or presentation.

---

## 1. Lexical Analysis (The Lexer)
**Goal:** Convert raw source text into a stream of meaningful "Tokens" (words).
**File:** `src/frontend/lexer.py`

*   **How it works:** It uses **Regular Expressions (Regex)** to match text. We use a **"Maximal Munch"** strategy, meaning the scanner always tries to match the longest possible valid string (e.g., `==` is matched before `=`).
*   **Concepts to explain:**
    *   **Tokens:** A token is an object containing `(Type, String Value, Line, Column)`. For example, `Token(INTEGER, "52", 1, 10)`.
    *   **Ignoring Whitespace/Comments:** Text like `//` or `/* */` is caught by specific regex rules and explicitly bypassed instead of creating tokens.
    *   **Lexical Error:** Thrown when a character doesn't match any known pattern (e.g., an illegal symbol like `@`).

## 2. Syntax Analysis (The Parser)
**Goal:** Verify that the tokens follow the language's grammar and build an Abstract Syntax Tree (AST).
**File:** `src/frontend/parser.py`

*   **How it works:** We implemented a **Recursive Descent Parser**. It is a top-down approach where each grammar rule (like an `if` statement or a mathematical expression) has its own corresponding Python function.
*   **Concepts to explain:**
    *   **AST (Abstract Syntax Tree):** A hierarchical graph where nodes represent operations (like `Add`) and children represent operands (like `x` and `5`).
    *   **Operator Precedence:** Handled inherently by how the functions call each other. `parse_addition()` calls `parse_multiplication()`, forcing multiplication to be evaluated deeper in the tree (first).
    *   **Why not YACC/Bison?** Writing our own Recursive Descent parser gives us 100% control over the AST structure and allows for much better, custom syntax error messages (e.g., "Expected ';' at line 5").

## 3. Semantic Analysis (Type Checking & Scoping)
**Goal:** Ensure the code makes *logical* sense. It answers: "Does this variable exist?" and "Are these types compatible?".
**File:** `src/semantic/analyzer.py`

*   **How it works:** It performs a single pass over the AST. As it enters a block `{...}`, it creates a new scope. As it exits, it destroys it.
*   **Concepts to explain:**
    *   **Symbol Table:** A stack of dictionaries (Hash Maps) where we store declared variables. When looking up a variable like `x`, we check the local scope first, then move up to the parent/global scope.
    *   **Type Evaluation:** If the AST says `x = 5 + "hello"`, the semantic analyzer checks the types mathematically and throws an `E002: Type Mismatch` error before the compiler tries to generate logic for it.
    *   **The Immutability Firewall (`const`):** The analyzer tracks if a symbol is marked `const`. Any `Assignment` node attempting to overwrite it throws an explicit semantic error.

## 4. Intermediate Representation (IR Generation)
**Goal:** Flatten the complex, nested AST into a linear list of simple instructions that are easy to optimize and translate to hardware.
**File:** `src/ir/ir_gen.py`

*   **How it works:** It flattens tree nodes into **Three-Address Code (TAC)**. Each instruction has at most three operands: `operation, arg1, arg2, result`. 
*   **Concepts to explain:**
    *   **Why IR?** Without IR, we'd have to write separate optimizers for x86 and RISC-V. IR provides a universal middle-ground.
    *   **Register/Variable Renaming:** To prevent scope clashes in this flat structure, we append unique counters to variable names (e.g., local variable `x` becomes `x_1`). Temporary results are assigned to pseudo-registers like `t0`, `t1`.
    *   **Short-Circuit Logic:** For `A && B`, it translates into explicit jumps (`JMP_IF_FALSE a, L_exit`), guaranteeing that `B` is never executed if `A` evaluates to false natively.

## 5. Optimization Passes
**Goal:** Make the IR code smaller and faster before turning it into Assembly.
**File:** `src/optimization/`

*   **How it works:** Specialized, independent passes loop over the IR instructions modifying them based on mathematical rules.
*   **Concepts to explain (The Big Three):**
    1.  **Constant Folding:** If the IR has `ADD t0 3 4`, the optimizer immediately replaces it with `MOV t0 7`. This happens entirely at compile-time.
    2.  **Strength Reduction:** Replaces heavy mathematical operations with cheaper hardware equivalents. For example, `MUL t0 x 4` is swapped out mathematically for a Bitwise Left Shift `LSHIFT t0 x 2`.
    3.  **Dead Code Elimination (DCE):** Scans parameters linearly to mark "used" variables. Any pure calculation whose resulting register is never used is completely removed.

## 6. Code Generation (The Backends)
**Goal:** Translate the optimized IR into native physical hardware instructions for x86-64 and RISC-V.
**Files:** `src/backend/codegen.py` and `codegen_riscv.py`

*   **How it works:** It acts as a **Stack Machine**. We don't implement complex Register Graph Coloring. Instead, practically everything is allocated onto the physical memory stack structure securely.
*   **Concepts to explain:**
    *   **Stack Frame:** We use the base/frame pointer (`rbp` in x86, `s0` in RISC-V). Every variable gets assigned fixed byte offsets on the stack (e.g., `[rbp - 8]`).
    *   **System V ABI Alignment:** x86 requires the Stack Pointer (`rsp`) to be aligned perfectly to 16 bytes before calling an external C function like `printf`. We calculate offsets and align `rsp` dynamically, preventing OS segmentation faults.
    *   **RISC-V Comparisons:** Unlike x86 which uses a hidden "Flags" register (`cmp / je`), RISC-V utilizes explicit evaluation registers cleanly mapping checks into variables natively (`slt t0, a, b`).
    *   **No Abstract Monoliths:** Explain that by generating our own NASM strings physically, we eliminate reliance on massive tools like LLVM. This results in unmatched transparency in understanding how memory layouts are mapped!

---

### Key Takeaway for Viva:
If asked *"What makes Trisynth unique?"*: 
State that **Trisynth handles its entire pipeline locally**. It isn't just a parser feeding LLVM; it fundamentally translates complex syntaxes into generic pseudo-IR, optimizes mathematically, allocates memory cleanly through its own natively developed stack frame manager, and dynamically bounds Assembly offsets across multiple completely different OS architectures (`x86 Linux` vs `RISC-V 64 GNU`).
