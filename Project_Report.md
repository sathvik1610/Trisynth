# Project Report

**Project Title:** Trisynth — Design and Implementation of a Custom Programming Language and Multi-Target Compiler  
**Date:** April 2026

---

## Abstract

This report documents the complete design and implementation of Trisynth, a statically typed, imperative programming language together with its accompanying multi-pass compiler. The compiler is implemented in Python and translates Trisynth source programs through a well-defined six-stage pipeline: lexical analysis, parsing into an Abstract Syntax Tree, semantic analysis and type checking, three-address intermediate representation (IR) generation, IR-level optimization, and native x86-64 assembly code generation targeting the NASM assembler. The language supports integer and boolean scalar types, strings, fixed-size arrays, function declarations (including forward-referenced and recursive functions), and structured control flow. Five distinct optimization passes are applied at the IR level prior to code emission. The resulting assembly is linked against the system C standard library (`libc`) to obtain a fully executable binary. The project demonstrates a complete, end-to-end compilation pipeline without dependence on an existing compiler back-end framework.

---

## 1. Introduction

Writing a compiler requires integrating several classical sub-disciplines of computer science: formal language theory, automata, data-flow analysis, and systems programming. The Trisynth project designs a language from scratch and builds all compilation stages independently.

The language is named *Trisynth* to reflect its three core design goals: tight type safety, expressive yet terse syntax, and multi-target synthesis. The compiler is capable of producing x86-64 NASM assembly and includes a RISC-V back-end scaffolded for future expansion.

This report is organized to mirror the structure of the compiler itself. Each section corresponds directly to a compiler phase and references the relevant Python module in the `src/` directory.

---

## 2. Problem Statement

Existing educational compiler projects often rely on established intermediate representations (LLVM IR, JVM bytecode) or grammar frameworks (PLY, ANTLR) to reduce implementation effort. While pragmatic, this approach insulates students from the algorithmic core of compilation.

The problem addressed by Trisynth is the end-to-end implementation of a compiler without such dependencies: every stage — tokenization, recursive-descent parsing, scope-aware semantic analysis, three-address IR generation, dataflow-guided optimization, and register-agnostic assembly emission — is constructed explicitly in Python. The compiler must enforce strong static types, support first-class function declarations in any order (hoisting), and produce correct x86-64 object code linked against `printf` and `scanf`.

---

## 3. System Architecture

### 3.1 Overall Design

The Trisynth compiler is a batch, ahead-of-time compiler with a strictly layered architecture. Source code flows through the pipeline in a single forward pass with no back-patching between stages. Each stage communicates with the next through a well-defined data structure.

```
Source File (.nc)
       │
       ▼
┌─────────────┐
│    Lexer    │  src/frontend/lexer.py
└──────┬──────┘
       │  List[Token]
       ▼
┌─────────────────────┐
│   Recursive-Descent │  src/frontend/parser.py
│        Parser       │
└──────────┬──────────┘
           │  AST (Program node)
           ▼
┌──────────────────────┐
│  Semantic Analyzer   │  src/semantic/analyzer.py
│  + Symbol Table      │  src/semantic/symbol_table.py
└──────────┬───────────┘
           │  Validated AST
           ▼
┌──────────────────────┐
│    IR Generator      │  src/ir/ir_gen.py
└──────────┬───────────┘
           │  List[Instruction] (3-address code)
           ▼
┌──────────────────────┐
│   Optimizer Suite    │  src/optimization/
│  (5 passes)          │
└──────────┬───────────┘
           │  Optimized IR
           ▼
┌──────────────────────┐
│   x86-64 Code Gen    │  src/backend/codegen_x86.py
└──────────┬───────────┘
           │  NASM Assembly (.asm)
           ▼
    NASM + ld/gcc → ELF Binary
```

### 3.2 Compiler Pipeline Summary

