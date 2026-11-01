# Language Reference Manual

**Language Name:** Trisynth  
**Group ID:** 1  
**Date:** April 2026

---

## Abstract

This manual is the reference for the Trisynth programming language. It documents the syntax, semantics, type system, and built-ins of Trisynth as implemented by the accompanying compiler, including the places where the implementation is stricter, looser, or more surprising than a C programmer would expect. Trisynth is a statically typed, imperative language with a C-family syntax. This document is intended for users who wish to write, understand, and debug Trisynth programs.

---

## 1. Introduction

Trisynth is a statically typed, compiled, imperative programming language. Every variable must be declared before use; every function must declare its return type and parameter types. The compiler rejects programs with type mismatches, undeclared identifiers, missing `return` statements, or `break`/`continue` outside a loop before producing any executable output.

Trisynth source files use the `.tri` file extension. The compiler (`src/main.py`) runs the full pipeline (lexer, parser, semantic analysis, IR generation, optimization, code generation), assembles the result with NASM, links it with `gcc`, and runs the resulting program.

---

## 2. Installation and Setup

### 2.1 Prerequisites

| Dependency | Purpose |
|---|---|
| Python 3 | Compiler runtime (the compiler has no third-party dependencies) |
| NASM | Assembles the generated `.asm` output |
| GCC | Links the object file against `libc` (Clang is not invoked) |
| WSL (Windows) | Provides a Linux environment with `nasm` and `gcc`; alternatively native `nasm` and `gcc` on `PATH` |

`requirements.txt` lists only `pytest`, which is needed only to run the test suite.

### 2.2 Installation

**Linux / macOS / WSL:**

```bash
git clone https://github.com/yourorg/Trisynth.git
cd Trisynth
bash setup.sh
```

`setup.sh` checks for `gcc` and `nasm`; if NASM is missing it builds a portable copy into `bin/linux/nasm`.

**Windows:**

```bat
setup.bat
```

`setup.bat` checks for `gcc` and `nasm` on `PATH` and, if NASM is missing, downloads a portable copy into `bin\windows`. The source-run compiler does not use that copy: on Windows it prefers WSL (it needs `wsl nasm --version` to succeed) and otherwise needs `nasm` and `gcc` on `PATH`. Neither script installs Python packages.

Pre-built packages of the compiler (`trisynth`, `trisynth.exe`, built from `src/main.py`) take the same arguments as `python src/main.py`.

### 2.3 Compiling a Program

From the repository root:

```bash
python src/main.py my_program.tri
```

(`python -m src.main my_program.tri` also works when the repository root is the current directory or on `PYTHONPATH`.)

The compiler will:
1. Lex, parse, analyze, generate IR for, and optimize `my_program.tri`.
2. Write the generated assembly to `output.asm` (x86-64) and `output_riscv.s` (RISC-V) in the **current directory**.
3. Invoke NASM to assemble `output.asm` into `output.o`.
4. Link `output.o` with `gcc` (`-no-pie`) to produce the executable `program` (`program.exe` on native Windows).
5. Run the executable itself and print its captured standard output.

Because the compiler already runs the program, you normally do not run it yourself. To run it again (for example to feed standard input), use `./program` (under WSL: `wsl ./program`). Source files whose name does not end in `.tri` are rejected.

### 2.4 Command-line interface

```
python src/main.py [file.tri] [options]
```

| Flag | Meaning |
|---|---|
| `file` | Source file (must end in `.tri`). If omitted, or with `--demo`, source code is read from standard input. |
| `--demo` | Interactive mode: read the program from standard input until end-of-file. |
| `--arch {x86,riscv,both}` | Target architecture to build and run (default `x86`). RISC-V execution needs `riscv64-linux-gnu-gcc` and `qemu-riscv64` under Linux/WSL. |
| `--tokens` | Print the token list and stop. |
| `--ast` | Print the abstract syntax tree and stop. |
| `--ir` | Print the IR before and after each optimization pass and stop. |
| `--asm` | Print the generated assembly (for the selected `--arch`) and stop. |
| `-v`, `--verbose` | Print all compilation stages and the program output. |
| `--compare-asm` | Print x86-64 and RISC-V assembly and stop. |
| `--benchmark` | Build and run x86-64 and RISC-V (under QEMU) and compare run times. |

Notes:

