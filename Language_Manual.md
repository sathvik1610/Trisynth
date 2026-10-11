# Language Reference Manual

**Language Name:** Trisynth  
**Group ID:** 1  
**Date:** April 2026

---

## Abstract

This manual is the authoritative reference for the Trisynth programming language. It documents the complete syntax, semantics, type system, and standard built-ins of Trisynth as implemented by the accompanying compiler. Trisynth is a statically typed, imperative language with a C-family syntax. This document is intended for users who wish to write, understand, and debug Trisynth programs.

---

## 1. Introduction

Trisynth is a statically typed, compiled, imperative programming language. Its design emphasizes type safety, explicit control flow, and predictable memory layout. Every variable must be declared before use; every function must declare its return type and parameter types. The compiler rejects programs with type mismatches, undeclared identifiers, missing `return` statements, or invalid control-flow constructs before producing any executable output.

Trisynth source files use the `.nc` file extension. Programs are compiled by the `trisynth` command-line front-end, which invokes the full pipeline and produces a native executable via NASM and the system linker.

---

## 2. Installation and Setup

### 2.1 Prerequisites

| Dependency | Purpose |
|---|---|
| Python 3.9 or later | Compiler runtime |
| NASM 2.15 or later | Assembles the generated `.asm` output |
| GCC or Clang (Linux/macOS) | Links the object file against `libc` |
| WSL (Windows) | Provides a Linux environment for assembly and linking |

### 2.2 Installation

**Linux / macOS:**

```bash
git clone https://github.com/yourorg/Trisynth.git
cd Trisynth
chmod +x setup.sh
./setup.sh
```

**Windows (via WSL):**

```bat
setup.bat
```

The setup scripts install Python dependencies from `requirements.txt`, verify that NASM is accessible, and optionally install a bundled NASM binary if the system does not provide one.

### 2.3 Compiling a Program

```bash
python -m src.main my_program.nc
```

The compiler will:
1. Compile `my_program.nc` through all pipeline stages.
2. Write the generated assembly to `output.asm`.
3. Invoke NASM to assemble `output.asm` into `output.o`.
4. Link `output.o` against `libc` to produce the executable `output`.

Run the compiled program:

```bash
./output
```

---

## 3. Basic Syntax

### 3.1 Character Set and Encoding

Trisynth source files must be UTF-8 encoded. Only ASCII characters are meaningful to the language; non-ASCII characters may appear inside string literals.

### 3.2 Comments

```c
// This is a single-line comment.

/*
   This is a multi-line block comment.
   Block comments do not nest.
*/
```

Unclosed block comments are a lexical error.

### 3.3 Identifiers

Identifiers begin with a letter (`a`–`z`, `A`–`Z`) or underscore (`_`), followed by zero or more letters, digits (`0`–`9`), or underscores. Identifiers are case-sensitive. Reserved keywords may not be used as identifiers.

```
my_variable    COUNT    _temp    x1
```

### 3.4 Keywords

The following identifiers are reserved and may not be used as variable or function names:

```
int    uint32    float    bool    char    void    string    const
if     else      while    for     break   continue return
print  readInt   true     false
```

### 3.5 Statements and Blocks

Every statement is terminated by a semicolon (`;`). A block is a sequence of zero or more statements enclosed in curly braces (`{` `}`). Blocks introduce a new lexical scope.

```c
{
    int x = 10;
    print(x);
}
```

---

## 4. Data Types

Trisynth is statically and strongly typed. The type of every expression is determined at compile time. Implicit conversion between types is not permitted.

| Type | Description | Literal Form |
|---|---|---|
| `int` | 64-bit signed integer | `0`, `-42`, `1000` |
| `uint32` | Unsigned 32-bit integer | `0`, `255` |
| `bool` | Boolean value | `true`, `false` |
| `string` | Immutable character pointer to a read-only literal | `"Hello"` |

> **Note:** The types `float` and `char` are syntactically recognized but are rejected by the semantic analyzer with an `E002` error. They are reserved for future back-end support.

### 4.1 Integer Literals

Integer literals consist of one or more decimal digits. Negative literals are expressed using the unary minus operator.

```c
int x = 42;
int y = -7;
```

### 4.2 Boolean Literals

```c
bool flag = true;
bool done = false;
```

### 4.3 String Literals

String literals are enclosed in double quotation marks. Escape sequences supported by NASM backtick strings (e.g., `\n`, `\t`) may be used within the literal.