| Stage | Input | Output | Module |
|---|---|---|---|
| Lexical Analysis | Raw source text | `List[Token]` | `lexer.py`, `token_type.py` |
| Parsing | Token stream | `Program` AST | `parser.py`, `ast.py` |
| Semantic Analysis | AST | Annotated AST | `analyzer.py`, `symbol_table.py` |
| IR Generation | Annotated AST | `List[Instruction]` | `ir_gen.py`, `instructions.py` |
| Optimization | IR | Reduced IR | `optimization/` |
| Code Generation | Optimized IR | x86-64 NASM text | `codegen_x86.py` |

---

## 4. Language Design

### 4.1 Syntax and Semantics

Trisynth adopts a C-family surface syntax to lower the learning curve while enforcing stronger static guarantees. Every variable must be declared with an explicit type before use; implicit conversions are not permitted. Function bodies must end with an explicit `return` statement on all code paths when the return type is non-`void`.

The language uses semicolons as statement terminators and curly braces for block delimiters. Comments follow C conventions: `//` for line comments and `/* ... */` for block comments. Source files carry the `.nc` extension.

### 4.2 Design Decisions

**Hoisting over declaration order.** Unlike C, Trisynth performs a two-pass semantic analysis traversal of the program's top-level declaration list. During the first pass, all function signatures are registered in the symbol table. During the second pass, function bodies are validated. This allows a function defined textually after its call site to be resolved correctly without forward declarations.

**No implicit type promotion.** All binary expressions require both operands to carry identical types. The semantic analyzer raises a `Type Error` if types diverge, enforcing discipline without runtime overhead.

**Const immutability enforcement.** Variables declared with the `const` qualifier are tracked in the symbol table with an `is_const` flag. Any assignment or increment/decrement targeting a `const` symbol is rejected at the semantic stage, not at runtime.

**Comparison operators produce `bool`.** Binary relational operators (`<`, `>`, `==`, `!=`, `<=`, `>=`) return type `bool` from the semantic analyzer. Control-flow constructs accept both `bool` and `int` as valid condition types.

**String immutability.** Strings are treated as read-only pointer operands pointing to data-section labels. String equality (`==`, `!=`) is lexically unsupported on string-typed values at the semantic level; the analyzer raises an `E002` error for any other operator applied to strings.

---

## 5. Compiler Implementation

### 5.1 Lexical Analysis

**Module:** `src/frontend/lexer.py`  
**Token definitions:** `src/frontend/token_type.py`

The `Lexer` class scans source text character-by-character using Python's `re` module in maximal-munch order. A prioritized list of `(pattern, TokenType)` pairs is evaluated at each position via `re.match`, which anchors the pattern at the current offset without consuming characters ahead. When a pattern matches, the token is constructed with its type, lexeme, line number, and column number; the position cursor is advanced accordingly.

Block comments are handled as a special case before the general pattern list by directly scanning for the `*/` terminator, raising a `LexicalError` for unclosed comments. String literals are stripped of their enclosing quotation marks at tokenization time, storing only the inner content in the `Token.value` field.

The keyword dictionary maps reserved words (e.g., `if`, `while`, `const`, `string`) to dedicated `TokenType` members rather than treating them as identifiers, ensuring the parser never needs keyword-disambiguation logic.

**Token categories defined:**

| Category | Examples |
|---|---|
| Literals | `INTEGER`, `FLOAT`, `STRING`, `CHAR` |
| Keywords (types) | `KW_INT`, `KW_UINT32`, `KW_BOOL`, `KW_STRING`, `KW_VOID`, `KW_CONST` |
| Keywords (control) | `KW_IF`, `KW_ELSE`, `KW_WHILE`, `KW_FOR`, `KW_BREAK`, `KW_CONTINUE`, `KW_RETURN` |
| Keywords (I/O) | `KW_PRINT`, `KW_READ_INT`, `KW_TRUE`, `KW_FALSE` |
| Arithmetic | `PLUS`, `MINUS`, `STAR`, `SLASH`, `MODULO`, `LSHIFT`, `RSHIFT` |
| Relational | `EQ`, `NEQ`, `LT`, `GT`, `LTE`, `GTE` |
| Logical | `AND`, `OR`, `NOT` |
| Punctuation | `LPAREN`, `RPAREN`, `LBRACE`, `RBRACE`, `LBRACKET`, `RBRACKET`, `SEMICOLON`, `COMMA` |
| Special | `EOF`, `ERROR` |

