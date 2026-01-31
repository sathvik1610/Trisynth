
# Language Specification: Trisynth

## 1. Introduction

Trisynth is a statically typed, procedural programming language designed to demonstrate the complete execution pipeline of a custom native compiler. It bridges the gap between abstract syntax and hardware execution, supporting types, control flow, functions, and arrays.

---

## 2. Data Types

Trisynth is a strictly typed language with no implicit type conversions.

### Primitive Types
| Type | Description |
| :--- | :--- |
| `int` | Signed 32-bit integer |
| `uint32` | Unsigned 32-bit integer |
| `float` | 32-bit floating-point number |
| `bool` | Boolean value (`true` or `false`) |
| `char` | 8-bit character |
| `void` | Empty type (used for function returns) |

### Composite Types
*   **Arrays**: Fixed-size arrays with homogeneous element types.
    *   Syntax: `type name[size];`
    *   Example: `int numbers[10];`

---

## 3. Variables & Scoping

*   **Declaration**: Variables must be declared before use.
*   **Initialization**: Optional initialization at declaration.
*   **Scoping**: Block-level lexical scoping.
*   **Shadowing**: Variable shadowing is allowed in nested scopes.
*   **Mutability**: All variables are mutable by default. Constants can be defined (implementation detail).

```c
int x = 10;
{
    int x = 20; // Shadows outer x
    print(x);   // Prints 20
}
print(x);       // Prints 10
```

---

## 4. Operators & Expressions

### Arithmetic
*   `+`, `-`, `*`, `/`, `%` (Modulo)
*   Pre-increment (`++i`) and Post-increment (`i++`)
*   Pre-decrement (`--i`) and Post-decrement (`i--`)

### Relational
*   `<`, `>`, `<=`, `>=`
*   `==` (Equal to), `!=` (Not equal to)
*   Result type is `bool`.

### Logical
*   `&&` (Logical AND)
*   `||` (Logical OR)
*   `!` (Logical NOT)

---

## 5. Control Flow

### Conditional Statements
*   `if (condition) { ... }`
*   `if (condition) { ... } else { ... }`

```c
if (x > 0) {
    print(x);
} else {
    print(-x);
}
```

### Iterative Statements
*   `while (condition) { ... }`
*   `for (init; condition; update) { ... }`

```c
for (int i = 0; i < 10; i++) {
    print(i);
}
```

### Control Transfer
*   `break`: Exit the current loop.
*   `continue`: Skip to the next iteration of the loop.

---

## 6. Functions

*   **Definition**: Explicit return type, name, and parameter list.
*   **Parameters**: Pass-by-value.
*   **Recursion**: Supported.
*   **Overloading**: Not supported.

```c
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

void traverse() {
    return;
}
```

---

## 7. Input / Output

Trisynth provides built-in primitives for I/O:

*   `print(expression)`: Prints the value of an expression to standard output.
*   `readInt()`: Reads an integer from standard input.

---

## 8. Comments

*   Single-line comments: `// ...`

---

## 9. Grammar Summary (EBNF Sketch)

```ebnf
program     ::= decl_list
decl_list   ::= decl_list decl | ε
decl        ::= var_decl | func_decl
var_decl    ::= type IDENTIFIER [ = expression ] ;
func_decl   ::= type IDENTIFIER ( param_list ) block
block       ::= { stmt_list }
stmt        ::= expr_stmt | if_stmt | while_stmt | for_stmt | return_stmt | break ; | continue ;
```

---

## 10. Optimization Semantics

For optimization purposes, variables that are neither printed nor returned are considered unobservable within a function. This allows the compiler to perform aggressive dead code elimination on local variables that do not contribute to the program's observable output.
