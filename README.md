# Trisynth Compiler — Language Reference & Developer Manual

**Trisynth** is a custom-built native compiler for **NanoC**, a minimal C-like language designed as a complete, pedagogically clear compiler construction reference.  
It compiles NanoC source through every classical stage — Lexing → Parsing → Semantic Analysis → IR Generation → Optimization → Native Code (x86-64 & RISC-V) — exposing each phase's internal representation and error reporting.

> [!NOTE]
> **Academic Disclaimer**: Trisynth is built to demonstrate compiler theory. Design decisions consistently choose *readability and correctness* over *performance and completeness*.

---

## Table of Contents

1. [Project Goals & Non-Goals](#1-project-goals--non-goals)
2. [Quick Start](#2-quick-start)
3. [NanoC Language Specification](#3-nanoc-language-specification)
   - [3.1 Lexical Rules](#31-lexical-rules)
   - [3.2 Types](#32-types)
   - [3.3 Literals](#33-literals)
   - [3.4 Variables & Constants](#34-variables--constants)
   - [3.5 Operators](#35-operators)
   - [3.6 Expressions](#36-expressions)
   - [3.7 Statements](#37-statements)
   - [3.8 Functions](#38-functions)
   - [3.9 Arrays](#39-arrays)
   - [3.10 I/O](#310-io)
4. [Compiler Architecture](#4-compiler-architecture)
   - [4.1 Phase 1 — Lexer](#41-phase-1--lexer)
   - [4.2 Phase 2 — Parser](#42-phase-2--parser)
   - [4.3 Phase 3 — Semantic Analyzer](#43-phase-3--semantic-analyzer)
   - [4.4 Phase 4 — IR Generator](#44-phase-4--ir-generator)
   - [4.5 Phase 5 — Optimizer](#45-phase-5--optimizer)
   - [4.6 Phase 6 — Backends (x86-64 & RISC-V)](#46-phase-6--backends-x86-64--risc-v)
   - [4.7 IR Interpreter](#47-ir-interpreter)
5. [Error Reference](#5-error-reference)
   - [5.1 Lexical Errors](#51-lexical-errors)
   - [5.2 Syntax Errors](#52-syntax-errors)
   - [5.3 Semantic / Type Errors](#53-semantic--type-errors)
6. [Optimization Reference](#6-optimization-reference)
7. [IR Instruction Set Reference](#7-ir-instruction-set-reference)
8. [Test Suite](#8-test-suite)
9. [Limitations & Known Behaviors](#9-limitations--known-behaviors)
10. [Future Work](#10-future-work)
11. [Contributors](#11-contributors)

---

## 1. Project Goals & Non-Goals

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

## 2. Quick Start

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

> See `INSTALL.md` and `SETUP.md` for full platform-specific installation details.

---

## 3. NanoC Language Specification

NanoC is a strict subset of C. Every valid NanoC program is structurally close to C, but has tighter type rules, no implicit conversions, and no pointers.

### 3.1 Lexical Rules

#### Character Set
NanoC source files are plain ASCII. Unicode identifiers are **not** supported.

#### Whitespace
Spaces, tabs (`\t`), carriage returns (`\r`), and newlines (`\n`) are all treated as whitespace and are ignored between tokens.

#### Comments
```c
// This is a single-line comment — ignored to end of line

/* This is a block comment.
   It can span multiple lines.
   It MUST be properly closed with */ 
```

> [!CAUTION]
> An **unclosed block comment** is a `Lexical Error`. The compiler detects `/*` without a matching `*/` and halts immediately.

#### Identifiers
```
[a-zA-Z_][a-zA-Z0-9_]*
```
Identifiers are case-sensitive. `myVar`, `MyVar`, and `MYVAR` are three distinct identifiers.

#### Keywords (Reserved)
The following words **cannot** be used as identifiers:

| Keyword | Purpose |
|---|---|
| `int` | Integer type |
| `bool` | Boolean type |
| `float` | Float type (lexed; backend limited) |
| `void` | No-return type |
| `const` | Immutable variable modifier |
| `string` | Statically allocated string pointer reference |
| `if` / `else` | Conditional branch |
| `while` | Pre-test loop |
| `for` | C-style three-part loop |
| `break` | Exit innermost loop |
| `continue` | Skip to next iteration |
| `return` | Return from function |
| `true` / `false` | Boolean literals |
| `print` | Built-in output |
| `readInt` | Built-in input |

---

### 3.2 Types

NanoC has a **static, strict type system** with no implicit conversions.

| Type | Size (conceptual) | Values | Notes |
|---|---|---|---|
| `int` | 64-bit signed integer | −2⁶³ … 2⁶³−1 | General purpose integer |
| `bool` | logical | `true`, `false` | Result of comparisons & logical ops |
| `void` | — | — | Only valid as function return type |
| `string` | array blocks | characters | Securely points implicitly representing C-style literals evaluated safely inside `.data` structures |
| `int[]` | fixed array of `int` | — | Declared as `int name[SIZE]` |
| `float` | 64-bit float | — | Accepted by lexer/parser; IR support limited |

> [!IMPORTANT]
> **No implicit promotion.** You cannot add `bool + int`, pass `int` where `int[]` is expected, or assign `bool` to `int`. Each violation raises a `Type Error` at compile time.

---

### 3.3 Literals

#### Integer Literals
```c
0    42    999    -1    // Parsed as base-10 signed int
```
Negative integer literals are parsed as a unary minus applied to a positive literal. Leading zeros do **not** indicate octal.

#### Boolean Literals
```c
true    false
```

#### Float Literals (limited support)
```c
3.14    0.001   // Lexed as FLOAT token; IRGen and backend treat as int where possible
```

#### String Literals
```c
"Hello World\n" // Supports explicit C-style native escapes (like \n and \t) resolving globally inside memory segments dynamically
```

---

### 3.4 Variables & Constants

#### Variable Declaration (with initializer)
```c
int x = 42;
bool flag = true;
```

#### Variable Declaration (no initializer)
```c
int count;    // Value is undefined — reading before assignment is undefined behavior
```

#### Constant Declaration
```c
const int MAX = 100;     // Must be initialized
const bool DEBUG = false;
```

Rules for `const`:
- **Must be initialized** at declaration — `const int x;` is a **Syntax Error**.
- **Cannot be reassigned** — `x = 200;` after `const int x = 100;` is a **Semantic Error**.
- **Cannot be incremented/decremented** — `++x` on a const is caught at the Assignment level (since `++x` desugars to `x = x + 1`).
- **Cannot be declared const at function scope** (function declarations may not be marked `const`).

#### Scope Rules
NanoC uses **lexical (static) scoping** with nested block scopes:
- Each `{ }` block opens a new scope.
- Inner scope names shadow outer scope names.
- Redeclaring the same name in the **same** scope is a **Semantic Error**.
- Variables from enclosing scopes are visible inside inner scopes.

```c
void main() {
    int x = 1;            // Scope 1 (function body)
    {
        int x = 2;        // Scope 2 — shadows outer x (legal)
        print(x);         // prints 2
    }
    print(x);             // prints 1 — outer x still in scope
}
```

---

### 3.5 Operators

#### Arithmetic Operators
| Operator | Operation | Operand Types | Result Type |
|---|---|---|---|
| `+` | Addition | `int`, `int` | `int` |
| `-` | Subtraction | `int`, `int` | `int` |
| `*` | Multiplication | `int`, `int` | `int` |
| `/` | Integer division | `int`, `int` | `int` |
| `%` | Modulo | `int`, `int` | `int` |

> Division truncates toward zero, identical to C.  
> Division by zero is **not** caught at compile time — it is undefined runtime behavior.

#### Relational Operators (produce `bool`)
| Operator | Meaning |
|---|---|
| `==` | Equal |
| `!=` | Not equal |
| `<` | Less than |
| `>` | Greater than |
| `<=` | Less than or equal |
| `>=` | Greater than or equal |

Relational operators require **both operands to be the same type** (`int` and `int`, or `bool` and `bool`). They always produce a `bool` result.

#### Logical Operators
| Operator | Meaning | Operands |
|---|---|---|
| `&&` | Logical AND | `bool`, `bool` |
| `\|\|` | Logical OR | `bool`, `bool` |
| `!` | Logical NOT | `bool` |

Logical operators require `bool` operands. Applying `&&` to `int` values is a **Type Error**.

> [!NOTE]
> NanoC uses **short-circuit evaluation** for `&&` and `||`. The IR generator emits conditional jumps — the right operand is only evaluated if necessary.

#### Increment / Decrement
```c
++x;   // x = x + 1  (pre-increment; desugared to Assignment by the parser)
--x;   // x = x - 1  (pre-decrement; same)
```
- Only valid on `int` variables.
- Not valid on `const` variables — caught as a re-assignment.
- Not directly valid on array elements.

#### Operator Precedence (high to low)

| Level | Operators | Associativity |
|---|---|---|
| 1 (highest) | `!`, `++`, `--` (unary) | Right |
| 2 | `*`, `/`, `%` | Left |
| 3 | `+`, `-` | Left |
| 4 | `<`, `>`, `<=`, `>=` | Left |
| 5 | `==`, `!=` | Left |
| 6 | `&&` | Left |
| 7 | `\|\|` | Left |
| 8 (lowest) | `=` (assignment) | Right |

---

### 3.6 Expressions

All expressions have a **type** determined at compile time.

```c
int x = 3 + 4 * 2;          // int — arithmetic
bool b = (x > 5);            // bool — relational
bool both = (x > 0) && b;   // bool — logical
int y = arr[2];              // int — array access
int z = foo(3);              // int — function call returning int
```

Expressions cannot be used as statements directly (there is no bare `x + 1;` statement).

---

### 3.7 Statements

#### Assignment
```c
x = expression;         // Assigns to an already-declared variable
arr[i] = expression;    // Assigns into an array element
```

- The right-hand side type must **exactly match** the variable's declared type.
- Assignment to `const` variables is a **Semantic Error**.

#### Expression Statement
Calls whose return values are discarded:
```c
print(x);       // print is a built-in statement
foo();          // call a void function
```

#### If / Else
```c
if (condition) {
    // ...
}

if (condition) {
    // ...
} else {
    // ...
}
```
- Condition must evaluate to `bool` or `int`.
- The `else` clause is optional.
- Braces `{ }` around each branch are **required**.

#### While Loop
```c
while (condition) {
    // body
}
```
- Condition must evaluate to `bool` or `int`.
- `break` exits the loop immediately.
- `continue` skips to the next iteration.

#### For Loop
```c
for (int i = 0; i < 10; ++i) {
    // body
}
```
- Init may declare a new `int` scoped to the loop.
- Update expression is evaluated after each iteration before checking the condition again.
- `break` and `continue` behave identically to `while`.

#### Return Statement
```c
return;              // Legal inside void functions
return expression;   // Must match the function's declared return type
```
**Missing return detection**: The semantic analyzer performs a conservative path analysis. A non-`void` function that has **no guaranteed return path** (e.g., a return only inside an `if` with no `else`) raises:
```
Missing return statement in non-void function 'name'
```

#### Break / Continue
```c
break;       // Exits the immediately enclosing loop
continue;    // Skips to the next iteration of the immediately enclosing loop
```
Using `break` or `continue` **outside any loop** is a **Semantic Error**.

---

### 3.8 Functions

#### Declaration Syntax
```c
return_type function_name(param_type param_name, ...) {
    // body
}
```

#### Examples
```c
void say_hello() {
    print(42);
}

int add(int a, int b) {
    return a + b;
}

int factorial(int n) {
    if (n <= 1) { return 1; }
    return n * factorial(n - 1);   // Recursion supported
}
```

#### Function Rules
- Functions must be declared **before** they are called (no forward declarations / hoisting by default — the program is processed top-to-bottom).
- `void` functions may have `return;` with no value.
- Non-`void` functions **must** have a return on every execution path (statically checked).
- Function name **overloading** is **not** supported — two functions with the same name is a **Semantic Error**.
- Functions are **not** first-class values — they cannot be stored in variables or passed as arguments.

#### Parameter Passing
- **Scalar types** (`int`, `bool`) are passed **by value** — the callee gets a copy.
- **Arrays** (`int[]`) are passed **by reference** — the callee operates directly on the caller's array storage.

```c
void zero_first(int arr[]) {
    arr[0] = 0;    // Modifies caller's array
}
```

#### Argument Count Checking
Too few or too many arguments at the call site is a **Semantic Error**:
```
Type Error: Function 'foo' expects 2 arguments, got 1.
```

#### Argument Type Checking
Each argument type must **exactly match** the corresponding parameter type:
```
Type Error: Argument 1 of 'foo' expects 'int[]', got 'int'.
```

---

### 3.9 Arrays

#### Declaration
```c
int arr[10];    // Fixed-size array of 10 ints, all initialized to 0
```
- Size must be a **positive integer literal** — a size of `0` or negative is a **Syntax Error** (caught at parse time).
- No dynamic sizing (`int arr[n]` where `n` is a variable is **not** supported).
- Floats as size (`int arr[3.5]`) are **not** accepted — the parser expects an `INTEGER` token.

#### Element Access
```c
int x = arr[2];      // Read element at index 2
arr[3] = x + 1;     // Write element at index 3
```
- The index **must** be of type `int`. Using `bool` as an index is a **Type Error**.
- **No bounds checking** at compile time or runtime — out-of-bounds access is undefined behavior.

#### Passing Arrays to Functions
```c
void fill(int a[], int val) {
    a[0] = val;
    a[1] = val + 1;
}

void main() {
    int arr[5];
    fill(arr, 10);
    print(arr[0]);   // 10
    print(arr[1]);   // 11
}
```
The parameter type for an array parameter is written `int arr[]` (empty brackets).

---

### 3.10 I/O

NanoC has two built-in I/O primitives — they are part of the language, not a library.

#### print
```c
print(expression);    // Prints the value of the expression natively
```
- Accepts any `int`, `bool`, or `string` type evaluation expressions.
- Strings dynamically process native escapes bypassing raw formats to properly emulate `\n` boundaries physically inside terminal routing.
- In the native backends, integers output formatting variables `%ld\n` and strings output as `%s` wrapping securely pointing external `printf` runtime behaviors natively.

#### readInt
```c
int n = readInt();    // Reads one integer from stdin
```
- Returns an `int`.
- Blocks until the user types a number and presses Enter.

---

## 4. Compiler Architecture

```
Source Code (.tri)
      │
      ▼
┌─────────────┐
│   LEXER     │  src/frontend/lexer.py
│             │  Converts characters → Token stream
└──────┬──────┘
       │  List[Token]
       ▼
┌─────────────┐
│   PARSER    │  src/frontend/parser.py
│             │  Recursive descent → AST
└──────┬──────┘
       │  AST (Program node)
       ▼
┌──────────────────┐
│ SEMANTIC ANALYZER│  src/semantic/analyzer.py
│                  │  Type checking, scope, const, return paths
└────────┬─────────┘
         │  Validated AST
         ▼
┌─────────────┐
│  IR GEN     │  src/ir/ir_gen.py
│             │  Lowers AST → Three-Address Code IR
└──────┬──────┘
       │  List[Instruction]
       ▼
┌─────────────┐
│  OPTIMIZER  │  src/optimization/optimizer.py
│             │  Constant Folding, Strength Reduction, DCE
└──────┬──────┘
       │  Optimized List[Instruction]
       ▼
┌──────────────────────┐   ┌────────────────────────────────┐
│  IR INTERPRETER      │   │  x86-64 & RISC-V BACKENDS      │
│  src/main.py         │   │  src/backend/                  │
│  Executes IR in Python│   │  Emits NASM or GNU AS Assembly │
└──────────────────────┘   └────────────────────────────────┘
```

---

### 4.1 Phase 1 — Lexer

**File**: `src/frontend/lexer.py`

The lexer converts raw source text into a flat list of `Token` objects. It operates with a **maximal munch** (longest-match) strategy using ordered regex patterns.

#### Token Structure
```python
Token(type: TokenType, value: str, line: int, column: int)
```

#### Token Types (selected)

| Category | Tokens |
|---|---|
| Keywords | `KW_INT`, `KW_BOOL`, `KW_VOID`, `KW_IF`, `KW_ELSE`, `KW_WHILE`, `KW_FOR`, `KW_RETURN`, `KW_CONST`, `KW_TRUE`, `KW_FALSE`, `KW_PRINT`, `KW_READ_INT`, `KW_BREAK`, `KW_CONTINUE` |
| Literals | `INTEGER`, `FLOAT`, `CHAR` |
| Identifiers | `IDENTIFIER` |
| Arithmetic | `PLUS`, `MINUS`, `STAR`, `SLASH`, `MODULO` |
| Relational | `LT`, `GT`, `LTE`, `GTE`, `EQ`, `NEQ` |
| Logical | `AND`, `OR`, `NOT` |
| Assign / Mutate | `ASSIGN`, `INCREMENT`, `DECREMENT` |
| Delimiters | `LPAREN`, `RPAREN`, `LBRACE`, `RBRACE`, `LBRACKET`, `RBRACKET`, `SEMICOLON`, `COMMA` |
| End | `EOF` |

#### Comment Handling
- `// ...` — Single-line comment: matched by regex `//[^\n]*` and discarded.
- `/* ... */` — Block comment: detected before the token loop. If `*/` is found, the entire block is skipped. If `*/` is **not** found, a `Lexical Error` is raised immediately.

#### Illegal Characters
Any character not matching any token pattern raises:
```
Lexical Error: Unexpected character 'X' at LINE:COL
```
Characters explicitly **not** tokenized: `$`, `@`, `#`, `^`, single `&`, single `|`.

---

### 4.2 Phase 2 — Parser

**File**: `src/frontend/parser.py`

The parser uses **recursive descent** (top-down, hand-written) to transform the token stream into an **Abstract Syntax Tree (AST)**.

#### Grammar (selected productions)
```
program         → declaration*
declaration     → func_decl | stmt
func_decl       → type IDENTIFIER '(' params? ')' block
params          → param (',' param)*
param           → type IDENTIFIER ('[' ']')?
type            → 'int' | 'bool' | 'void' | 'float'
block           → '{' stmt* '}'
stmt            → var_decl | if_stmt | while_stmt | for_stmt
                | return_stmt | break_stmt | continue_stmt
                | expr_stmt | print_stmt
var_decl        → ('const')? type IDENTIFIER ('[' INTEGER ']')? ('=' expr)? ';'
expr            → assignment | logical_or
assignment      → IDENTIFIER '=' expr
                | IDENTIFIER '[' expr ']' '=' expr
logical_or      → logical_and ('||' logical_and)*
logical_and     → equality ('&&' equality)*
equality        → relational (('=='|'!=') relational)*
relational      → addition (('<'|'>'|'<='|'>=') addition)*
addition        → multiplication (('+'|'-') multiplication)*
multiplication  → unary (('*'|'/'|'%') unary)*
unary           → ('!'|'++'|'--') unary | primary
primary         → INTEGER | FLOAT | 'true' | 'false'
                | IDENTIFIER | IDENTIFIER '(' args? ')'
                | IDENTIFIER '[' expr ']'
                | '(' expr ')'
                | 'readInt' '(' ')'
```

#### Key Parser Behaviors
- **Array size validation**: `int arr[0]` and `int arr[-5]` both raise `Syntax Error` — the parser validates that the integer size token satisfies `size > 0`. Negative sizes fail even earlier because `-` is not an `INTEGER` token.
- **Const without initializer**: `const int x;` raises `Syntax Error: Const variable must be initialized`.
- **Const function**: `const void main() {}` raises `Syntax Error: Functions cannot be const`.
- **Increment desugaring**: `++x` is lowered to `Assignment(x, BinaryExpr(x, +, 1))` by the parser. This means the const check fires at the Assignment level, not the UnaryExpr level.

#### Implementation Architecture (Recreation Details)
To reconstruct the Parser from scratch:
1. **Core Pattern**: Implement a standard **Recursive Descent Predictive Parser**. You will need a `self._peek()` returning the current token and `self._match()` to consume tokens upon equality.
2. **Abstract Syntax Tree (AST)**: Build classes inheriting typically from `ASTNode` (e.g., `Program`, `BinaryExpr`, `IfStmt`). 
3. **Left-Factoring & Precedence**: Operators must strictly scale precedence through hierarchical nested functions (e.g., `parse_expr` calls `parse_logical_or` calls `parse_logical_and` ... down to `parse_primary`).
4. **Variable Declarations**: Always parse `const` keywords dynamically, binding properties to your AST `VarDecl` classes explicitly.

---

### 4.3 Phase 3 — Semantic Analyzer

**File**: `src/semantic/analyzer.py`  
**Support**: `src/semantic/symbol_table.py`

The Semantic Analyzer performs a **single-pass tree walk** over the AST, maintaining a stack of scopes (a `SymbolTable`).

#### Symbol Table
Each `Symbol` stores:
```python
Symbol(name: str, type_name: str, category: str, is_const: bool)
```
`category` is one of: `'variable'`, `'function'`.

Function symbols additionally receive a `param_types: list[str]` attribute after their parameters are processed.

#### Checks Performed

| Check | Error Raised When |
|---|---|
| Undeclared variable | `print(z)` and `z` was never declared |
| Redeclaration same scope | `int x = 1; int x = 2;` in the same `{}` block |
| Const assignment | Assigning any value to a `const` variable |
| Type mismatch — variable decl | `int x = true;` |
| Type mismatch — assignment | `x = true;` where `x` is `int` |
| Type mismatch — binary operation | `true + 1;` (bool + int not permitted) |
| Type mismatch — array index | `arr[true]` — index must be `int` |
| Type mismatch — array element assign | `arr[0] = true;` where `arr` is `int[]` |
| Wrong argument count | `foo(1)` when `foo` expects 2 parameters |
| Wrong argument type | `foo(arr)` when `foo` expects `int`, not `int[]` |
| Non-array indexed | `int x = 5; x[0]` |
| `break` outside loop | `break;` at function top level |
| `continue` outside loop | `continue;` at function top level |
| Missing return statement | Non-`void` function with no guaranteed return path |
| Duplicate function declaration | `void foo() {} void foo() {}` |
| Call variable as function | `int x = 5; x();` |
| Call undeclared function | `ghost();` |
| Relational result used as int | `int x = (3 < 5) + 1;` — `bool + int` is Type Error |

#### Return Path Analysis (`_body_has_return`)
A conservative tree-walking check that answers: *does this node always reach a `return`?*

Rules:
- `Block` — returns `True` only if **any** statement in the list is a guaranteed return.
- `ReturnStmt` — always `True`.
- `IfStmt` — `True` only if **both** `then_branch` and `else_branch` (must exist) return.
- `WhileStmt` / `ForStmt` — always `False` (conservative — loop may never execute).

#### Implementation Architecture (Recreation Details)
To reconstruct Semantic Validation:
1. **Scope Logic**: Build a `SymbolTable` natively acting as a physical Stack (`List[dict]`). Upon hitting `ast.Block` (from functions or conditions), invoke `push_scope()`. Complete traversing the block, then call `pop_scope()`.
2. **Type Propagation**: Utilize the **Visitor Pattern**. Walk precisely bottom-up natively verifying left and right branches (e.g. `visit_BinaryExpr` checks `left_type == right_type`). Assign attributes like `node._semantic_type` physically to the AST enabling the IR Generator to know formats seamlessly.
3. **Function Parameters**: Before validating function bodies dynamically, map the explicit parameters directly onto the topmost symbol table scope to prevent undefined references.

---

### 4.4 Phase 4 — IR Generator

**File**: `src/ir/ir_gen.py`  
**Types**: `src/ir/instructions.py`

The IR Generator lowers the validated AST into **Three-Address Code (TAC)** — a flat list of `Instruction` objects.

#### Instruction Structure
```python
Instruction(opcode: OpCode, arg1=None, arg2=None, result=None)
```

> [!IMPORTANT]
> Field conventions differ by opcode. Always refer to the IR Instruction Set Reference (Section 7) for the exact `arg1`/`arg2`/`result` mapping of each instruction. Do **not** assume `result` is always the destination — for several opcodes it is not.

#### Variable Renaming (SSA-lite)
Every declared variable is renamed to `name_N` where `N` is a monotonically increasing counter (e.g., `x` → `x_0`, `i` → `i_1`). This prevents name collisions across nested scopes without full SSA form.

Compiler-generated temporaries are named `tN` (e.g., `t0`, `t1`).

#### Short-Circuit Evaluation for `&&` / `||`
```
// a || b
MOV t_sc 1
JMP_IF_FALSE a L_false    // if a is false, check b
JMP L_true                // a is true, short-circuit
LABEL L_false
JMP_IF_FALSE b L_end      // if b is also false → false result
LABEL L_true
MOV t_sc 1
LABEL L_end
```

#### For Loop Lowering
```c
for (int i = 0; i < 10; ++i) { body }
```
Lowers to:
```
MOV i_1 0          // init
LABEL L_loop
LT t0 i_1 10
JMP_IF_FALSE t0 L_exit   // condition check
body...
LABEL L_update
ADD t1 i_1 1       // update (++i desugared)
MOV i_1 t1
JMP L_loop
LABEL L_exit
```

#### Implementation Architecture (Recreation Details)
To reconstruct the Intermediate Representation Generator:
1. **SSA Versioning Memory**: Keep a centralized dictionary tracking how many times a physical variable name natively exists locally mapping new iterations out as `x_0`, `x_1` guaranteeing zero aliasing overlaps implicitly bypassing nested definitions natively in C.
2. **Linear Instruction Emits**: Translate AST scopes using flat lists. Each `visit` returns its designated storage destination (e.g., `t0`), generating and appending opcodes concurrently. `result = left + right` emits `ADD t0 left right` and actively passes `t0` mathematically to outer nodes sequentially.
3. **Label Caching**: Construct dynamically unique strings natively creating logical boundaries representing raw program sequences sequentially.

---

### 4.5 Phase 5 — Optimizer

**File**: `src/optimization/optimizer.py` (pipeline runner)  
**Passes**: `constant_fold.py`, `strength_reduction.py`, `dead_code.py`

Passes are run iteratively by the `Optimizer` pipeline simulating complete textbook architectures natively guaranteeing advanced performance loops:

```
Input IR → Strength Reduction → Common Subexp Elimination → Copy Propagation → Constant Folding → Cleanup CSE → Dead Code Elimination → Output IR
```
These 6 fully autonomous models execute securely traversing instructions checking logic overlaps robustly dynamically accelerating your pipeline seamlessly.

Each pass is independently testable.

#### Constant Folding & Propagation
- Tracks a `constants` dict mapping variable names to known constant values.
- Folds `ADD t0 3 4` → `MOV t0 7`.
- Propagates: if `x_0 = 5` is known, then `ADD t1 x_0 3` becomes `MOV t1 8`.

#### Copy Propagation & Common Subexpression Elimination (CSE)
- **CSE** securely manages redundant overlaps merging duplicated nodes. If `t1 = ADD a b` and later `t2 = ADD a b`, it replaces allocations swapping `t2` identically to `t1`.
- **Copy Prop** autonomously evaluates chained alias arrays recursively checking values mapping `MOV a b` securely passing origin points physically tracking aliases saving registry fetches.

#### Pass 2 — Strength Reduction
Replaces expensive operations with cheaper bitwise equivalents:

| Pattern | Replacement | Condition |
|---|---|---|
| `MUL result x N` | `LSHIFT result x log2(N)` | N is power of 2, N ≥ 2 |
| `DIV result x N` | `RSHIFT result x log2(N)` | N is power of 2, N ≥ 2 |
| `MUL result x 0` | `MOV result 0` | N == 0 |
| `MUL result x 1` | `MOV result x` | N == 1 |

#### Pass 3 — Dead Code Elimination (DCE)
- Builds the set of **used variables** by scanning all `arg1` and `arg2` fields across the entire instruction list.
- `ASTORE` is special: its `result` field holds the value-to-store (not a definition), so `result` is explicitly added to the used-set.
- Instructions with **side effects** are unconditionally kept: `CALL`, `PARAM`, `PARAM_REF`, `LOAD_PARAM`, `LOAD_PARAM_REF`, `ASTORE`, `ALOAD`, `ARR_DECL`, `PRINT`, `RETURN`, `LABEL`, `JMP`, `JMP_IF_FALSE`, `FUNC_START`, `FUNC_END`.
- Pure instructions (arithmetic, MOV) are removed if their `result` variable is not in the used-set.
- DCE iterates to convergence (multiple passes until no change).

---

### 4.6 Phase 6 — Backends (x86-64 & RISC-V)

**Files**: `src/backend/`

The backend lowers optimized IR into native assembly:
- **x86-64**: Emits NASM assembly.
- **RISC-V**: Emits 64-bit GNU AS assembly.

Both backends use a simplified stack-machine translating directly from Three-Address Code.

#### Calling Convention (simplified)
- Function arguments are pushed **right-to-left** onto the stack before a `call` instruction.
- The return value is passed through `rax`.
- `rbp` is used as the frame pointer. Each function establishes a stack frame with `push rbp / mov rbp, rsp`.
- Local variables are addressed as `[rbp - N]` where `N` depends on declaration order.

> [!WARNING]
> **Stack alignment** before external calls (like `printf`) is not strictly enforced per the System V ABI. The backend is correct for Trisynth's own calling convention but does not guarantee ABI compliance for linking with C libraries without modification.

#### Array & String Memory Behavior
Arrays securely initialize directly onto memory stack constraints mapping pointers linearly generating blocks using `sub rsp, SIZE*8` natively evaluating physical byte bounds mapped over `[rbp - index]`.

Strings implicitly bypass complex definitions! Literals natively construct static constraints utilizing standard `.data` array layouts dynamically referencing physical pointers assigning `lea rax, [rel str_0]` directly linking strings to regular stack local boundaries evaluating perfectly formatted formats including escaping backslashes over robust NASM blocks!

#### I/O
- `print(x)` is lowered to `printf("%ld\n", x)` via an external C runtime call.
- `readInt()` is lowered to `scanf("%ld", &x)`.

#### Implementation Architecture (Recreation Details)
To rebuild the Machine Backends completely from scratch:
1. **Stack Memory Manager**: Don't use heavy graph coloring explicitly! Establish a `StackFrame` model allocating simple sequential `offset` byte tracking. E.g. Integer registers allocate offsets natively pushing `[rbp - 8]` and `[s0 - 8]`.
2. **Pure Accumulator Flow**: Limit arithmetic logic fundamentally onto `rax` (X86) or `t0` (RISC-V). Ex: to compute `a = b + c`, write backend instructions evaluating `mov rax, b`, `mov rbx, rax`, `mov rax, c`, `add rax, rbx`, `mov a, rax`. This guarantees registers never structurally collide regardless of execution depth dynamically mapped across IR boundaries natively.
3. **Argument Pushing**: Track parameters logically. Upon detecting `PARAM` or `PARAM_REF`, cache variable constraints linearly inside python arrays securely evaluating lists recursively right-to-left dynamically emitting localized push logic natively aligning bytes (e.g., `addi sp, sp, -8; sd t0, 0(sp)` in GNU RISC-V) right before external Call hooks securely matching calling parameters physically.

---

### 4.7 IR Interpreter

**File**: `src/main.py` — class `IRInterpreter`

The IR Interpreter executes the optimized IR directly in Python, providing fast execution feedback without requiring an assembler or linker. It is used for all automated tests.

#### Execution Model
```python
IRInterpreter(ir_list).run()
```
- Maintains `self.locals` — a dict mapping IR variable names to Python values.
- Maintains `self.arrays` — a dict mapping array names to Python lists.
- Maintains `self.labels` — a pre-built dict mapping label names to instruction indices (built at `__init__` time for O(1) jumps).
- Maintains `self.functions` — a dict mapping function names to their `FUNC_START` index.
- Maintains `self.call_stack` — a list of saved frames for function calls.
- Maintains `self.return_value` — holds the most recent function return value between `RETURN` and the CALL site that reads it.

#### Key Execution Rules
- `LABEL` instructions are skipped (they are only used for jump targets).
- `JMP` sets `self.pc = self.labels[label_name]`, then the main loop increments `pc` by 1 — so execution resumes at the instruction **after** the `LABEL`.
- `JMP_IF_FALSE` conditionally jumps (does not jump if condition is truthy).
- `CALL` pushes a frame (`pc`, `locals`, `result_register`) onto `call_stack`, resets `locals = {}`, and jumps to the function's `FUNC_START`.
- `RETURN` stores the value in `self.return_value`, pops the call stack, restores caller's locals and pc, then writes `return_value` into `state['result']` in the caller's `locals`.
- `FUNC_END` without a call stack (i.e., end of `main`) terminates execution.

---

## 5. Error Reference

### 5.1 Lexical Errors

| Situation | Error Message |
|---|---|
| Unknown character (`$`, `@`, `^`, `&`, `\|`) | `Lexical Error: Unexpected character 'X' at L:C` |
| Unclosed block comment `/*` | `Lexical Error: Unclosed block comment starting at L:C` |

### 5.2 Syntax Errors

| Situation | Error Message |
|---|---|
| Missing `;` after statement | `Syntax Error at L:C: Expected ';'` |
| Missing `)` after condition | `Syntax Error at L:C: Expected ')'` |
| Missing `{` or `}` | `Syntax Error: Expected '{' ...` |
| `const` function declaration | `Syntax Error: Functions cannot be const` |
| `const` variable without initializer | `Syntax Error: Const variable must be initialized` |
| Array size ≤ 0 | `Array size must be a positive integer at L:C` |
| Array size is not an integer token | `Syntax Error at L:C: Expected array size.` |
| Empty expression in assignment (`x = ;`) | `Expected expression at L:C, found SEMICOLON` |
| Function declared with no body | Parser error at `{` |
| Missing return type in function | Parser halts at identifier |

### 5.3 Semantic / Type Errors

| Situation | Error Message |
|---|---|
| Undeclared variable `z` | `Semantic Error: Undeclared variable 'z'.` |
| Redeclaration `int x; int x;` in same scope | `Semantic Error: Symbol 'x' already declared in this scope.` |
| Const reassignment | `Semantic Error: Cannot assign to const variable 'x'.` |
| `break` outside loop | `Semantic Error: 'break' outside of loop.` |
| `continue` outside loop | `Semantic Error: 'continue' outside of loop.` |
| Calling undeclared function | `Semantic Error: Undeclared variable 'ghost'.` |
| Calling variable as function | `Semantic Error: 'x' is not a function.` |
| Wrong argument count | `Type Error: Function 'foo' expects N arguments, got M.` |
| Wrong argument type | `Type Error: Argument N of 'foo' expects 'T', got 'U'.` |
| Type mismatch in declaration | `Type Error: Cannot assign 'T' to 'U' for variable 'x'.` |
| Type mismatch in assignment | `Type Error: Cannot assign 'T' to 'U' for variable 'x'.` |
| Type mismatch in binary op | `Type Error: Type mismatch in binary operation 'OP'. Got 'T' and 'U'.` |
| Index is not `int` | `Type Error: Array index must be int, got 'T'.` |
| Indexing a non-array | `Type Error: 'x' is not an array.` |
| Array element type mismatch | `Type Error: Cannot assign 'T' to 'U' array element.` |
| Missing return in non-void function | `Missing return statement in non-void function 'name'` |
| Duplicate function definition | `Semantic Error: Symbol 'foo' already declared in this scope.` |

---

## 6. Optimization Reference

### Constant Folding Examples

| Before | After |
|---|---|
| `int x = 3 * 4;` | `int x = 12;` (compile-time) |
| `int y = x + 0;` where x=12 | `int y = 12;` |
| `if (true && false)` | Short-circuit evaluated at IR level |

### Strength Reduction Table

| Arithmetic | Bitwise Equivalent | Condition |
|---|---|---|
| `x * 2` | `x << 1` | 2 = 2¹ |
| `x * 4` | `x << 2` | 4 = 2² |
| `x * 8` | `x << 3` | 8 = 2³ |
| `x / 2` | `x >> 1` | 2 = 2¹ |
| `x / 4` | `x >> 2` | 4 = 2² |
| `x * 0` | `0` | zero mul |
| `x * 1` | `x` | identity |

### Dead Code Elimination: What is and isn't Removed

**Safe to remove** (never-used pure computation):
```c
void main() {
    int dead = 999;    // Removed if never read
    int live = 42;
    print(live);
}
```
**Never removed** (side-effecting):
```
CALL, PARAM, PRINT, RETURN, ASTORE, ALOAD, ARR_DECL, JMP, JMP_IF_FALSE, LABEL
```

---

## 7. IR Instruction Set Reference

| Opcode | `arg1` | `arg2` | `result` | Semantics |
|---|---|---|---|---|
| `MOV` | source value/var | — | dest var | `result = arg1` |
| `ADD` | left operand | right operand | dest var | `result = arg1 + arg2` |
| `SUB` | left | right | dest | `result = arg1 - arg2` |
| `MUL` | left | right | dest | `result = arg1 * arg2` |
| `DIV` | left | right | dest | `result = arg1 / arg2` |
| `MOD` | left | right | dest | `result = arg1 % arg2` |
| `LSHIFT` | left | shift count | dest | `result = arg1 << arg2` |
| `RSHIFT` | left | shift count | dest | `result = arg1 >> arg2` |
| `LT` | left | right | dest | `result = (arg1 < arg2)` |
| `GT` | left | right | dest | `result = (arg1 > arg2)` |
| `LTE` | left | right | dest | `result = (arg1 <= arg2)` |
| `GTE` | left | right | dest | `result = (arg1 >= arg2)` |
| `EQ` | left | right | dest | `result = (arg1 == arg2)` |
| `NEQ` | left | right | dest | `result = (arg1 != arg2)` |
| `JMP` | target label | — | — | Unconditional jump to `labels[arg1]` |
| `JMP_IF_FALSE` | condition var | target label | — | Jump to `labels[arg2]` if `arg1 == 0` |
| `LABEL` | label name | — | — | Jump target — no-op at execution |
| `FUNC_START` | function name | — | — | Marks function entry |
| `FUNC_END` | function name | — | — | Marks function exit / triggers return-from-call |
| `RETURN` | return value (or None) | — | — | Sets `return_value`, pops call stack |
| `CALL` | function name | arg count | dest var | Saves frame, jumps to `functions[arg1]`; result stored in `result` after return |
| `PARAM` | value to push | — | — | Push argument before a `CALL` |
| `PARAM_REF` | array name | — | — | Push array reference argument |
| `LOAD_PARAM` | param index | — | dest var | Pop next param from stack → `result` |
| `LOAD_PARAM_REF` | param index | — | dest var | Pop next array-ref param → `result` |
| `ARR_DECL` | size | — | array name | Allocate array of `arg1` elements in `arrays[result]` |
| `ASTORE` | array name | index | value | `arrays[arg1][arg2] = result` |
| `ALOAD` | array name | index | dest | `result = arrays[arg1][arg2]` |
| `PRINT` | value/var | — | — | Output integer `arg1` to stdout appended internally mapped to newline format |
| `PRINT_STR` | string_tgt | — | — | Directly mapping evaluated text bounds seamlessly resolving `\n` formats over stdout securely |
| `LOAD_STR` | literal_raw | — | dest | Points memory referencing isolated `.data` chunks representing the static characters into `result` registers |

---

## 8. Test Suite

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
- **Bug Hunter tests** deliberately try edge cases that are easy to miss: single `&`/`|`, unclosed comments, const-through-increment, relational-as-int, duplicate functions, wrong argument counts.

---

## 9. Limitations & Known Behaviors

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

## 10. Future Work

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

## 11. Contributors

| Name | ID |
|---|---|
| V. Chitraksh | CS23B054 |
| P. Sathvik | CS23B042 |
| S. Danish Dada | CS23B047 |

---

*Trisynth — A Compiler Built to Be Read.*