- `output.asm` and `output_riscv.s` (and `output.o`, `program`) are written to the current directory, so run the compiler from a scratch directory, not from a directory whose files you care about.
- Compile-time errors are printed on standard output and **the exit status is always 0** (except for a wrong file extension, which exits with 1). Lexer and parser errors are printed as `Error: <message>`; semantic, IR-generation and assembler/linker errors are printed as `   Failed: <message>` (three leading spaces). A missing source file prints `Error: File 'x.tri' not found.`
- The program's standard error and exit status are discarded; if the program crashes (for example division by zero) the compiler prints nothing for it.
- Under Windows + WSL the compiler's own `wsl nasm` and `wsl gcc` calls consume piped standard input, so when the compiler runs the program itself `readInt` may receive no input (it returned 0 in testing). To supply input, compile first and then run `wsl ./program` (or `./program`) directly with the input piped to it.

---

## 3. Basic Syntax

### 3.1 Character Set and Encoding

Only ASCII characters are meaningful to the language. Non-ASCII characters may appear inside string literals and comments, but not in identifiers (a lexical error). The compiler reads the source file using the platform's default text encoding (UTF-8 on Linux, commonly cp1252 on Windows), so on such systems some UTF-8 byte sequences cause a decoding error (`Error: 'charmap' codec can't decode byte ...`). Keep source files ASCII-only where possible.

### 3.2 Comments

```c
// This is a single-line comment.

/*
   This is a multi-line block comment.
   Block comments do not nest.
*/
```

Unclosed block comments are a lexical error. Because comments do not nest, `/* a /* b */ c */` ends at the first `*/` and leaves `c */` to be parsed as code.

### 3.3 Identifiers

Identifiers begin with a letter (`a`-`z`, `A`-`Z`) or underscore (`_`), followed by zero or more letters, digits (`0`-`9`), or underscores. Identifiers are case-sensitive. Reserved keywords may not be used as identifiers.

```
my_variable    COUNT    _temp    x1
```

### 3.4 Keywords

The following identifiers are reserved and may not be used as variable or function names:

```
int    bool    char    void    string    const
if     else    while   for     break     continue    return
print  readInt true    false
```

`char` is reserved but unusable (see section 4). `float` and `uint32` are not keywords; they are ordinary identifiers.

### 3.5 Statements and Blocks

Simple statements (declarations, expression statements, `print`, `return`, `break`, `continue`) are terminated by a semicolon (`;`). A block is a sequence of zero or more statements enclosed in curly braces (`{` `}`). Blocks introduce a new lexical scope. The empty statement `;` is not allowed (it is a syntax error); use `{}` instead.

A Trisynth file consists only of function definitions. Statements and variable declarations cannot appear outside a function (see section 9.4). **All code snippets in this manual that show statements or local declarations must be placed inside a function body** such as `void main() { ... }` to compile.

```c
void main() {
    {
        int x = 10;
        print(x);
    }
}
```

---

## 4. Data Types

Trisynth is statically and strongly typed. The type of every expression is determined at compile time. There are no implicit conversions between types, with one exception: `if` and `while` conditions and the operands of `&&` and `||` accept `int` as well as `bool`.

| Type | Description | Literal Form |
|---|---|---|
| `int` | 64-bit signed integer | `0`, `42`, `1000` (negative values are written with unary `-`) |
| `bool` | Boolean value | `true`, `false` |
| `string` | Pointer to a read-only string literal | `"Hello"` |

> **Note:** `char` is a reserved word but not a usable type. A character literal such as `'a'` is a syntax error (`char c = 'a';` gives `Error: Expected expression at 1:23, found TokenType.CHAR`), and `char c;` is rejected with `E002`. `char` arrays, parameters and return types are not diagnosed and have no defined behavior. `float` and `uint32` are not part of the language: they are ordinary identifiers, and floating-point literals such as `3.14` are a lexical error. `void` is accepted only as a function return type in practice; `void x;` and `void` parameters are not diagnosed and should not be used.

### 4.1 Integer Literals

Integer literals consist of one or more decimal digits. Negative values are expressed using the unary minus operator.

```c
int x = 42;
int y = -7;
```

A literal larger than 2^63-1 is **not** a compile-time error: it silently wraps modulo 2^64 (`9223372036854775808` becomes `-9223372036854775808`; NASM may print a "does not fit in 64 bits" warning). `-9223372036854775808` is accepted.

### 4.2 Boolean Literals

```c
bool flag = true;
bool done = false;
```

`bool` values are stored as integers (`true` is 1, `false` is 0).

### 4.3 String Literals

String literals are enclosed in double quotation marks. The literal text is passed to NASM as a backtick string, so NASM escapes work: `\n`, `\t`, `\r`, `\a`, `\"`, `\\`, `\xNN` and octal escapes; an unknown escape `\c` yields `c`. `%` has no special meaning.

