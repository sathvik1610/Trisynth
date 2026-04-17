# Trisynth Technical Documentation

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


---

# Trisynth Compiler — Backend & Code Generation

> **This document is a continuation of the main README.**
> It covers everything that happens **after the optimization passes** —
> from IR to native assembly for two architectures.

---

# python src/main.py tests/complex_test.tri --arch x86    # x86 only
# python src/main.py tests/complex_test.tri --arch riscv  # RISC-V only
# python src/main.py tests/complex_test.tri --arch both   # both (default)


## Table of Contents

1. [Where We Left Off — Optimized IR](#where-we-left-off--optimized-ir)
2. [Stage 6 — IR Interpreter (Verification)](#stage-6--ir-interpreter-verification)
3. [Stage 7 — X86-64 Code Generation](#stage-7--x86-64-code-generation)
4. [Stage 8 — RISC-V 64-bit Code Generation](#stage-8--risc-v-64-bit-code-generation)
5. [X86-64 vs RISC-V Side-by-Side](#x86-64-vs-risc-v-side-by-side)
6. [Requirements](#requirements)
7. [Running the Compiler](#running-the-compiler)
8. [Building & Running X86-64 Output](#building--running-x86-64-output)
9. [Building & Running RISC-V Output](#building--running-risc-v-output)
10. [Full Example — What You Should See](#full-example--what-you-should-see)

---

## Where We Left Off — Optimized IR

After all six optimization passes run, the IR is stripped down to only what is
essential for execution. For example, the `complex_test.tri` program goes from
**50+ IR instructions** down to just **7**:

```
FUNC_START helper
LOAD_PARAM a_0 0
LOAD_PARAM b_1 1
GT t0 a_0 b_1
JMP_IF_FALSE t0 L0
RETURN a_0
LABEL L0
RETURN b_1
FUNC_END helper

FUNC_START main
PRINT 316          ← entire expression folded to a constant at compile time
PARAM 5
PARAM 3
CALL t14 helper 2
PRINT t14          ← result of helper(5, 3)
PRINT 128          ← x*y folded to 128
PRINT 128
FUNC_END main
```

This optimized IR is what both code generators receive as input.

---

## Stage 6 — IR Interpreter (Verification)

Before emitting any assembly, the compiler **executes the IR directly** in Python.
This is a safety net — if the interpreter output matches the expected values,
the optimized IR is correct and safe to lower to assembly.

```
[6] Execution:
316
5
128
128

  ✅ Execution Complete
```

If this stage fails, there is a bug in the IR or optimizer — **not** in the
code generators. This separation makes debugging much easier.

---

## Stage 7 — X86-64 Code Generation

**File:** `src/backend/codegen.py`
**Class:** `X86Generator`
**Output:** `output.asm` (NASM syntax, ELF64 format)

### Strategy

The backend uses a **pure stack machine** approach. Every variable — whether a
user variable like `x_2` or a compiler temporary like `t14` — lives in a fixed
slot on the stack at `[rbp - N]`. There is no register allocation.

This keeps the code generator simple and correct at the cost of some performance,
which is acceptable for a compiler of this scope.

### Stack Frame Layout

```
High address
┌──────────────────────┐
│  caller's stack      │
│  arg1 at [rbp + 24]  │  ← second argument passed by caller
│  arg0 at [rbp + 16]  │  ← first argument passed by caller
│  return address      │  ← pushed by `call` instruction
├──────────────────────┤  ← rbp  (frame pointer, set by `push rbp / mov rbp, rsp`)
│  local var 1         │  ← [rbp -  8]
│  local var 2         │  ← [rbp - 16]
│  local var 3         │  ← [rbp - 24]
│  ...                 │
└──────────────────────┤  ← rsp  (stack pointer, lowered by `sub rsp, N`)
Low address
```

### Function Prologue & Epilogue

Every function begins with:
```nasm
push rbp            ; save caller's frame pointer
mov  rbp, rsp       ; set our frame pointer to current stack top
sub  rsp, N         ; reserve N bytes for local variables
```

And ends with:
```nasm
.exit_funcname:
    mov  rsp, rbp   ; discard all locals by restoring stack pointer
    pop  rbp        ; restore caller's frame pointer
    ret             ; return to caller (pops return address into rip)
```

### Calling Convention

Arguments are pushed **right-to-left** before a `call`:
```nasm
; call helper(5, 3)
mov rax, 3          ; load second argument (rightmost first)
push rax            ; push it onto the stack
mov rax, 5          ; load first argument
push rax            ; push it
call helper         ; push return address, jump to helper
add rsp, 16         ; clean up 2 args × 8 bytes = 16 bytes after return
mov [rbp - 8], rax  ; store return value (rax) into result slot
```

Inside the callee, parameters are loaded from above the frame pointer:
```nasm
mov rax, [rbp + 16]  ; first arg  (a)
mov rax, [rbp + 24]  ; second arg (b)
```

### Printf Alignment Fix

The System V ABI requires `rsp` to be **16-byte aligned** before any `call`.
A naïve `and rsp, -16` would silently corrupt `[rbp - N]` addressing.
The fix saves and restores `rsp` around every `printf` call:

```nasm
mov rsi, rax            ; argument: the integer value to print
lea rdi, [rel fmt_int]  ; argument: pointer to "%ld\n" format string (RIP-relative)
xor rax, rax            ; rax = 0 (required by printf ABI: no vector registers used)
mov rbx, rsp            ; save current rsp before alignment
and rsp, -16            ; align rsp down to nearest 16-byte boundary
call printf             ; call C printf
mov rsp, rbx            ; restore rsp exactly — [rbp-N] offsets remain valid
```

### Complete Annotated Output (complex_test.tri)

```nasm
section .data
    fmt_int db "%ld", 10, 0     ; format string: "%ld\n" + null terminator

section .text
    extern printf               ; declare printf from C standard library
    extern scanf                ; declare scanf (used by readInt())

; ── helper function ─────────────────────────────────────────────────────────

global helper                   ; make symbol visible to linker
helper:
    push rbp                    ; save caller's rbp
    mov  rbp, rsp               ; establish our frame pointer
    sub  rsp, 32                ; reserve 32 bytes: a(8) + b(8) + t0(8) + pad(8)

    ; LOAD_PARAM a_0  (index 0 → [rbp + 16])
    mov rax, [rbp + 16]         ; load first argument from caller's stack
    mov [rbp - 8], rax          ; store into local slot for a_0

    ; LOAD_PARAM b_1  (index 1 → [rbp + 24])
    mov rax, [rbp + 24]         ; load second argument
    mov [rbp - 16], rax         ; store into local slot for b_1

    ; GT t0  a_0  b_1   (t0 = a > b)
    mov rax, [rbp - 8]          ; load a_0
    cmp rax, [rbp - 16]         ; compare a with b
    setg al                     ; al = 1 if a > b, else 0
    movzx rax, al               ; zero-extend al → rax
    mov [rbp - 24], rax         ; store result into t0

    ; JMP_IF_FALSE t0  L0
    mov rax, [rbp - 24]         ; load condition (t0)
    cmp rax, 0                  ; is it false (zero)?
    je  L0                      ; if false, jump to L0 (return b)

    ; RETURN a_0
    mov rax, [rbp - 8]          ; load a into rax (return value register)
    mov rsp, rbp                ; tear down frame
    pop rbp
    ret                         ; return to caller

L0:
    ; RETURN b_1
    mov rax, [rbp - 16]         ; load b into rax
    mov rsp, rbp
    pop rbp
    ret

.exit_helper:                   ; fallthrough epilogue (unreachable here, but emitted for safety)
    mov rsp, rbp
    pop rbp
    ret

; ── main function ────────────────────────────────────────────────────────────

global main
main:
    push rbp
    mov  rbp, rsp
    sub  rsp, 16                ; reserve 16 bytes for t14 (call result)

    ; PRINT 316  (constant folded by optimizer)
    mov rax, 316                ; load immediate constant
    mov rsi, rax                ; printf arg2: the integer value
    lea rdi, [rel fmt_int]      ; printf arg1: format string pointer (RIP-relative)
    xor rax, rax                ; rax=0: no floating-point args
    mov rbx, rsp                ; save rsp before alignment
    and rsp, -16                ; align to 16-byte boundary
    call printf
    mov rsp, rbx                ; restore rsp

    ; PARAM 5 / PARAM 3 / CALL t14 helper 2
    mov rax, 3                  ; push second argument (3) first (right-to-left)
    push rax
    mov rax, 5                  ; push first argument (5)
    push rax
    call helper                 ; call helper(5, 3)
    add rsp, 16                 ; clean up 2 × 8 = 16 bytes of arguments
    mov [rbp - 8], rax          ; store return value into t14

    ; PRINT t14
    mov rax, [rbp - 8]          ; load t14 (= 5, since helper(5,3) returns 5)
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx

    ; PRINT 128  (x*y = 16*8 = 128, folded at compile time)
    mov rax, 128
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx

    ; PRINT 128
    mov rax, 128
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx

.exit_main:
    mov rsp, rbp
    pop rbp
    ret
```

---

## Stage 8 — RISC-V 64-bit Code Generation

**File:** `src/backend/codegen_riscv.py`
**Class:** `RISCVGenerator`
**Output:** `output_riscv.s` (GNU Assembler syntax)
**Architecture:** RV64GC (RISC-V 64-bit, General + Compressed extensions)

### What is RV64GC?

| Component | Meaning |
|-----------|---------|
| **RV64** | 64-bit base integer instruction set. All registers are 64-bit. |
| **G** | General-purpose shorthand for IMAFD (Integer, Multiply, Atomic, Float, Double) |
| **C** | Compressed instructions — 16-bit encodings for common operations (reduces code size) |

This is the standard ISA used by:
- **SiFive HiFive** development boards
- **StarFive VisionFive** single-board computers
- **QEMU** `virt` machine target
- Most Linux RISC-V distributions

### Key Registers Used

| Register | ABI Name | Role in this compiler |
|----------|----------|-----------------------|
| `x2` | `sp` | Stack pointer |
| `x8` | `s0` / `fp` | Frame pointer (our base for all locals) |
| `x1` | `ra` | Return address (saved/restored in prologue/epilogue) |
| `x5` | `t0` | Primary scratch — used like `rax` in x86 |
| `x6` | `t1` | Secondary scratch — used like `rbx` in x86 |
| `x7` | `t2` | Tertiary scratch — address holding for ASTORE |
| `x10` | `a0` | First argument / return value (for printf and function returns) |
| `x11` | `a1` | Second argument to printf (the integer value) |

### Stack Frame Layout

```
High address
┌──────────────────────────┐
│  caller's stack          │
│  arg1 at  24(s0)         │  ← second argument passed by caller
│  arg0 at  16(s0)         │  ← first argument passed by caller
├──────────────────────────┤
│  saved ra at  8(s0)      │  ← return address saved in prologue
│  saved s0 at  0(s0)      │  ← caller's frame pointer saved here
├──────────────────────────┤  ← s0  (frame pointer)
│  local var 1  -8(s0)     │
│  local var 2  -16(s0)    │
│  local var 3  -24(s0)    │
│  ...                     │
└──────────────────────────┤  ← sp
Low address
```

### Function Prologue & Epilogue

```asm
funcname:
    addi sp, sp, -N         ; grow stack by N bytes (locals + 16 for ra/s0)
    sd   ra, (N-8)(sp)      ; save return address
    sd   s0, (N-16)(sp)     ; save caller's frame pointer
    addi s0, sp, (N-16)     ; set s0 = our frame pointer

.exit_funcname:
    ld   ra, (N-8)(sp)      ; restore return address
    ld   s0, (N-16)(sp)     ; restore frame pointer
    addi sp, sp, N          ; shrink stack back
    ret                     ; return (pseudoinstruction for jalr x0, ra, 0)
```

### How Comparisons Work (no flags register)

Unlike x86, RISC-V has **no flags register**. Every comparison produces
an integer result (0 or 1) in a register using dedicated instructions:

```
# a > b
slt  t0, t0(b), t1(a)     ; t0 = 1 if b < a  (i.e. a > b)

# a == b
sub  t0, t1(a), t0(b)     ; t0 = a - b
seqz t0, t0               ; t0 = 1 if t0 == 0  (i.e. a == b)

# a != b
sub  t0, t1(a), t0(b)
snez t0, t0               ; t0 = 1 if t0 != 0

# a <= b  (not a single instruction — derived)
slt  t0, t0(b), t1(a)     ; t0 = (b < a)
xori t0, t0, 1            ; t0 = NOT (b < a) = (a <= b)

# a >= b
slt  t0, t1(a), t0(b)     ; t0 = (a < b)
xori t0, t0, 1            ; t0 = NOT (a < b) = (a >= b)
```

### Complete Annotated Output (complex_test.tri)

```asm
.section .data
fmt_int: .string "%ld\n"        ; format string for printf

.section .text

# ── helper function ──────────────────────────────────────────────────────────

.globl helper
helper:
    addi sp, sp, -48            ; grow stack: 32 bytes locals + 16 for ra/s0
    sd   ra, 40(sp)             ; save return address
    sd   s0, 32(sp)             ; save caller's frame pointer
    addi s0, sp, 32             ; s0 = frame pointer

    # LOAD_PARAM a_0  (index 0 → 16(s0))
    ld   t0, 16(s0)             ; load first argument from caller's stack
    sd   t0, -8(s0)             ; store into local slot for a_0

    # LOAD_PARAM b_1  (index 1 → 24(s0))
    ld   t0, 24(s0)             ; load second argument
    sd   t0, -16(s0)            ; store into local slot for b_1

    # GT t0  a_0  b_1   (t0 = a > b)
    ld   t0, -8(s0)             ; load a_0 into t0
    mv   t1, t0                 ; copy a into t1
    ld   t0, -16(s0)            ; load b_1 into t0
    slt  t0, t0, t1             ; t0 = 1 if b < a  (equivalent to a > b)
    sd   t0, -24(s0)            ; store result into t0's slot

    # JMP_IF_FALSE t0  L0
    ld   t0, -24(s0)            ; load condition
    beqz t0, L0                 ; branch to L0 if condition is zero (false)

    # RETURN a_0
    ld   t0, -8(s0)             ; load a_0
    mv   a0, t0                 ; move return value into a0
    j    .exit_helper           ; jump to epilogue

L0:
    # RETURN b_1
    ld   t0, -16(s0)            ; load b_1
    mv   a0, t0                 ; move return value into a0
    j    .exit_helper

.exit_helper:
    ld   ra, 40(sp)             ; restore return address
    ld   s0, 32(sp)             ; restore frame pointer
    addi sp, sp, 48             ; shrink stack
    ret                         ; return to caller

# ── main function ─────────────────────────────────────────────────────────────

.globl main
main:
    addi sp, sp, -32            ; 16 bytes locals + 16 for ra/s0
    sd   ra, 24(sp)
    sd   s0, 16(sp)
    addi s0, sp, 16

    # PRINT 316
    li   t0, 316                ; load constant 316
    mv   a1, t0                 ; printf second arg: the integer value
    la   a0, fmt_int            ; printf first arg: format string address
    call printf

    # PARAM 5 / PARAM 3 / CALL t14 helper 2
    li   t0, 3                  ; second argument (rightmost pushed first)
    addi sp, sp, -8             ; grow stack for one argument
    sd   t0, 0(sp)              ; push 3

    li   t0, 5                  ; first argument
    addi sp, sp, -8
    sd   t0, 0(sp)              ; push 5

    call helper                 ; call helper — args at 0(sp) and 8(sp)
    addi sp, sp, 16             ; clean up 2 × 8 = 16 bytes
    mv   t0, a0                 ; move return value from a0 into t0
    sd   t0, -8(s0)             ; store into t14's stack slot

    # PRINT t14
    ld   t0, -8(s0)             ; load t14 (= 5)
    mv   a1, t0
    la   a0, fmt_int
    call printf

    # PRINT 128
    li   t0, 128
    mv   a1, t0
    la   a0, fmt_int
    call printf

    # PRINT 128
    li   t0, 128
    mv   a1, t0
    la   a0, fmt_int
    call printf

.exit_main:
    ld   ra, 24(sp)
    ld   s0, 16(sp)
    addi sp, sp, 32
    ret
```

---

## X86-64 vs RISC-V Side-by-Side

| Operation | X86-64 (NASM) | RISC-V 64 (GNU AS) |
|-----------|--------------|---------------------|
| Load constant | `mov rax, 42` | `li t0, 42` |
| Load from stack | `mov rax, [rbp - 8]` | `ld t0, -8(s0)` |
| Store to stack | `mov [rbp - 8], rax` | `sd t0, -8(s0)` |
| Add | `add rax, rbx` | `add t0, t1, t0` |
| Multiply | `imul rax, rbx` | `mul t0, t1, t0` |
| Left shift (imm) | `shl rax, 2` | `slli t0, t0, 2` |
| Right shift (imm) | `sar rax, 1` | `srai t0, t0, 1` |
| Compare a > b | `cmp rax, rbx` + `setg al` | `slt t0, t0(b), t1(a)` |
| Compare a == b | `cmp` + `sete al` | `sub` + `seqz` |
| Branch if false | `cmp rax, 0` + `je label` | `beqz t0, label` |
| Unconditional jump | `jmp label` | `j label` |
| Call function | `call func` | `call func` |
| Return value | `rax` | `a0` |
| Frame pointer | `rbp` | `s0` |
| Push to stack | `push rax` | `addi sp,sp,-8` + `sd t0,0(sp)` |
| Pop from stack | `pop rax` | `ld t0,0(sp)` + `addi sp,sp,8` |
| Return | `ret` | `ret` |

---

## Requirements

### For X86-64

| Tool | Purpose | Install |
|------|---------|---------|
| `nasm` | Assembles `.asm` → `.o` object file | `sudo apt install nasm` |
| `gcc` | Links `.o` + libc → executable | `sudo apt install gcc` |

### For RISC-V

| Tool | Purpose | Install |
|------|---------|---------|
| `gcc-riscv64-linux-gnu` | Cross-compiler: assembles + links RISC-V `.s` on x86 host | `sudo apt install gcc-riscv64-linux-gnu` |
| `qemu-user-static` | Emulates RISC-V CPU to run the binary on your x86 machine | `sudo apt install qemu-user-static` |

### Python

| Requirement | Version |
|-------------|---------|
| Python | 3.8 or higher |
| External packages | None — standard library only |

---

## Running the Compiler

```bash
# Navigate to the project root (inside WSL or on Linux)
cd /mnt/d/GitHub/Custom-Native-Compiler   # WSL path to Windows drive
# or
cd ~/Custom-Native-Compiler               # native Linux path

# Run both code generators (default)
python3 src/main.py tests/complex_test.tri

# Run x86-64 code generation only
python3 src/main.py tests/complex_test.tri --arch x86

# Run RISC-V code generation only
python3 src/main.py tests/complex_test.tri --arch riscv

# Run both explicitly
python3 src/main.py tests/complex_test.tri --arch both

# Interactive mode (type code directly)
python3 src/main.py --demo
```

After running, two output files appear in the project root:
- `output.asm` — x86-64 NASM assembly
- `output_riscv.s` — RISC-V GNU AS assembly

---

## Building & Running X86-64 Output

### On WSL (Ubuntu on Windows)

```bash
# Step 1 — Install tools (one time only)
sudo apt-get update
# Refreshes the package index from Ubuntu servers — do this before any install.

sudo apt install nasm gcc -y
# nasm : NASM assembler for x86-64
# gcc  : GNU C compiler used here as linker to attach the C runtime (printf etc.)
# -y   : auto-accept the install prompt

# Step 2 — Assemble the .asm file into an ELF64 object file
nasm -f elf64 output.asm -o output.o
# -f elf64  : output format is 64-bit ELF (the standard Linux object format)
# output.asm: our generated assembly source
# -o output.o : name of the object file to produce

# Step 3 — Link the object file into an executable
gcc output.o -o program -no-pie
# output.o   : the object file from nasm
# -o program : name of the final executable (avoid naming it "output" — 
#              there may already be a folder with that name in the project)
# -no-pie    : disable Position Independent Executable — our assembly uses
#              absolute addressing which is incompatible with PIE

# Step 4 — Run
./program
# Expected output:
# 316
# 5
# 128
# 128
```

### On Native Linux (Ubuntu / Debian)

Identical commands — no differences. WSL and native Ubuntu use the same
package manager and tool names.

---

## Building & Running RISC-V Output

### On WSL or Ubuntu (cross-compilation path)

This is the recommended approach. You compile on your x86 machine but
produce a RISC-V binary, then run it under QEMU CPU emulation.

```bash
# Step 1 — Install tools (one time only)
sudo apt-get update
# Refresh package list — required before installing any new packages.

sudo apt install gcc-riscv64-linux-gnu -y
# gcc-riscv64-linux-gnu : The RISC-V cross-compiler toolchain.
#   Includes:
#     riscv64-linux-gnu-as      (assembler)
#     riscv64-linux-gnu-ld      (linker)
#     riscv64-linux-gnu-gcc     (full compiler + linker frontend)
#   "Cross-compiler" means: runs on x86, produces RISC-V machine code.

sudo apt-get update --fix-missing
# Sometimes package mirrors are temporarily inconsistent.
# --fix-missing retries failed downloads and skips broken entries.

sudo apt install qemu-user-static -y
# qemu-user-static : QEMU in user-mode emulation.
#   Runs a single RISC-V ELF binary on an x86 machine by translating
#   RISC-V instructions to x86 on the fly.
#   "Static" version has no external dependencies — more reliable in WSL.

# Step 2 — Assemble + link in one command
riscv64-linux-gnu-gcc output_riscv.s -o program_riscv -static
# riscv64-linux-gnu-gcc : the cross-compiler frontend
# output_riscv.s        : our generated RISC-V assembly source
# -o program_riscv      : name of the output binary
# -static               : statically link libc into the binary.
#                         Required for qemu-user — the emulator cannot
#                         load dynamic libraries from a different architecture.

# Step 3 — Run under QEMU
qemu-riscv64-static ./program_riscv
# qemu-riscv64-static : emulates a RISC-V 64-bit CPU
# ./program_riscv     : the statically linked RISC-V binary to execute
#
# Expected output:
# 316
# 5
# 128
# 128
```

### On a Native RISC-V Board or VM

If you have a RISC-V device (e.g. StarFive VisionFive 2, SiFive Unmatched,
or a RISC-V QEMU full-system VM):

```bash
# No cross-compiler needed — use the native gcc
gcc output_riscv.s -o program_riscv
# gcc on a RISC-V machine already targets RISC-V natively.
# No -static needed since libc is available natively.

./program_riscv
# Run directly — no emulator needed.
```

---

## Full Example — What You Should See

Running the full pipeline on `complex_test.tri`:

```
==================================
           PROGRAM OUTPUT
==================================

316
5
128
128

==================================
         COMPILATION DETAILS
==================================

[1] Tokens:        ... (token table)
[2] AST:           ... (tree printout)
[3] Semantic:      ✅ Passed
[4] IR:            ... (raw three-address code)
[5] Optimization:  ... (6 pass results)
                   ✅ Optimization Complete
[6] Execution:     316 / 5 / 128 / 128
                   ✅ Execution Complete
[7] X86-64:        ... (NASM assembly)
                   ✅ Assembly written to 'output.asm'
[8] RISC-V:        ... (GNU AS assembly)
                   ✅ Assembly written to 'output_riscv.s'
```

Both `output.asm` and `output_riscv.s` produce identical output when
assembled and executed:
```
316
5
128
128
```
