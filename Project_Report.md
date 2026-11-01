# Project Report

**Project Title:** Trisynth — Design and Implementation of a Custom Programming Language and Multi-Target Compiler  

---

## Abstract

This report documents the design and implementation of Trisynth, a statically typed, imperative programming language together with its accompanying multi-pass compiler. The compiler is implemented in Python and translates Trisynth source programs through a six-stage pipeline: lexical analysis, parsing into an Abstract Syntax Tree, semantic analysis and type checking, three-address intermediate representation (IR) generation, IR-level optimization, and assembly code generation. After optimization the same IR is lowered by two back-ends, x86-64 (NASM syntax) and RISC-V 64 (GNU as syntax); the x86-64 output is assembled, linked and run by default. The language supports integer and boolean scalar types, strings, fixed-size arrays, function declarations (including forward-referenced and recursive functions), and structured control flow. Five distinct optimization passes (six pass invocations, since common subexpression elimination runs twice) are applied at the IR level prior to code emission. The resulting x86-64 assembly is assembled with NASM and linked against the system C standard library (`libc`) through `gcc` to obtain an executable binary. The project implements the whole pipeline without a compiler back-end framework such as LLVM.

---

## 1. Introduction

Writing a compiler requires integrating several sub-disciplines of computer science: language processing, data-flow reasoning, and systems programming. The Trisynth project designs a small language and builds every compilation stage in Python.

The compiler produces x86-64 NASM assembly and RISC-V 64 GNU-as assembly from the same optimized IR. The x86-64 path is the default and the one exercised by the test suite; the RISC-V output is generated on every run, but assembling and running it requires `riscv64-linux-gnu-gcc` and `qemu-riscv64` on Linux or WSL (it was inspected as text, not executed, when this report was verified).

This report is organized to mirror the structure of the compiler itself. Each section corresponds directly to a compiler phase and references the relevant Python module in the `src/` directory.

---

## 2. Problem Statement

Many educational compiler projects rely on established intermediate representations (LLVM IR, JVM bytecode) or grammar frameworks (PLY, ANTLR) to reduce implementation effort. While pragmatic, this approach hides the algorithmic core of compilation.

Trisynth addresses the end-to-end implementation of a compiler without such dependencies: every stage — tokenization, recursive-descent parsing, scope-aware semantic analysis, three-address IR generation, local IR optimization, and stack-slot assembly emission — is constructed explicitly in Python. The compiler enforces static types, supports function declarations in any order (hoisting), and produces x86-64 code that is linked against `printf` (used by `print`) and `scanf` (used only by the `readInt` helper).

---

## 3. System Architecture

### 3.1 Overall Design

The Trisynth compiler is a batch, ahead-of-time compiler with a layered architecture. Source code flows through the pipeline in a single forward pass with no back-patching between stages. Each stage communicates with the next through a well-defined data structure. Every stage stops at the first error it finds.

```
Source File (.tri)
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
│  (5 passes, run as 6 │
│   steps, one sweep)  │
└──────────┬───────────┘
           │  Optimized IR
           ├──────────────────────────────┐
           ▼                              ▼
┌───────────────────────┐     ┌──────────────────────────┐
│   x86-64 Code Gen     │     │   RISC-V Code Gen        │
│ backend/codegen_x86.py│     │ backend/riscv/           │
│                       │     │   codegen_riscv.py       │
└──────────┬────────────┘     └────────────┬─────────────┘
           │  output.asm                   │  output_riscv.s
           ▼                               ▼
  nasm -f elf64 → gcc -no-pie      riscv64-linux-gnu-gcc -static
     → ELF binary `program`          → run under qemu-riscv64
```

Both back-ends always run; `output.asm` and `output_riscv.s` are written to the current working directory on every compilation that reaches code generation. The `--arch x86|riscv|both` option (default `x86`) only selects which output is assembled and run.

### 3.2 Compiler Pipeline Summary

| Stage | Input | Output | Module |
|---|---|---|---|
| Lexical Analysis | Raw source text | `List[Token]` | `lexer.py`, `token_type.py` |
| Parsing | Token stream | `Program` AST | `parser.py`, `ast.py` |
| Semantic Analysis | AST | Validated AST (only `print` arguments receive a `_semantic_type` annotation) | `analyzer.py`, `symbol_table.py` |
| IR Generation | Validated AST | `List[Instruction]` | `ir_gen.py`, `instructions.py` |
| Optimization | IR | Reduced IR | `optimization/` |
| Code Generation | Optimized IR | x86-64 NASM text and RISC-V GNU-as text | `codegen_x86.py`, `codegen_riscv.py` |