```c
string greeting = "Hello, Trisynth!";
print(greeting);
```

A string literal must not contain a backtick or a raw newline, and must not end with an escaped backslash (`"a\\"`): these currently break the assembler step or produce garbage output.

---

## 5. Variables

### 5.1 Declaration

Variable declarations follow the form:

```
type name ;
type name = expression ;
```

```c
int count;
int limit = 100;
bool found = false;
string label = "result";
```

A variable must be declared before it is used. Declaration without initialization leaves the variable with an indeterminate value (whatever was on the stack); use before assignment is not checked at compile time. Only one variable may be declared per declaration (`int a = 1, b = 2;` is a syntax error). In `int x = x;` the `x` on the right is not yet declared.

### 5.2 Assignment

```c
count = count + 1;
found = true;
```

Assignment is an expression in Trisynth and may appear in any expression context (`a = b = 3;`, `print(x = 4);`, `if (x = 5)`). The target must be a variable or an array element, and assignment is right-associative.

### 5.3 Constants

The `const` qualifier prevents any subsequent assignment to the variable after its declaration. Constants must be initialized at declaration (otherwise `Error: Const variable must be initialized.`); the initializer need not be a compile-time constant. Parameters and functions cannot be `const`, and a `for` initializer cannot declare a `const`.

```c
void main() {
    const int MAX = 100;
    const int LIMIT = 5;
    print(MAX + LIMIT);   // 105
}
```

Assignment, `++` and `--` of a `const` variable are all reported with the same message (`++x` is rewritten to `x = x + 1`):

```c
// MAX = 200;   // Semantic Error: Cannot assign to const variable 'MAX'.
// ++MAX;       // Semantic Error: Cannot assign to const variable 'MAX'.
```

`const` also applies to array declarations. Direct assignment to an element of a `const` array is rejected:

```c
const int table[4];
// table[0] = 1;   // E002 Semantic Error: Cannot mutate elements of const array 'table'.
```

A `const` array cannot be initialized and its contents are indeterminate, so it is of little use. Known gaps: `++table[0]`, `--table[0]`, and passing the array to an `int a[]` parameter and writing through it are **not** rejected.

### 5.4 Scoping and Shadowing

- Each block, each function body, and each `for` statement opens a new scope. Names declared in an inner scope may shadow outer names; redeclaring a name in the *same* scope is an error (`Semantic Error: Symbol 'x' already declared in this scope.`).
- Function parameters live in an enclosing scope of the function body, so a local declared in the function's outermost block may shadow a parameter.
- A variable declared in a `for` initializer is visible only inside the loop; the loop body may redeclare the same name.
- A variable is visible only after its declaration (`int x = x;` is an error unless an outer `x` exists).
- A local variable with the same name as a function hides it: calling it gives `'f' is not a function.`

---

## 6. Operators

### 6.1 Arithmetic Operators

| Operator | Operation | Example |
|---|---|---|
| `+` | Addition | `a + b` |
| `-` | Subtraction or unary negation | `a - b`, `-a` |
| `*` | Multiplication | `a * b` |
| `/` | Integer division | `a / b` |
| `%` | Modulo (remainder) | `a % b` |
| `<<` | Left bit-shift | `a << 2` |
| `>>` | Right arithmetic bit-shift | `a >> 1` |
| `++` | Pre-increment (prefix only) | `++i` |
| `--` | Pre-decrement (prefix only) | `--i` |

Both operands of a binary operator must have the same type, and the result has that type. (`bool` operands are not rejected: `true + true` is a `bool` holding 2.) `++` and `--` exist only as prefix operators, take a variable or an array element of type `int`, and evaluate to the *updated* value (`int y = ++x;` stores the new `x`). `++x` is rewritten to `x = x + 1`. `a--b` and `5--3` are syntax errors because `--` is lexed as one token. Operands are evaluated left to right (`++x + ++x` with `x == 1` yields 6).