```c
string greeting = "Hello, Trisynth!";
print(greeting);
```

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

A variable must be declared before it is used. Declaration without initialization leaves the variable in an undefined state; use before assignment is not checked at compile time.

### 5.2 Assignment

```c
count = count + 1;
found = true;
```

Assignment is an expression in Trisynth and may appear in any expression context.

### 5.3 Constants

The `const` qualifier prevents any subsequent assignment to the variable after its declaration. Constants must be initialized at declaration.

```c
const int MAX = 100;
const int LIMIT = 5;
```

Any attempt to assign to, increment, or decrement a `const` variable is a compile-time semantic error.

```c
// MAX = 200;   // Error: Cannot assign to const variable `MAX`
// ++MAX;       // Error: Cannot increment/decrement const variable `MAX`
```

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
| `++` | Pre-increment | `++i` |
| `--` | Pre-decrement | `--i` |

All arithmetic operators require both operands to be of the same type.

### 6.2 Relational Operators

Relational operators always return type `bool`.

| Operator | Meaning |
|---|---|
| `==` | Equals |
| `!=` | Not equals |
| `<` | Less than |
| `>` | Greater than |
| `<=` | Less than or equal |
| `>=` | Greater than or equal |

### 6.3 Logical Operators

| Operator | Meaning | Short-circuit |
|---|---|---|
| `&&` | Logical AND | Yes — right operand not evaluated if left is false |
| `\|\|` | Logical OR | Yes — right operand not evaluated if left is true |
| `!` | Logical NOT | N/A |

Logical operators require operands of type `bool` or `int`. They always return type `bool`.

### 6.4 Operator Precedence

Operators are listed from lowest to highest precedence:

| Precedence | Operators |
|---|---|
| 1 (lowest) | Assignment `=` |
| 2 | Logical OR `\|\|` |
| 3 | Logical AND `&&` |
| 4 | Equality `== !=` |
| 5 | Relational `< > <= >=` |
| 6 | Additive `+ -` |
| 7 | Multiplicative `* / %` |
| 8 | Shift `<< >>` |
| 9 (highest) | Unary `! - ++ --` |

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

The `else` branch is optional. The condition must evaluate to type `bool` or `int`. A non-zero integer is treated as true; zero is treated as false.

```c
int x = 10;
if (x > 5) {
    print(1);
} else {
    print(0);
}
```

### 7.2 `while` Loop

```c
while (condition) {
    // body
}
```

The condition is evaluated before each iteration. If false on the first evaluation, the body is never executed.

```c
int i = 0;
while (i < 5) {
    print(i);
    ++i;
}
```

### 7.3 `for` Loop

```c
for (init ; condition ; update) {
    // body
}
```

All three header components are optional. The initializer may declare a variable scoped to the loop.

```c
for (int i = 0; i < 10; ++i) {
    print(i);
}
```

### 7.4 `break` and `continue`

```c
break;      // Exit the innermost enclosing loop immediately.
continue;   // Jump to the update expression of the innermost loop.
```

Both statements are semantic errors if used outside a loop body.

---

## 8. Functions

### 8.1 Declaration

```
return_type name ( parameter_list ) { body }
```

The parameter list is a comma-separated sequence of `type name` pairs. An empty parameter list is written as `()`.

```c
int add(int a, int b) {
    return a + b;
}

void greet() {
    print(0);
}
```

### 8.2 Return Statement

Non-`void` functions must return a value on all control-flow paths. The return type of the value must match the declared return type of the function.

```c
int square(int n) {
    return n * n;
}
```

A `void` function may use a bare `return;` or simply reach the end of its body.

### 8.3 Function Calls

```c
int result = add(3, 4);
greet();
```

### 8.4 Function Hoisting

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

---

## 9. Arrays

### 9.1 Declaration

Arrays are declared with a fixed, compile-time integer size. The size must be a positive integer literal.

```c
int arr[10];
bool flags[4];
```

### 9.2 Access and Assignment

```c
arr[0] = 42;
int val = arr[0];
```

Array indices must be of type `int`. Bounds checking is not performed at compile time or runtime in the current implementation.

### 9.3 Passing Arrays to Functions

Arrays are passed by reference. The function parameter type is written with `[]` appended to the element type.

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

### 9.4 Global Arrays

Arrays may be declared at global scope, outside any function. Global arrays are accessible from every function in the program.

```c
int memo[20];

void init_memo() {
    int i = 0;
    while (i < 20) {
        memo[i] = 0;
        ++i;
    }
}
```

