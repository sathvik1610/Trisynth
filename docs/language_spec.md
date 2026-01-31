# NanoC Language Specification

**NanoC** is a strictly typed, procedural language designed for compiler education. It mimics C syntax but simplifies semantic complexity while maintaining robustness.

## 1. Lexical Structure

*   **Keywords**: `int`, `uint32`, `float`, `bool`, `char`, `void`, `const`, `if`, `else`, `while`, `for`, `break`, `continue`, `return`, `true`, `false`, `print`, `readInt`.
*   **Identifiers**: `[a-zA-Z_][a-zA-Z0-9_]*`
*   **Literals**:
    *   Integers: `123`
    *   Floats: `12.34` (Parsed but treated as opaque in current backend)
    *   Booleans: `true`, `false`
*   **Comments**: `// Single line comment` (Multi-line `/* ... */` not supported).

## 2. Types & Variables

### Basic Types
*   `int`: Signed 32-bit integer.
*   `bool`: Boolean value.
*   `void`: No value (return type only).

### Declarations
Variables must be declared before use (except functions, which are hoisted).
```c
int x = 10;
int y; // Uninitialized (undefined value)
```

### Immutable Constants
Variables declared with `const` cannot be reassigned. They MUST be initialized.
```c
const int MAX = 100;
MAX = 200; // Compile Error: Cannot assign to const variable.
```

### Arrays
Fixed-size, homogeneous arrays. Indices are 0-based.
*   **Declaration**: `int arr[10];`
*   **Access**: `arr[0] = 5;`
*   **Limitations**: No pointers type exposed. Passed by reference implicitly in IR. No bounds checking at runtime.

## 3. Operators & Expressions

### Arithmetic
*   `+`, `-`, `*`, `/`, `%`
*   `++`, `--`: Pre-increment/decrement only (`++i`).
*   *Note*: `++i` is syntax sugar for `i = i + 1`.

### Relational
*   `==`, `!=`, `<`, `>`, `<=`, `>=` (Result is `bool`)

### Logical
*   `&&`, `||` : Short-circuit evaluation.
*   `!` : Logical NOT.

## 4. Control Flow

### If-Else
```c
if (condition) { ... } else { ... }
```

### Loops
*   **While**: `while (cond) { ... }`
*   **For**: `for (init; cond; update) { ... }`
*   **Control**: `break` exits innermost loop. `continue` skips to next iteration.

## 5. Functions

### Definition
Functions can be defined anywhere in the global scope (Hoisting supported).
```c
void main() {
    print(foo()); // Valid!
}

int foo() {
    return 42;
}
```

### Recursion
Supported.

## 6. Input / Output

*   `print(expr)`: Prints integer value to stdout.
*   `readInt()`: Reads integer from stdin.

## 7. Memory Model
*   **Stack**: All variables are stack-allocated.
*   **Heap**: Not supported (No `malloc`).
*   **Safety**: No runtime checks for array bounds or stack overflow.