`int` is a signed 64-bit two's-complement integer. `+`, `-`, `*` and `<<` wrap around on overflow, `/` and `%` truncate toward zero (so `-7 / 2` is `-3` and `-7 % 3` is `-1`), and `>>` is an arithmetic shift. Shift counts are taken modulo 64 (`1 << 64` is 1, `1 << -1` is `-9223372036854775808`). The optimizer preserves these semantics: constant folding emulates them (it does not fold shifts whose count is outside 0..63), and division by a power of two is reduced to a shift only together with a correction for negative dividends. Division by zero (and `INT64_MIN / -1`) is never folded; on x86-64 it kills the program with SIGFPE and no message (output not yet flushed is lost). On RISC-V the `div`/`rem` instructions do not trap.

### 6.2 Relational Operators

Relational operators always return type `bool`. Both operands must have the same type.

| Operator | Meaning |
|---|---|
| `==` | Equals |
| `!=` | Not equals |
| `<` | Less than |
| `>` | Greater than |
| `<=` | Less than or equal |
| `>=` | Greater than or equal |

`==` and `!=` are also accepted on `string` operands but compare addresses, not contents (identical literals share one copy, so `"x" == "x"` is true). `<`, `>`, `<=`, `>=` on strings are rejected. Comparisons cannot be chained (`1 < 2 < 3` compares a `bool` with an `int` and is a type error).

### 6.3 Logical Operators

| Operator | Meaning | Short-circuit |
|---|---|---|
| `&&` | Logical AND | Yes: right operand not evaluated if left is false |
| `\|\|` | Logical OR | Yes: right operand not evaluated if left is true |
| `!` | Logical NOT | N/A |

`&&` and `||` require operands of type `bool` or `int` and always return `bool` (1 or 0). `!x` is 1 if `x` is zero and 0 otherwise, but `!` (like unary `-`) performs no operand type check and yields the *type of its operand*: `!5` has type `int`, so `bool b = !a;` with an `int a` is a type error while `int b = !a;` is accepted.

### 6.4 Operator Precedence

Operators are listed from lowest to highest precedence. All binary operators are left-associative; assignment is right-associative.

| Precedence | Operators |
|---|---|
| 1 (lowest) | Assignment `=` |
| 2 | Logical OR `\|\|` |
| 3 | Logical AND `&&` |
| 4 | Equality `== !=` |
| 5 | Relational `< > <= >=` |
| 6 | Shift `<< >>` |
| 7 | Additive `+ -` |
| 8 | Multiplicative `* / %` |
| 9 | Prefix unary `! - ++ --` |
| 10 (highest) | Call `f(...)`, index `a[i]`, parentheses |

Note that shift binds **more loosely** than `+` and `-` (`1 << 2 + 1` is `1 << 3`, i.e. 8). Use parentheses when mixing them.

---

## 7. Control Flow

### 7.1 `if` / `else`

```c
if (condition) {
    // then branch
} else {
    // else branch
}
```

The `else` branch is optional. The condition must evaluate to type `bool` or `int`. A non-zero integer is treated as true; zero is treated as false. The branches may be any single statement, with or without braces; an `else` binds to the nearest `if`.

```c
void main() {
    int x = 10;
    if (x > 5) {
        print(1);
    } else {
        print(0);
    }
}
```

### 7.2 `while` Loop

```c
while (condition) {
    // body
}
```

The condition (type `bool` or `int`) is evaluated before each iteration. If false on the first evaluation, the body is never executed. The body may be a single statement without braces.

```c
void main() {
    int i = 0;
    while (i < 5) {
        print(i);
        ++i;
    }
}
```

### 7.3 `for` Loop

```c
for (init ; condition ; update) {
    // body
}
```

All three header components are optional (`for (;;)` loops forever until `break`). The initializer may declare a variable (scoped to the loop; it cannot be `const`) or be an expression. Unlike `if` and `while`, the `for` condition must be of type `bool`: `for (int i = 3; i; --i)` is rejected with `Type Error: For condition must be bool, got 'int'.`

```c
void main() {
    for (int i = 0; i < 10; ++i) {
        print(i);
    }
}
```

### 7.4 `break` and `continue`

```c
break;      // Exit the innermost enclosing loop immediately.
continue;   // Jump to the update expression of the innermost for loop,
            // or to the condition of the innermost while loop.
```

Both statements are semantic errors if used outside a loop body (`Semantic Error: 'break' outside of loop.`).

---

## 8. Functions

### 8.1 Declaration

```
return_type name ( parameter_list ) { body }
```

The parameter list is a comma-separated sequence of `type name` pairs; an array parameter is written `type name[]` (no size). An empty parameter list is written as `()`. Functions can only be defined at the top level; a function defined inside another function is a syntax error (`Function 'g' cannot be declared inside another function or block.`).