---

## 10. Strings

### 10.1 Declaration and Use

String variables hold a pointer to an immutable character sequence defined in the compiled binary's data section. String literals are enclosed in double quotes.

```c
string msg = "Compilation complete.";
print(msg);
```

### 10.2 Limitations

- Strings are read-only. Element-level access and mutation are not supported.
- Only the `==` and `!=` operators may not be applied to `string` typed values at the semantic level; the compiler will reject such expressions with an `E002` error.
- String concatenation is not a built-in operation.

---

## 11. Input / Output

### 11.1 `print`

`print` is a built-in statement that outputs an integer or a string to standard output followed by a newline (for integers) or without newline (for strings).

```c
print(42);           // Outputs: 42
print("Hello!");     // Outputs: Hello!
int x = 100;
print(x);            // Outputs: 100
```

### 11.2 `readInt`

`readInt` is a built-in function that reads a single integer from standard input and returns it as type `int`.

```c
int n = readInt();
print(n);
```

`readInt` is pre-registered in the semantic symbol table and corresponds to a `scanf`-based helper function emitted in the assembly header.

---

## 12. Error Handling

The Trisynth compiler performs all error detection at compile time. There is no runtime exception mechanism. Errors are categorized as follows:

### 12.1 Lexical Errors

Arise when the source text contains a character or token pattern not recognized by the lexer.

| Error | Example | Message |
|---|---|---|
| Unexpected character | `int x = $5;` | `Lexical Error: Unexpected character '$' at 1:9` |
| Unclosed block comment | `/* unterminated` | `Lexical Error: Unclosed block comment starting at 1:1` |

### 12.2 Syntax Errors

Arise when the token stream does not conform to the grammar. The parser reports the offending token and its position.

```
Syntax Error: Expected ';' after statement at line 5, column 12.
```

### 12.3 Semantic Errors

Arise from type violations, undeclared identifiers, or structural rule violations detected during semantic analysis.

| Error Code | Description | Example |
|---|---|---|
| `E002` | Type mismatch or unsupported type | Assigning `bool` to `int` variable |
| `E002` | Unsupported type in declaration | `float x = 3.14;` |
| `E003` | `return` outside a function | Bare `return` at global scope |
| `E004` | Missing `main` entry point | No `void main()` or `int main()` defined |
| — | Undeclared variable | Using `y` before `int y;` |
| — | Assignment to `const` | `LIMIT = 20;` where `LIMIT` is `const` |
| — | Break/continue outside loop | `break;` at function scope |
| — | Function argument count mismatch | `add(1)` when `add` expects 2 arguments |
| — | Return type mismatch | Returning `bool` from an `int` function |

---

## 13. Example Programs

### 13.1 Hello World

```c
void main() {
    string msg = "Hello, World!";
    print(msg);
}
```

**Output:**

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
        print(1);  // 1 — x is even
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

### 13.6 Memoized Fibonacci with Global Array

```c
int memo[20];
const int N = 10;

void init_memo() {
    int i = 0;
    while (i < 20) {
        memo[i] = 0;
        ++i;
    }
}

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
    print(res);  // 55
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

---

### 13.8 Constant Folding (Compiler Optimization)

The following program exercises the constant folding pass. The expression `(10 * 10 + 44) / 12` is fully evaluated at compile time and replaced with the constant `12` in the IR.

```c
void main() {
    int x = (10 * 10 + 44) / 12;
    print(x);  // 12
}
```

---

## 14. Limitations

The following limitations apply to the current release of Trisynth:

| Limitation | Description |
|---|---|
| No `float` or `char` support | Both types are lexed and parsed but rejected by the semantic analyzer with `E002`. |
| No string operations | String comparison, concatenation, and indexing are not supported. |
| No runtime bounds checking | Array out-of-bounds access results in undefined behavior at runtime. |
| No multi-file compilation | The compiler accepts a single source file per invocation; there is no `#include` or module system. |
| No pointer types | There are no raw pointer declarations; array references are passed implicitly. |
| No nested functions | All functions must be declared at the top (global) level. |
| Single return value | Functions may return only one value; tuples and multiple return values are not supported. |
| No error recovery in parser | The parser halts on the first syntax error; subsequent errors in the program are not reported in the same run. |
| Post-increment not supported | Only pre-increment (`++i`) and pre-decrement (`--i`) are supported; postfix forms (`i++`) produce a syntax error. |