---

## 4. Language Design

### 4.1 Syntax and Semantics

Trisynth adopts a C-family surface syntax. Every variable must be declared with an explicit type before use; implicit conversions are not permitted. A non-`void` function must contain a `return` that the analyzer can see on every path: a `return` directly in the function's block, or an `if`/`else` whose branches both return. A `return` that appears only inside a `while` or `for` body does not count (for example `int f() { while (true) { return 1; } }` is rejected with "Missing return statement in non-void function 'f'").

The language uses semicolons as statement terminators and curly braces for block delimiters. Comments follow C conventions: `//` for line comments and `/* ... */` for block comments (not nested). Source files carry the `.tri` extension; the compiler rejects any other extension.

### 4.2 Design Decisions

**Hoisting over declaration order.** Unlike C, Trisynth performs a two-pass semantic analysis traversal of the program's top-level declaration list. During the first pass, all function signatures (name, return type and parameter types) are registered in the symbol table. During the second pass, function bodies are validated. This allows a function defined textually after its call site to be resolved correctly without forward declarations. Duplicate function names are rejected.

**No implicit type promotion.** All binary expressions require both operands to carry identical types; the semantic analyzer raises a `Type Error` if types diverge. Exceptions: `&&` and `||` accept any mix of `int` and `bool` operands, the unary operators do not check their operand type (`!` and `-` return the operand's type), and arithmetic on `bool` operands is accepted (`true + true` is `2`).

**Const immutability enforcement.** Variables declared with the `const` qualifier are tracked in the symbol table with an `is_const` flag. Any assignment or increment/decrement targeting a `const` scalar is rejected at the semantic stage, not at runtime. Assigning to an element of a `const` array is also rejected (`E002 ... Cannot mutate elements of const array`); a known gap is that `++a[i]` / `--a[i]` on a `const` array is not rejected.

**Comparison operators produce `bool`.** Binary relational operators (`<`, `>`, `==`, `!=`, `<=`, `>=`) return type `bool` from the semantic analyzer. `if` and `while` conditions accept `bool` or `int`; a `for` condition must be `bool` (a missing `for` condition is allowed).

**String immutability.** Strings are treated as read-only pointer operands pointing to data-section labels. `==` and `!=` on strings are allowed and compare the pointer values (identical literals share one data label), not the characters. Every other binary operator applied to strings raises an `E002` error.

---

## 5. Compiler Implementation

### 5.1 Lexical Analysis

**Module:** `src/frontend/lexer.py`  
**Token definitions:** `src/frontend/token_type.py`

The `Lexer` class scans the source text with Python's `re` module. A prioritized list of `(pattern, TokenType)` pairs is tried in order at each position via `regex.match(source, pos)`; the first pattern that matches wins (multi-character operators such as `++` and `<=` are listed before their single-character prefixes). When a pattern matches, the token is constructed with its type, lexeme, line number, and column number; the position cursor is advanced accordingly.

Block comments are handled as a special case before the general pattern list by directly scanning for the `*/` terminator; an unclosed comment raises a plain `Exception` whose message begins `Lexical Error:` and includes the line and column. String literals are stripped of their enclosing quotation marks at tokenization time, storing only the inner content in the `Token.value` field; escape sequences are kept verbatim and are interpreted later by the assembler (NASM backtick strings).

The keyword dictionary maps reserved words (`int`, `bool`, `char`, `void`, `const`, `string`, `if`, `else`, `while`, `for`, `break`, `continue`, `return`, `print`, `readInt`, `true`, `false`) to dedicated `TokenType` members rather than treating them as identifiers. `print` and `readInt` are keywords, not library functions.

**Token categories defined (50 `TokenType` members):**

| Category | Members |
|---|---|
| Literals and names | `INTEGER`, `STRING`, `CHAR`, `IDENTIFIER` |
| Keywords (types) | `KW_INT`, `KW_BOOL`, `KW_CHAR`, `KW_STRING`, `KW_VOID`, `KW_CONST` |
| Keywords (control) | `KW_IF`, `KW_ELSE`, `KW_WHILE`, `KW_FOR`, `KW_BREAK`, `KW_CONTINUE`, `KW_RETURN` |
| Keywords (I/O) | `KW_PRINT`, `KW_READ_INT` |
| Keywords (boolean literals) | `KW_TRUE`, `KW_FALSE` |
| Arithmetic and shift | `PLUS`, `MINUS`, `STAR`, `SLASH`, `MODULO`, `LSHIFT`, `RSHIFT` |
| Increment / decrement | `INCREMENT`, `DECREMENT` |
| Relational | `EQ`, `NEQ`, `LT`, `GT`, `LTE`, `GTE` |
| Logical | `AND`, `OR`, `NOT` |
| Assignment | `ASSIGN` |
| Punctuation | `LPAREN`, `RPAREN`, `LBRACE`, `RBRACE`, `LBRACKET`, `RBRACKET`, `SEMICOLON`, `COMMA` |
| Special | `EOF`, `ERROR` (`ERROR` is defined but never produced) |

### 5.2 Parsing Strategy and AST

**Module:** `src/frontend/parser.py`, `src/frontend/ast.py`

The parser is a hand-written, recursive-descent parser with no external parser-generator dependency. It accepts the flat token stream produced by the lexer and builds an Abstract Syntax Tree. Operator precedence is encoded by nested function calls: higher-precedence operators are resolved deeper in the call stack.

**Expression precedence hierarchy (lowest to highest):**

```
Assignment  (=)            right-associative
Logical OR  (||)
Logical AND (&&)
Equality    (== !=)
Relational  (< > <= >=)
Shift       (<< >>)
Additive    (+ -)
Multiplicative (* / %)
Unary       (! - ++ --)    prefix only
Primary     (literals, identifiers, function calls, array access, parenthesized expressions, readInt())
```

For example `1 + 2 << 3` evaluates to `24` and `1 << 2 + 1` to `8`. `++x` / `--x` are prefix only (`x++` is a syntax error) and need a variable or array element; on a plain variable the parser rewrites `++x` to the assignment `x = x + 1`, and only `++a[i]` / `--a[i]` produce a `UnaryExpr`.

**AST Node taxonomy:**

| Category | Nodes |
|---|---|
| Expressions | `Literal`, `StringLiteral`, `Variable`, `ArrayAccess`, `BinaryExpr`, `UnaryExpr`, `LogicalExpr`, `Assignment`, `ArrayAssignment`, `CallExpr` |
| Statements | `ExprStmt`, `PrintStmt`, `VarDecl`, `ArrayDecl`, `Block`, `IfStmt`, `WhileStmt`, `ForStmt`, `BreakStmt`, `ContinueStmt`, `ReturnStmt`, `FunctionDecl` |
| Program | `Program` |

Every AST node extends the abstract base `ASTNode`, which requires a `__repr__` method. These reprs are one-line summaries (for example `Block(count=N)`); the full tree is printed by the separate `ASTPrinter` class in `main.py` (`--ast`). Nodes carry no computed types; types are computed by the semantic analyzer.

### 5.3 Semantic Analysis

**Module:** `src/semantic/analyzer.py`, `src/semantic/symbol_table.py`

The `SemanticAnalyzer` traverses the AST using the Visitor pattern. A `method_name = f'visit_{type(node).__name__}'` lookup via `getattr` dispatches each node to its specific handler.

**Responsibilities:**

1. **Two-pass function hoisting.** The first sub-pass over `Program.declarations` registers every `FunctionDecl` name, return type and parameter types in the global scope. The second sub-pass processes function bodies. This ensures that a call to a not-yet-defined function (including mutual recursion) does not generate an `undeclared` error.

2. **Scoped symbol table.** The symbol table is implemented as a stack of dictionaries (`scopes`). Entering a block pushes a new scope; exiting pops it. Variable resolution walks the stack from innermost to outermost, implementing lexical scoping. Redeclaring a name in the same scope is an error.

3. **Type checking.** Every expression node returns a type string (`'int'`, `'bool'`, `'string'`, `'int[]'`, etc.). Binary expressions check that both operands share a type. Function calls verify argument count and per-argument type against the recorded `param_types`.

4. **Const enforcement.** Any assignment or increment targeting a const scalar raises `Semantic Error: Cannot assign to const variable '<name>'.`

5. **Return path validation.** The `_body_has_return()` helper recursively inspects a function body: a block passes if any statement in it returns, an `if` passes only if both branches return, and `while`/`for` never count. A non-`void` function that fails the check is rejected.

6. **Entry-point requirement.** After processing all declarations, the analyzer verifies that a symbol named `main` exists (its signature is not checked); its absence raises `E004 Semantic Error`.

7. **No global declarations.** Any top-level declaration that is not a function (a global variable, constant or array) is rejected with `E002 Semantic Error: Global variable '<name>' is not supported; declare it inside a function.` (`analyzer.py:85-87`). Both back-ends only compile instructions that lie inside `FUNC_START`/`FUNC_END`.

8. **`char`.** `char` is a keyword and a type name, but there is no char-literal grammar rule (`'a'` is a syntax error), and the analyzer rejects only scalar `char` variable declarations with `E002`; `char` arrays, parameters and return types are not rejected.

### 5.4 Intermediate Representation

**Module:** `src/ir/ir_gen.py`, `src/ir/instructions.py`

The IR is a linear sequence of `Instruction` objects (no control-flow graph), each holding an `OpCode` enum member and up to three operand fields (`arg1`, `arg2`, `result`). This corresponds to the classical three-address code (TAC) form. An instruction prints as `OPCODE result arg1 arg2`.

**IR OpCode groups (31 opcodes):**

| Group | OpCodes |
|---|---|
| Data movement | `MOV`, `LOAD_STR` |
| Arithmetic | `ADD`, `SUB`, `MUL`, `DIV`, `MOD`, `LSHIFT`, `RSHIFT` |
| Comparison | `LT`, `GT`, `LTE`, `GTE`, `EQ`, `NEQ` |
| Control flow | `LABEL`, `JMP`, `JMP_IF_FALSE` |
| Functions | `FUNC_START`, `FUNC_END`, `RETURN`, `CALL`, `PARAM`, `LOAD_PARAM` |
| Arrays | `ARR_DECL`, `ALOAD`, `ASTORE`, `PARAM_REF`, `LOAD_PARAM_REF` |
| I/O | `PRINT`, `PRINT_STR` |

Operand conventions worth knowing: there is no negate, not or increment opcode. `-x` is `SUB 0 x`, `!x` is `EQ x 0`, and `++x` is `ADD` followed by `MOV`. `ASTORE arr idx` carries the stored value in its `result` field. `CALL f n` has the argument count in `arg2` and always has a temporary as `result`. `LOAD_PARAM` / `LOAD_PARAM_REF` take the parameter index in `arg1`.

The `IRGenerator` uses a scope stack (mirroring the semantic analyzer's structure) to rename every declared variable, array and parameter to a globally unique name (e.g., `x_3`), eliminating shadowing ambiguity in the flat IR sequence. Temporary variables are allocated with sequential names `t0`, `t1`, …, and labels with `L0`, `L1`, …; these counters run across the whole program and are not reset per function.

**Short-circuit evaluation.** Logical `&&` and `||` operators are translated into conditional jump sequences rather than simple binary instructions, preserving correct short-circuit semantics: the right operand is only evaluated if needed. The result is a temporary that is always 0 or 1.

**Sample IR (`int x = (10 * 10 + 44) / 12; print(x);` inside `main`, from `--ir`):**

```
FUNC_START main
MUL t0 10 10
ADD t1 t0 44
DIV t2 t1 12
MOV x_0 t2
PRINT x_0
FUNC_END main
```

### 5.5 Optimizations

**Module:** `src/optimization/`

Five optimization classes are applied to the IR list after generation and before code emission. Each pass is a class exposing `run(List[Instruction]) -> List[Instruction]`. `main.py` runs them once each, in this order (no iteration to a fixed point): **Strength Reduction → CSE → Copy Propagation → Constant Folding → CSE ("Post-Folding Cleanup") → Dead Code Elimination.** All passes work on the flat instruction list; state is reset at labels and function starts.

**Strength Reduction (`strength_reduction.py`).** Rewrites: `x*0` → `MOV 0`; `x*1` → `MOV x`; multiplication by a compile-time power of two (either operand) → `LSHIFT`; `x/1` → `MOV x`; `x+0` and `x-0` → `MOV x`; `x-x` → `MOV 0`; self-moves are dropped. Signed division of a non-literal dividend by a power of two `2^k` is expanded to a bias sequence so the result still truncates toward zero: `LT` (is the dividend negative), `LSHIFT`/`SUB` to build the bias `2^k - 1` (for `k = 1` the 0/1 flag is the bias itself), `ADD`, then `RSHIFT`. Literal dividends are left for constant folding. `MOD` is not reduced.

**Common Subexpression Elimination (`cse.py`).** A hash-map tracks previously computed `(opcode, arg1, arg2)` tuples for arithmetic and comparison instructions (not `ALOAD` or `CALL`); operands of `ADD`, `MUL`, `EQ` and `NEQ` are ordered so that commutative variants match. If the same expression is computed again and neither operand nor the earlier result has been reassigned, the recomputation is replaced with a `MOV` from the earlier result. The table is cleared at every `LABEL` and `FUNC_START`.

**Copy Propagation (`copy_propagation.py`).** After `MOV dest src` where `src` is a variable or temporary (constants are not recorded here), later uses of `dest` in the same label-delimited region are replaced by `src` until either is reassigned. It also rewrites the stored value operand of `ASTORE`.

**Constant Folding (`constant_fold.py`).** Evaluates arithmetic and comparison instructions whose operands are both compile-time integer constants, replacing the instruction with a `MOV` of the result (for example `MUL t0 10 10` → `MOV t0 100`). It also propagates known constants into later operands (within a region, plus variables assigned exactly once in the function's entry block), turns `JMP_IF_FALSE` on a constant into nothing (non-zero) or an unconditional `JMP` (zero), and removes a `JMP` to the immediately following label. Folding follows the machine semantics: results wrap to signed 64 bits, `/` and `%` truncate toward zero, and division by zero, `INT64_MIN / -1`, and shift counts outside 0–63 are left unfolded for the hardware.

**Dead Code Elimination (`dead_code.py`).** Removes any instruction whose `result` (temporary or user variable) is never used as an operand in reachable code, repeating until nothing changes. Instructions with side effects are kept (`PRINT`, `CALL`, `PARAM*`, `LOAD_PARAM*`, `ASTORE`, `ARR_DECL`, `ALOAD`, control flow, `RETURN`). Code after a `RETURN` or `JMP` is removed up to the next label that a reachable jump targets; a `JMP` to the next label and unused labels are removed too.

### 5.6 Code Generation (x86-64)

**Module:** `src/backend/codegen_x86.py`, `src/backend/common/stack_frame.py`

The `X86Generator` class translates the optimized IR into NASM-syntax x86-64 assembly. The code generator operates function-by-function (instructions outside `FUNC_START`/`FUNC_END` are ignored): for each function, it first performs a pre-pass over the function's instruction list to collect every IR name that appears as a `result`, allocates each a distinct 8-byte slot (arrays: `size*8` bytes) within a `StackFrame` object, and then emits the corresponding x86-64 instruction sequence. Slots are never reused, and all values live in memory; only `rax`, `rbx`, `rcx`, `rdx`, `r9` and `rsp`/`rbp` are used (there is no register allocation).

**Calling convention.** Trisynth uses a custom stack-based convention: arguments are pushed right-to-left before a `call` instruction; the callee saves the caller's frame pointer with the standard `push rbp / mov rbp, rsp` prologue and reads parameter *i* at `[rbp + 16 + i*8]`; the return value is in `rax`; the caller removes the arguments with `add rsp, 8*n` after the call.

**Array references.** Fixed-size arrays occupy a contiguous region of `size*8` bytes inside the function's single stack frame, reserved by the one prologue `sub rsp, N` (N is rounded up to 16); `ARR_DECL` itself emits no code and arrays are not zero-initialized. When an array is passed to a function, its base address is loaded with `lea rax, [rbp - offset]` (or `mov rax, [rbp - offset]` when forwarding an array parameter) and pushed as a pointer (reference semantics).

**I/O.** The `print` built-in passes the value in `rsi` and the format string address in `rdi` before invoking `printf`; integers use `"%ld\n"` and strings use `"%s"` (no newline is added). Stack alignment to a 16-byte boundary is established around the call by saving `rsp` in `rbx`, executing `and rsp, -16`, calling, and restoring `rsp` from `rbx`. The generated code never saves or restores the caller's `rbx` itself (it is callee-saved in the System V ABI), and `ADD` also uses `rbx` as scratch. `readInt` is emitted as a standalone helper function in the assembly header that calls `scanf` and returns the scanned integer in `rax`.

**Data segment.** String literals are emitted into the `section .data` block as `str_<n>  db  \`...\`, 0` labels (identical literals share one label). Format strings `fmt_int`, `fmt_str` and `fmt_read_int` are also declared there.

### 5.7 Code Generation (RISC-V)

**Module:** `src/backend/riscv/codegen_riscv.py`

`RISCVGenerator` reuses the same `StackFrame` and handles every IR opcode. It uses the same stack-only scheme: `s0` is the frame pointer (locals at negative offsets), `ra` and `s0` are saved in the prologue, arguments are pushed on the stack and read at `16 + 8*i (s0)`, the return value is in `a0`, and the caller removes the arguments. Values are computed through `t0`/`t1`/`t2`. `print` calls `printf` with `a0`/`a1`; no explicit stack alignment is performed. The output is `output_riscv.s`, assembled with `riscv64-linux-gnu-gcc -static` and run under `qemu-riscv64` (`--arch riscv|both`, `--benchmark`).

### 5.8 Driver, Toolchain and Output Files

**Module:** `src/main.py`

Command line: `python src/main.py file.tri [--tokens] [--ast] [--ir] [--asm] [--compare-asm] [-v] [--arch x86|riscv|both] [--benchmark]`, or no file / `--demo` to read source from standard input. `--tokens`, `--ast` and `--ir` print the stage and stop; `--asm` and `--compare-asm` print the assembly and stop; `-v` prints every stage, including the global symbol table.

`_resolve_toolchain` chooses one of three modes: `linux` (host is not Windows; uses the bundled `bin/linux/nasm` if present, with an automatic `chmod`, else system `nasm`), `wsl` (Windows with `wsl nasm --version` working; uses WSL's `nasm` and `gcc`), or `windows_native` (`nasm` and `gcc` on PATH; `win64` object format, `program.exe`; RISC-V skipped). If none applies, "No assembler toolchain found." is printed. The x86-64 build is `nasm -f elf64 output.asm -o output.o` followed by `gcc output.o -o program -no-pie`. In `windows_native` mode the generated code still follows the System V register convention for `printf`, so that mode is not expected to work (not verified).

Files written to the current directory: `output.asm` and `output_riscv.s` (always), `output.o` (or `output.obj`) and `program` (or `program.exe`) when running, and `program_riscv` when the RISC-V step succeeds. Run the compiler from a scratch directory, not from the repository root.

---

## 6. Features

### 6.1 Functions

Functions are declared with return type, name, and a parenthesized parameter list, at top level only. Function hoisting allows invocation before the declaration site. Recursive calls are fully supported, including mutual recursion, because all function names are pre-registered in the global symbol table during the first semantic pass.

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

Both `while` and `for` loops are supported. The `for` loop initializer may declare a new variable; that variable is scoped to the loop via a dedicated IR scope. The `for` condition must have type `bool`. The `break` and `continue` statements are supported and validated at the semantic level to ensure they appear only inside a loop body. The IR generator maintains a `loop_stack` to resolve break/continue targets to the correct labels (`continue` in a `for` jumps to the update step).

```c
void main() {
    for (int i = 0; i < 5; ++i) {
        print(i);
    }

    int count = 3;
    while (count > 0) {
        print(count);
        --count;
    }
}
```

### 6.3 Arrays

Fixed-size, statically typed arrays are declared with a positive integer literal size. Elements are accessed and assigned via bracket notation. Arrays must be declared locally within a function (global arrays are rejected). Array parameters are written `int a[]`. When passed to functions, arrays are passed by reference using the `PARAM_REF` / `LOAD_PARAM_REF` IR opcodes. Local arrays are not zero-initialized by the x86-64 back-end and indexing is not bounds-checked.

```c
void main() {
    int arr[5];
    for (int i = 0; i < 5; ++i) {
        arr[i] = i * 10;
    }
    print(arr[3]); // 30
}
```

### 6.4 Strings

String literals are declared as `string` type variables. They are stored as `db` entries in the assembly data section and referenced as read-only character pointers. The `print` built-in dispatches to a `PRINT_STR` IR instruction when the argument is of type `string`, causing the code generator to emit a `printf` call with a `%s` format string (no trailing newline). Strings have no operations other than assignment, passing, printing and pointer-comparison with `==` / `!=`.

```c
void main() {
    string msg = "Hello, Trisynth!";
    print(msg);
}
```

### 6.5 Type System

Trisynth enforces a static type system at compile time. The types available for variable declarations are:

| Type | Description |
|---|---|
| `int` | 64-bit signed integer |
| `bool` | Boolean (`true` / `false`); relational expressions yield `bool`; printed as 1 / 0 |
| `string` | Immutable character pointer to a data-section literal |
| `int[]`, `bool[]`, `string[]` | Fixed-size arrays (local, positive literal size); `T a[]` as a parameter |
| `void` | Function return type only (the analyzer does not reject `void x;`) |
| `const` | Qualifier applicable to a scalar or an array |

`char` is a keyword and type name but is effectively unsupported: a char literal such as `'a'` is a syntax error (the parser has no rule for it), and the analyzer rejects scalar `char` variable declarations with an `E002 Semantic Error` (`char` arrays, parameters and return types are not rejected). `float` and `uint32` are not part of the language: they are ordinary identifiers and floating-point literals are a lexical error (`Unexpected character '.'`).

`int` is a signed 64-bit two's-complement integer. `+`, `-`, `*` and `<<` wrap around on overflow, `/` and `%` truncate toward zero (so `-7 / 2` is `-3` and `-7 % 3` is `-1`), and `>>` is an arithmetic shift. The optimizer preserves these semantics: constant folding emulates them, and division by a power of two is reduced to a shift only together with a correction for negative dividends. Division by zero (and `INT64_MIN / -1`) traps at runtime and is never folded; the compiled program then terminates without a message.

### 6.6 Constants

The `const` qualifier produces a symbol-table entry with `is_const=True`. Any subsequent write to that scalar — whether a direct assignment, increment, or decrement — is caught by the semantic analyzer before IR generation occurs. Constants, like all variables, must be declared inside a function.

```c
void main() {
    const int LIMIT = 10;
    // LIMIT = 20; // Semantic Error: Cannot assign to const variable 'LIMIT'.
}
```

---

## 7. Challenges Faced

**7.1 Hoisting without pre-declaration.** Implementing function hoisting in a single-source-file compiler required a deliberate two-pass design in the semantic analyzer. The challenge was ensuring that the first pass registered only signatures (not full bodies) so that the type information was available for call-site validation during the second pass.

**7.2 Short-circuit logical evaluation.** Logical AND and OR cannot be naively translated to a single binary IR instruction because the right operand must not be evaluated when the left operand decides the result. The IR generator therefore emits a conditional-jump pattern for each logical operator, branching around the right operand evaluation when the result can be determined from the left operand alone.

**7.3 Stack frame construction for arrays.** Arrays on the stack require a contiguous block allocation rather than a single 8-byte slot. The code generator's frame pre-pass distinguishes arrays by the `ARR_DECL` opcode (which carries the size) and array-reference parameters by `LOAD_PARAM_REF`; the IR generator's `_array_names` set is used only at call sites to choose between `PARAM` and `PARAM_REF`.

**7.4 Array reference passing.** Passing arrays to functions by value would require copying the entire block. The compiler instead passes the stack address of the first element as a pointer. This required a distinct `PARAM_REF` / `LOAD_PARAM_REF` IR opcode pair and corresponding code-gen logic to pass the array's address (`lea`) rather than a loaded value.

**7.5 Stack alignment for `printf`.** The System V AMD64 ABI requires the stack pointer to be 16-byte aligned at the point of a `call` instruction. Because user-function calls push their arguments, the compiler cannot predict the alignment state within a function's body, so an `rbx`-based pattern (save `rsp` in `rbx`, align, call, restore) is used around every `printf` and in the `scanf` call of `readInt`. A known cost is that `rbx` is clobbered without being restored for the caller.

**7.6 Cross-platform build packaging.** The driver supports Linux, Windows with WSL, and native Windows. On Linux a bundled `nasm` binary is preferred and made executable automatically; under WSL the system `nasm` and `gcc` inside WSL are used. `setup.sh` and `setup.bat` in the repository root install the prerequisites.

---

## 8. Results and Outputs

All programs below were compiled with `python src/main.py <file>.tri` and run on x86-64 through WSL; the outputs shown are the observed ones.

### 8.1 Feature Demonstration

**Input (`comprehensive.tri`):**

```c
void main() {
    const int LIMIT = 5;
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

**Observed output:**

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

Without optimization, the expression generates three arithmetic IR instructions (`MUL`, `ADD`, `DIV`) followed by a `MOV` into `x_0` (see the sample IR in Section 5.4). After copy propagation and constant folding the IR is:

```
FUNC_START main
MOV t0 100
MOV t1 144
MOV t2 12
MOV x_0 12
PRINT 12
FUNC_END main
```

The dead-code pass then removes the three temporaries and `x_0`, leaving only `PRINT 12` inside `main`.

**Observed output:**

```
12
```

### 8.3 Recursive Fibonacci with Memoization

Arrays cannot be global, so the memo table is a local array that is zero-filled explicitly (local arrays are not zero-initialized) and passed by reference.

**Input (`fib.tri`):**

```c
int fib(int n, int memo[]) {
    if (n <= 1) return n;
    if (memo[n] != 0) return memo[n];
    int res = fib(n - 1, memo) + fib(n - 2, memo);
    memo[n] = res;
    return res;
}

void main() {
    int memo[20];
    for (int i = 0; i < 20; ++i) {
        memo[i] = 0;
    }
    int res = fib(10, memo);
    print(res);
}
```

**Observed output:**

```
55
```

---

## 9. Conclusion

The Trisynth compiler demonstrates that a complete compilation pipeline can be built from scratch in Python without compiler-generator frameworks. Every stage — tokenization, recursive-descent parsing, scope-aware type checking, three-address IR generation, multi-pass optimization, and assembly emission for x86-64 and RISC-V — is implemented explicitly. The compiler correctly handles hoisted functions, recursive calls, local arrays passed by reference, constant folding, and structured control flow. The x86-64 output is assembled with NASM and linked against `libc` through `gcc`, and is executed correctly on Linux-based x86-64 targets (including WSL) in the tested programs. The RISC-V back-end generates text for every opcode but was not executed in this verification.

---

## 10. Future Work

- **`float` and `char` types.** `char` is only a keyword and type name (no literal syntax, and the analyzer rejects scalar `char` variables); `float` does not exist yet. Adding them end to end (lexing, parsing, type checking, IR and assembly lowering) would extend the language.
- **RISC-V validation.** The RISC-V generator (`src/backend/riscv/codegen_riscv.py`) covers all IR opcodes but should be validated under `qemu-riscv64`; it performs no explicit stack alignment, and shift immediates of 64 or more would not assemble.
- **Global variables.** Globals are currently rejected; supporting them requires emitting a data section and addressing it from both back-ends.
- **Register allocation.** The current code generator places all temporaries on the stack. Implementing live-range analysis and a register allocator would improve runtime performance.
- **Struct and record types.** Adding composite data types.
- **Error recovery.** Every stage currently aborts on the first error; a panic-mode or phrase-level recovery strategy in the parser would improve usability.

---

## 11. Design Choices and Known Limitations

| Area | Behaviour (as implemented) |
|---|---|
| Operators | No postfix `++`/`--`, no compound assignment (`+=` etc.), no bitwise `&`, `\|`, `^`, `~`. |
| Types | No `float` / `uint32`. `char` has a keyword but no literal syntax and is rejected for scalar variables. |
| Globals | Global variables, constants and arrays are rejected by the analyzer (`analyzer.py:85-87`). |
| Functions | Nested function declarations are rejected by the parser; functions are not values. |
| Arrays | Positive literal size, local only; not zero-initialized on x86-64 and not bounds-checked. |
| Uninitialized scalars | `int x; print(x);` reads a stack slot that is allocated after the frame size is fixed (below `rsp`); the value is undefined. |
| Strings | Literals only, plus passing, printing and pointer comparison with `==` / `!=`; no concatenation or indexing. |
| Conditions | `if` and `while` accept `int` or `bool`; `for` requires `bool`. |
| Errors | The first error aborts compilation. Lexer and parser messages carry `line:col`; semantic, IR and optimizer errors do not. Exceptions are plain `Exception`s, printed as `Error: ...` or `   Failed: ...`. The process exit status is always 0. |
| Back-ends | Both x86-64 and RISC-V code are generated on every run; `--arch` selects only what is assembled and run. |
| IR and optimizer | Linear IR with no control-flow graph. The CLI performs a single sweep of the six pass steps. `Optimizer` in `optimizer.py` (fixed point, at most 10 rounds) is used only by `tests/unit/test_compiler_pipeline.py`. |
| Code generation | Stack-only: one 8-byte slot per IR name, no slot reuse, no register allocation. `rbx` is used as scratch and is not preserved for the caller. |
| `IRInterpreter` | Defined in `main.py` but not called by the CLI; used only by `tests/unit/test_string_literals.py`. It uses Python semantics (floor division, unbounded integers, zeroed arrays), which differ from the native code. |
| Const arrays | `++a[i]` / `--a[i]` on a `const` array is not rejected. |
| Division by zero | Traps at run time on x86-64; the program ends with no message. |
| Program input | When the compiler itself runs the assembled program, standard input is not reliably forwarded (observed: `readInt` returned 0 under Windows + WSL). To supply input, run the assembled program directly (for example `echo 21 \| wsl ./program`, which printed 42 for `print(readInt() * 2)`). Program output is shown only after the program exits. |
| CLI and toolchain | Options and toolchain detection are described in Section 5.8. |

---

## 12. Testing

The test suite lives in `tests/unit/` and is run with `python -m pytest tests -q` from the repository root. At the time of writing it collects 186 tests, all passing.

| Test file | Tests |
|---|---|
| `test_01_lexer.py` | 6 |
| `test_02_parser.py` | 9 |
| `test_03_semantic.py` | 11 |
| `test_04_ir_gen.py` | 4 |
| `test_compiler_pipeline.py` | 1 |
| `test_opt_01_strength_reduction.py` | 6 |
| `test_opt_02_cse.py` | 5 |
| `test_opt_03_copy_propagation.py` | 4 |
| `test_opt_04_constant_folding.py` | 6 |
| `test_opt_05_dce.py` | 3 |
| `test_opt_06_arithmetic_semantics.py` | 128 (compares native x86-64 results with C semantics) |
| `test_string_literals.py` | 3 |
| **Total** | **186** |