```c
int add(int a, int b) {
    return a + b;
}

void greet() {
    print(0);
}
```

### 8.2 Return Statement

The return type of the value must match the declared return type of the function (`E002 Type Error: Function 'f' expects return type 'int', but returned 'bool'.`). A `void` function must not return a value (`return 1;` is an `E002` error).

A non-`void` function is checked **syntactically** for a missing return: it is accepted only if its body contains a `return` as a direct statement, or an `if`/`else` in which both branches return. A `return` inside a `while` or `for` does not count, so `int f() { while (true) { return 1; } }` and `int f(int x) { if (x > 0) { return 1; } }` are rejected with `Missing return statement in non-void function 'f'`.

```c
int square(int n) {
    return n * n;
}
```

A `void` function may use a bare `return;` or simply reach the end of its body.

### 8.3 Function Calls

```c
int add(int a, int b) {
    return a + b;
}

void greet() {
    print("hello
");
}

void main() {
    int result = add(3, 4);
    greet();
    print(result);   // 7
}
```

The argument count and each argument type must match the declaration. Arguments are evaluated left to right and passed by value (arrays by reference, see 9.3).

### 8.4 Functions Before Their Definition

Functions may be called before their textual declaration point. The compiler performs a two-pass analysis: all function signatures are registered in the first pass, and function bodies are validated in the second pass.

```c
void main() {
    int r = compute(5, 10); // `compute` is defined below
    print(r);               // 15
}

int compute(int a, int b) {
    return a + b;
}
```

### 8.5 Recursion

Recursive and mutually recursive functions are fully supported.

```c
int fib(int n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
}
```

### 8.6 The `main` Function

The semantic analyzer only checks that a function named `main` exists (error `E004 Semantic Error: Program is missing required entry point 'main' function.`). It may have any return type and any parameters (parameters receive indeterminate values), and its return value is ignored.

---

## 9. Arrays

### 9.1 Declaration

Arrays are declared with a fixed size that must be a positive integer literal. Negative numbers, `const` names and expressions are not accepted (`Syntax Error ...: Expected array size.`), and size 0 gives `Array size must be a positive integer`. Arrays cannot have an initializer.

```c
void main() {
    int arr[10];
    bool flags[4];
    string names[2];
}
```

### 9.2 Access and Assignment

```c
void main() {
    int arr[10];
    arr[0] = 42;
    int val = arr[0];
}
```

Array indices must be of type `int`. Array elements are not initialized: they hold indeterminate values, including when the declaration is re-executed in a loop. Bounds checking is not performed at compile time or runtime (`a[5]` on a 2-element array silently reads/writes adjacent memory). `++a[i]` and `--a[i]` are allowed.

Whole-array assignment (`a = b;`) and array comparison (`a == b`) are accepted by the compiler but are not meaningful: after `a = b;` the two names end up referring to the same storage (an optimizer effect). Do not use them. Using an array name in `print` prints an address.

### 9.3 Passing Arrays to Functions

Arrays are passed by reference. The parameter is written with `[]` after the parameter name, without a size.

```c
void init(int data[], int size) {
    int i = 0;
    while (i < size) {
        data[i] = 0;
        ++i;
    }
}

void main() {
    int arr[5];
    init(arr, 5);
}
```

The array argument must be a plain variable name. Writes through the parameter modify the caller's array (including a `const` array). Functions cannot return arrays.

### 9.4 No Global Variables

Variables and arrays (including `const` ones) cannot be declared at global scope. A file may contain only function definitions; any global declaration is rejected with `E002 Semantic Error: Global variable 'x' is not supported; declare it inside a function.` Declare state inside a function and pass arrays to the functions that need them:

```c
void init_memo(int memo[], int size) {
    int i = 0;
    while (i < size) {
        memo[i] = 0;
        ++i;
    }
}

void main() {
    int memo[20];
    init_memo(memo, 20);
    print(memo[19]);   // 0
}
```

---

## 10. Strings

### 10.1 Declaration and Use

String variables hold a pointer to a read-only character sequence stored in the compiled program's data section. A string variable can be reassigned to another literal, but the characters cannot be changed.

```c
void main() {
    string msg = "Compilation complete.";
    print(msg);
}
```

### 10.2 Limitations