### 5.2 Parsing Strategy and AST

**Module:** `src/frontend/parser.py`, `src/frontend/ast.py`

The parser is a hand-written, recursive-descent parser with no external parser-generator dependency. It accepts the flat token stream produced by the lexer and builds a typed Abstract Syntax Tree. The grammar is structured so that operator precedence is encoded by nested function calls: higher-precedence operators are resolved deeper in the call stack.

**Expression precedence hierarchy (lowest to highest):**

```
Assignment  (=)
Logical OR  (||)
Logical AND (&&)
Equality    (== !=)
Relational  (< > <= >=)
Additive    (+ -)
Multiplicative (* / %)
Shift       (<< >>)
Unary       (! - ++ --)
Primary     (literals, identifiers, function calls, array access, parenthesized expressions)
```

**AST Node taxonomy:**

| Category | Nodes |
|---|---|
| Expressions | `Literal`, `StringLiteral`, `Variable`, `ArrayAccess`, `BinaryExpr`, `UnaryExpr`, `LogicalExpr`, `Assignment`, `ArrayAssignment`, `CallExpr` |
| Statements | `ExprStmt`, `PrintStmt`, `VarDecl`, `ArrayDecl`, `Block`, `IfStmt`, `WhileStmt`, `ForStmt`, `BreakStmt`, `ContinueStmt`, `ReturnStmt`, `FunctionDecl` |
| Program | `Program` |

Every AST node extends the abstract base `ASTNode`, which requires a `__repr__` method. This design enables debugging by printing the full tree structure without a separate visitor.

### 5.3 Semantic Analysis

**Module:** `src/semantic/analyzer.py`, `src/semantic/symbol_table.py`

The `SemanticAnalyzer` traverses the validated AST using the Visitor pattern. A `method_name = f'visit_{type(node).__name__}'` dispatch table routes each node to its specific handler.

**Responsibilities:**

1. **Two-pass function hoisting.** The first sub-pass over `Program.declarations` registers every `FunctionDecl` name and return type in the global scope. The second sub-pass processes function bodies. This ensures that a call to a not-yet-defined function does not generate an `undeclared` error.

2. **Scoped symbol table.** The symbol table is implemented as a stack of dictionaries (`scopes`). Entering a block pushes a new scope; exiting pops it. Variable resolution walks the stack from innermost to outermost, implementing lexical scoping.

3. **Type checking.** Every expression node returns a type string (`'int'`, `'bool'`, `'string'`, `'int[]'`, etc.). Binary expressions check that both operands share a type. Function calls verify argument count and per-argument type against the recorded `param_types`.

4. **Const enforcement.** Any assignment or increment targeting a symbol with `is_const=True` raises `Semantic Error: Cannot assign to const variable`.

5. **Return path validation.** The `_body_has_return()` helper recursively inspects a function body to confirm that all non-`void` functions contain a `return` statement on every control-flow path.

6. **Entry-point requirement.** After processing all declarations, the analyzer verifies that a function named `main` exists; its absence raises `E004 Semantic Error`.

### 5.4 Intermediate Representation

**Module:** `src/ir/ir_gen.py`, `src/ir/instructions.py`

The IR is a linear sequence of `Instruction` objects, each holding an `OpCode` enum member and up to three operand fields (`arg1`, `arg2`, `result`). This corresponds to the classical three-address code (TAC) form used in textbook compiler theory.

**IR OpCode groups:**