- Strings are read-only. Indexing (`s[0]`) is not supported (`Type Error: 's' is not an array.`).
- `==` and `!=` may be applied to two strings but compare addresses, not contents. Every other operator on strings (`+`, `<`, ...) is rejected with `E002 Semantic Error: Operator 'PLUS' is not structurally supported on string pointers.`
- String concatenation is not a built-in operation.
- Strings can be passed to functions, returned from functions, stored in `string` arrays, and printed.
- See 4.3 for characters that must not appear in a literal.

---

## 11. Input / Output

### 11.1 `print`

`print(expr);` is a built-in statement taking exactly one expression. A value of type `string` is written as-is **without** a newline; every other value (`int`, `bool` as 1 or 0, comparison results, ...) is written in decimal followed by a newline. `print()` and `print(a, b)` are syntax errors.

```c
void main() {
    print(42);           // Outputs: 42 (and a newline)
    print("Hello!");     // Outputs: Hello! (no newline)
    int x = 100;
    print(x);            // Outputs: 100 (and a newline)
    print(true);         // Outputs: 1
}
```

Printing a `void` call or an array name is accepted but prints garbage. Add `\n` to string literals if you want line breaks (`print("done\n");`).

### 11.2 `readInt`

`readInt()` is a built-in function that reads one whitespace-delimited integer from standard input (using `scanf("%ld")`) and returns it as type `int`. It takes no arguments.

```c
void main() {
    int n = readInt();
    print(n);
}
```

Input that is not an integer, or end of input, is not reported: `readInt` returns an indeterminate value (typically stale stack contents). Out-of-range values saturate to the 64-bit limits. `readInt` is pre-registered in the semantic symbol table and corresponds to a `scanf`-based helper emitted in the assembly header. See 2.4 for supplying standard input under Windows + WSL.

---

## 12. Error Handling

Type, scope and structural errors are detected at compile time, and a program with such an error produces no executable. There is no runtime exception mechanism: arithmetic faults (division by zero, `INT64_MIN / -1`) crash the program silently, and out-of-bounds array accesses are undefined. The compiler stops at the **first** error of any kind (lexical, then syntax, then semantic) and prints one diagnostic per run.

### 12.1 Lexical Errors

Arise when the source text contains a character or token pattern not recognized by the lexer. Printed with the prefix `Error: `.

| Error | Example | Message |
|---|---|---|
| Unexpected character | `int x = $5;` | `Error: Lexical Error: Unexpected character '$' at 1:9` |
| Unclosed block comment | `/* unterminated` | `Error: Lexical Error: Unclosed block comment starting at 1:1` |
| Unterminated string | `print("abc);` | `Error: Lexical Error: Unexpected character '"' at LINE:COL` |

Characters such as `& | ^ ~ ? # .` (a lone `&` or `|`, floating-point `3.14`, and so on) are also lexical errors.

### 12.2 Syntax Errors

Arise when the token stream does not conform to the grammar. Printed with the prefix `Error: `; most messages name the line and column:

```
Error: Syntax Error at 1:24: Expected ';' after expression.
Error: Expected type declaration at 1:1
Error: Expected expression at 1:14, found TokenType.SEMICOLON
```

A few messages carry no position (`Invalid assignment target.`, `Const variable must be initialized.`, `Functions cannot be const.`, `Increment/Decrement requires a variable.`).

### 12.3 Semantic Errors

Arise from type violations, undeclared identifiers, or structural rule violations detected during semantic analysis. Printed with the prefix `   Failed: ` (three spaces).