| Group | OpCodes |
|---|---|
| Data movement | `MOV`, `LOAD_STR` |
| Arithmetic | `ADD`, `SUB`, `MUL`, `DIV`, `MOD`, `LSHIFT`, `RSHIFT` |
| Comparison | `LT`, `GT`, `LTE`, `GTE`, `EQ`, `NEQ` |
| Control flow | `LABEL`, `JMP`, `JMP_IF_FALSE` |
| Functions | `FUNC_START`, `FUNC_END`, `RETURN`, `CALL`, `PARAM`, `LOAD_PARAM` |
| Arrays | `ARR_DECL`, `ALOAD`, `ASTORE`, `PARAM_REF`, `LOAD_PARAM_REF` |
| I/O | `PRINT`, `PRINT_STR` |

The `IRGenerator` uses a scope stack (mirroring the semantic analyzer's structure) to rename every declared variable to a globally unique name (e.g., `x_3`), eliminating shadowing ambiguity in the flat IR sequence. Temporary variables are allocated with sequential names `t0`, `t1`, …, and labels with `L0`, `L1`, ….

**Short-circuit evaluation.** Logical `&&` and `||` operators are translated into conditional jump sequences rather than simple binary instructions, preserving correct short-circuit semantics: the right operand is only evaluated if needed.

**Sample IR (corresponding to `int x = (10 * 10 + 44) / 12;`):**

```
MUL  t0  10  10
ADD  t1  t0  44
DIV  t2  t1  12
MOV  x_0  t2
```

### 5.5 Optimizations

**Module:** `src/optimization/`

Five optimization passes are applied to the IR list after generation and before code emission. Each pass is a standalone function accepting and returning a `List[Instruction]`.

**Pass 1 — Constant Folding (`constant_fold.py`).** Evaluates arithmetic and comparison instructions whose operands are both compile-time integer constants, replacing the instruction with a direct `MOV` of the computed result. For example, `MUL t0 10 10` → `MOV t0 100`.

**Pass 2 — Copy Propagation (`copy_propagation.py`).** After a `MOV dest src`, subsequent uses of `dest` are replaced by `src` (when `src` is a constant or an unmodified variable), reducing unnecessary data movement.

**Pass 3 — Common Subexpression Elimination (`cse.py`).** A hash-map tracks previously computed `(opcode, arg1, arg2)` tuples. If the same expression is computed again and neither operand has been modified, the recomputation is replaced with a `MOV` from the previously computed temporary.

**Pass 4 — Dead Code Elimination (`dead_code.py`).** Marks temporaries that are never used as operands and removes the instructions that produce them. Also removes unreachable instructions following an unconditional `JMP` up to the next `LABEL`.

**Pass 5 — Strength Reduction (`strength_reduction.py`).** Replaces computationally expensive operations with cheaper equivalents; for instance, multiplication or division by a compile-time power-of-two is converted to a left or right arithmetic shift.

### 5.6 Code Generation (x86-64)

**Module:** `src/backend/codegen_x86.py`

The `X86Generator` class translates the optimized IR into NASM-syntax x86-64 assembly. The code generator operates function-by-function: for each function, it first performs a pre-pass over the function's instruction list to collect all variable and temporary names, allocates each to a unique stack offset within a `StackFrame` object, and then emits the corresponding x86-64 instruction sequence.

**Calling convention.** Trisynth uses a stack-based calling convention: arguments are pushed right-to-left before a `call` instruction, and the callee pops the caller's frame pointer using the standard `push rbp / mov rbp, rsp` prologue. Parameters are retrieved from `[rbp + 16 + i*8]`. Return values are passed in `rax`.

**Array references.** Fixed-size arrays are allocated directly on the stack as contiguous 8-byte-per-element blocks (`sub rsp, size * 8`). When an array is passed to a function, its base address is loaded with `lea rax, [rbp - offset]` and passed as a pointer (reference semantics).

**I/O.** The `print` built-in passes the value in `rsi` and the format string address in `rdi` before invoking `printf`. Stack alignment to a 16-byte boundary is preserved around the call using a `rbx`-save/restore pattern. `readInt` is emitted as a standalone helper function in the assembly header that calls `scanf` and returns the scanned integer in `rax`.

**Data segment.** String literals are emitted into the `section .data` block as `str_<n>  db  \`...\`, 0` labels. Format strings for integer and string printing are also declared there.

---

## 6. Features

### 6.1 Functions

Functions are declared with return type, name, and a parenthesized parameter list. Function hoisting allows invocation before the declaration site. Recursive calls are fully supported, including mutual recursion, because all function names are pre-registered in the global symbol table during the first semantic pass.

```c
int compute(int a, int b) {
    return a + b;
}

void main() {
    int result = compute(20, 40);
    print(result); // 60
}
```

### 6.2 Loops

Both `while` and `for` loops are supported. The `for` loop initializer may declare a new variable; that variable is scoped to the loop via a dedicated IR scope. The `break` and `continue` statements are supported and validated at the semantic level to ensure they appear only inside a loop body. The IR generator maintains a `loop_stack` to resolve break/continue targets to the correct labels.

```c
for (int i = 0; i < 5; ++i) {
    print(i);
}

int count = 3;
while (count > 0) {
    print(count);
    --count;
}
```

### 6.3 Arrays

Fixed-size, statically typed arrays are declared with a size literal. Elements are accessed and assigned via bracket notation. Arrays may be declared at global scope (outside any function) or locally within a function. When passed to functions, arrays are passed by reference using the `PARAM_REF` / `LOAD_PARAM_REF` IR opcodes.

```c
int arr[5];
for (int i = 0; i < 5; ++i) {
    arr[i] = i * 10;
}
print(arr[3]); // 30
```

### 6.4 Strings

String literals are declared as `string` type variables. They are stored as `db` entries in the assembly data section and referenced as read-only character pointers. The `print` built-in dispatches to a `PRINT_STR` IR instruction when the argument is of type `string`, causing the code generator to emit a `printf` call with a `%s` format string.

```c
string msg = "Hello, Trisynth!";
print(msg);
```

### 6.5 Type System

Trisynth enforces a static, nominal type system at compile time. The types available for variable declarations are:

| Type | Description |
|---|---|
| `int` | 64-bit signed integer |
| `uint32` | 32-bit unsigned integer (parsed; back-end treated as 64-bit) |
| `bool` | Boolean (`true` / `false`); relational expressions yield `bool` |
| `string` | Immutable character pointer to a data-section literal |
| `const` | Qualifier applicable to any scalar or array |

The types `float` and `char` are recognized by the lexer and parser but are rejected at the semantic stage with an `E002 Semantic Error`, indicating they are not yet structurally supported by the back-end.

### 6.6 Constants

The `const` qualifier produces a symbol-table entry with `is_const=True`. Any subsequent write to that symbol — whether a direct assignment, increment, or decrement — is caught by the semantic analyzer before IR generation occurs.

```c
const int LIMIT = 10;
// LIMIT = 20; // E002: Cannot assign to const variable `LIMIT`
```

---

## 7. Challenges Faced

**7.1 Hoisting without pre-declaration.** Implementing function hoisting in a single-source-file compiler required a deliberate two-pass design in the semantic analyzer. The challenge was ensuring that the first pass registered only signatures (not full bodies) so that the type information was available for call-site validation during the second pass.

**7.2 Short-circuit logical evaluation.** Logical AND and OR cannot be naively translated to a single binary IR instruction because of side effects and performance. The IR generator therefore emits a conditional-jump pattern for each logical operator, branching around the right operand evaluation when the result can be determined from the left operand alone.

**7.3 Stack frame construction for arrays.** Arrays on the stack require a contiguous block allocation rather than a single 8-byte slot. The `StackFrame` pre-pass must distinguish between scalar temporaries and array names (tracked via `self._array_names` in the IR generator) to emit the correct `ARR_DECL` opcode and allocate the correct block size.

**7.4 Array reference passing.** Passing arrays to functions by value would require copying the entire block. The compiler instead passes the stack address of the first element as a pointer. This required a distinct `PARAM_REF` / `LOAD_PARAM_REF` / `LOAD_PARAM_REF` IR opcode pair and corresponding code-gen logic to emit `lea` rather than `mov` for the parameter address.

**7.5 Stack alignment for `printf`.** The System V AMD64 ABI requires the stack pointer to be 16-byte aligned at the point of a `call` instruction. Because the compiler cannot always predict the alignment state within a function's body, a `rbx`-based save/restore pattern is used around every `printf` and `scanf` invocation.

**7.6 Cross-platform build packaging.** Distributing a pre-built NASM binary alongside the Python compiler required platform detection in the setup scripts and permission management in WSL/Linux environments to ensure the bundled binary was executable.

---

## 8. Results and Outputs

### 8.1 Feature Demonstration

**Input (`comprehensive.nc`):**

```c
const int LIMIT = 5;

void main() {
    print(8888);

    int arr[5];
    for (int i = 0; i < LIMIT; ++i) {
        arr[i] = i * 10;
    }

    int result = compute(arr[2], arr[4]);
    print(result);

    if (result > 50 && result < 100) {
        print(1);
    } else {
        print(0);
    }

    int count = 3;
    while (count > 0) {
        print(count);
        --count;
    }
}

int compute(int a, int b) {
    return a + b;
}
```

**Expected output:**

```
8888
60
1
3
2
1
```

### 8.2 Constant Folding Demonstration

**Input:**

```c
void main() {
    int x = (10 * 10 + 44) / 12;
    print(x);
}
```

Without optimization, the expression generates four arithmetic IR instructions. After constant folding, the expression is collapsed to a single `MOV x_0 12`, and the four intermediate temporaries are eliminated by the dead-code pass.

**Expected output:**

```
12
```

### 8.3 Recursive Fibonacci with Memoization

**Input (excerpt from `stress_test.nc`):**

```c
int memo[20];
const int N = 10;

int fib(int n) {
    if (n <= 1) return n;
    if (memo[n] != 0) return memo[n];
    int res = fib(n - 1) + fib(n - 2);
    memo[n] = res;
    return res;
}

void main() {
    init_memo();
    int res = fib(N);
    print(res);
}
```

**Expected output:**

```
55
```

---

## 9. Conclusion

The Trisynth compiler demonstrates that a complete, industrially structured compilation pipeline can be constructed from first principles in a high-level language without reliance on compiler-generator frameworks. Every stage — tokenization, recursive-descent parsing, scope-aware type checking, three-address IR generation, multi-pass optimization, and native x86-64 assembly emission — is implemented explicitly. The resulting compiler correctly handles hoisted functions, recursive calls, global and local arrays passed by reference, constant folding, and structured control flow. The system produces NASM-compatible assembly that, when assembled and linked against `libc`, executes correctly on Linux-based x86-64 targets.

---

## 10. Future Work

- **`float` and `char` type back-end support.** These types are already parsed and recognized lexically; completing their IR-to-assembly lowering would extend the language's expressiveness.
- **RISC-V back-end completion.** A partial RISC-V code generator (`output_riscv.s`) exists; completing this target would make Trisynth portable to embedded RISC-V platforms.
- **Register allocation.** The current code generator places all temporaries on the stack. Implementing live-range analysis and a graph-coloring register allocator would significantly improve runtime performance.
- **Struct and record types.** Adding composite data types would bridge the gap between Trisynth and production systems languages.
- **`float`-aware constant folding.** Extending the constant-folding pass to handle floating-point arithmetic is a direct extension of the existing infrastructure.
- **Error recovery in the parser.** Currently the parser aborts on the first syntax error. A panic-mode or phrase-level recovery strategy would improve usability for interactive development.