| Code | Condition | Message |
|---|---|---|
| `E002` | `if` condition not `bool`/`int` | `E002 Type Error: If condition must evaluate to bool or int, got 'string'.` |
| `E002` | Return type mismatch | `E002 Type Error: Function 'f' expects return type 'int', but returned 'bool'.` (also `... is void and cannot return a value.`, `... but returned nothing.`) |
| `E002` | `char` variable | `E002 Semantic Error: Unsupported intrinsic type 'char' for variable 'c'.` |
| `E002` | Operator other than `==`/`!=` on strings | `E002 Semantic Error: Operator 'PLUS' is not structurally supported on string pointers.` |
| `E002` | Assigning to an element of a `const` array | `E002 Semantic Error: Cannot mutate elements of const array 'table'.` |
| `E002` | Global variable | `E002 Semantic Error: Global variable 'x' is not supported; declare it inside a function.` |
| `E004` | No function named `main` | `E004 Semantic Error: Program is missing required entry point 'main' function.` |
| none | Type mismatch in initializer/assignment | `Type Error: Cannot assign 'bool' to 'int' for variable 'x'.` |
| none | Mismatched operand types | `Type Error: Type mismatch in binary operation 'PLUS'. Got 'int' and 'bool'.` |
| none | Undeclared variable/array | `Semantic Error: Undeclared variable 'y'.` |
| none | Assignment, `++` or `--` of a `const` variable | `Semantic Error: Cannot assign to const variable 'MAX'.` |
| none | `break`/`continue` outside a loop | `Semantic Error: 'break' outside of loop.` |
| none | Wrong argument count | `Type Error: Function 'add' expects 2 arguments, got 1.` |
| none | Wrong argument type | `Type Error: Argument 2 of 'add' expects 'int', got 'bool'.` |
| none | Call to an unknown function / a non-function | `Semantic Error: User-defined function 'g' not found ...` / `Semantic Error: 'x' is not a function.` |
| none | Duplicate name in one scope | `Semantic Error: Symbol 'x' already declared in this scope.` |
| none | Missing `return` | `Missing return statement in non-void function 'f'` |
| none | `while` condition not `bool`/`int` | `Type Error: While condition must be bool or int, got 'string'.` |
| none | `for` condition not `bool` | `Type Error: For condition must be bool, got 'int'.` |
| none | Non-`int` array index / indexing a non-array | `Type Error: Array index must be int, got 'bool'.` / `Type Error: 'a' is not an array.` |

There is no `E003`: a `return` outside a function cannot occur because only function definitions are accepted at the top level (a top-level `return;` is the syntax error `Error: Expected type declaration at 1:1`).

---

## 13. Example Programs

### 13.1 Hello World

```c
void main() {
    string msg = "Hello, World!";
    print(msg);
}
```

**Output** (no trailing newline, since strings are printed without one):

```
Hello, World!
```

---

### 13.2 Arithmetic and Variables

```c
void main() {
    int a = 15;
    int b = 4;
    int sum  = a + b;
    int diff = a - b;
    int prod = a * b;
    int quot = a / b;
    int rem  = a % b;
    print(sum);   // 19
    print(diff);  // 11
    print(prod);  // 60
    print(quot);  // 3
    print(rem);   // 3
}
```

---

### 13.3 Conditional Logic

```c
bool is_even(int n) {
    if (n % 2 == 0) {
        return true;
    }
    return false;
}

void main() {
    int x = 12;
    if (is_even(x)) {
        print(1);  // 1 - x is even
    } else {
        print(0);
    }
}
```

---

### 13.4 Loops and Arrays

```c
void main() {
    int arr[5];
    for (int i = 0; i < 5; ++i) {
        arr[i] = i * i;
    }

    int j = 0;
    while (j < 5) {
        print(arr[j]);  // 0, 1, 4, 9, 16
        ++j;
    }
}
```

---

### 13.5 Recursive Fibonacci

```c
int fib(int n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
}

void main() {
    print(fib(10));  // 55
}
```

---

### 13.6 Memoized Fibonacci with an Array Parameter

Because there are no global variables, the memo table lives in `main` and is passed by reference.

```c
int fib(int n, int memo[]) {
    if (n <= 1) return n;
    if (memo[n] != 0) return memo[n];
    int res = fib(n - 1, memo) + fib(n - 2, memo);
    memo[n] = res;
    return res;
}

void main() {
    const int N = 10;
    int memo[20];
    for (int i = 0; i < 20; ++i) {
        memo[i] = 0;
    }
    print(fib(N, memo));  // 55
}
```

---

### 13.7 User Input

```c
void main() {
    int n = readInt();
    if (n > 0) {
        print(1);    // Positive
    } else {
        print(-1);   // Non-positive
    }
}
```

Run `./program` (or `wsl ./program`) directly to supply input, for example `echo 5 | ./program` prints `1`.

---

### 13.8 Constant Folding (Compiler Optimization)

The following program exercises the constant folding pass. The expression `(10 * 10 + 44) / 12` is fully evaluated at compile time and replaced with the constant `12` in the IR (inspect with `--ir`).

```c
void main() {
    int x = (10 * 10 + 44) / 12;
    print(x);  // 12
}
```

---

### 13.9 Precedence and Integer Semantics

```c
void main() {
    int a = 3;
    print(a << 1 + 1);    // 12  (shift binds looser than +: 3 << 2)
    print((a << 1) + 1);  // 7
    print(-7 / 2);        // -3  (division truncates toward zero)
    print(-7 % 3);        // -1
    int x = 1;
    int y = ++x;          // prefix ++ yields the new value
    print(y);             // 2
}
```

---

## 14. Design Choices and Known Limitations

This section lists what the language deliberately or currently does not support, and implementation behaviors a programmer must know. Each row was checked against the compiler.

| Topic | Behavior |
|---|---|
| Postfix `++`/`--` | Not supported (`i++;` is `Syntax Error ... Expected ';' after expression.`). Prefix `++x` is rewritten by the parser to `x = x + 1`, whose value is the new value; a postfix form would need the old value kept in a temporary. |
| Compound assignment | `+=`, `-=`, ... are not supported (`Expected expression ... found TokenType.ASSIGN`); write `x = x + 1`. |
| Bitwise operators | `&`, `\|`, `^`, `~` do not exist (lexical error). Only `<<` and `>>` and logical `&&`, `\|\|`, `!` are provided. |
| Ternary and other operators | No `?:`, no unary `+`, no comma operator, no multiple declarators (`int a, b;`). |
| `float`, `uint32` | Not part of the language (ordinary identifiers; `3.14` is a lexical error). |
| `char` | Reserved word, unusable: char literals are syntax errors; `char c;` is `E002`; `char` arrays/parameters are undiagnosed and undefined. |
| Global variables | Not supported. The backends emit no global storage, so every global declaration (scalar, array, `const`) is rejected with `E002`. Pass arrays as parameters instead. |
| Nested functions | Not supported (syntax error). All functions are top-level. |
| Function order | A function may be used before its definition; recursion and mutual recursion work. |
| Conditions | `if` and `while` accept `bool` or `int` (non-zero is true); `for` requires `bool`. |
| Short-circuit | `&&` and `\|\|` short-circuit and yield `bool`. `!` yields the type of its operand. |
| Strings | Read-only literals; no indexing, concatenation or content comparison. `==`/`!=` compare pointers (identical literals compare equal). `print` of a string adds no newline. |
| Arrays | Literal positive size, no initializer, elements uninitialized, no bounds checking, passed by reference (`int a[]`), cannot be returned; whole-array assignment/comparison is accepted but meaningless; `const` arrays can be mutated via `++`/`--` or a parameter. |
| Integers | 64-bit two's complement; `+ - * <<` wrap; `/` and `%` truncate toward zero; `>>` is arithmetic; shift counts are taken mod 64. The optimizer preserves all of this. Division by zero and `INT64_MIN / -1` crash the program on x86-64. |
| Literals | A literal above 2^63-1 silently wraps modulo 2^64 (no compile-time error). |
| Uninitialized values | Declared-but-unassigned scalars, array elements, and `main` parameters hold indeterminate values; the same applies to a failed `readInt`. |
| Error reporting | The compiler stops at the first error (lexical, syntax or semantic); there is no error recovery. |
| Return checking | Syntactic: a direct `return`, or `if`/`else` with returns in both branches; returns inside loops do not count. |
| `main` | Any function named `main` satisfies the entry-point check (any return type or parameters); its return value is ignored. |
| Scoping | Blocks, function bodies and `for` statements open scopes; shadowing is allowed; a local in a function's outermost block may shadow a parameter; same-scope redeclaration is an error. |
| String escapes | NASM backtick escapes are used. A literal that ends in `\\`, contains a backtick, or contains a raw newline breaks assembly or output. `%` is safe. |
| Source encoding | The source file is read with the platform default encoding; on Windows (cp1252) some UTF-8 bytes cause a decoding error. Non-ASCII identifiers are not allowed. |
| `readInt` | Uses `scanf("%ld")`; invalid input or end of input is silent and gives an indeterminate value; takes no arguments. |
| Running with input | When the compiler runs the program itself under Windows + WSL, piped stdin is not reliably forwarded (`readInt` returned 0). Run the assembled `./program` (or `wsl ./program`) directly to supply input. |
| Compiler output | Diagnostics are printed as `Error: ...` or `   Failed: ...`; the exit status is always 0 (1 only for a wrong file extension); program stderr/exit status are discarded; `output.asm`, `output_riscv.s`, `output.o` and `program` are written to the current directory. |
| Dangling `else` / bodies | Loop and `if` bodies may be single statements; `else` binds to the nearest `if`; the empty statement `;` is a syntax error. |
| No multi-file compilation | One source file per invocation; no `#include` or module system. |
| No pointer types | There are no pointer declarations; arrays are passed by reference implicitly. |
| Single return value | Functions return at most one value. |
| Runtime errors | There is no runtime exception mechanism; faults are silent crashes. |
