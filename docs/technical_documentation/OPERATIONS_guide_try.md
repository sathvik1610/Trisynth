# Trisynth (NanoC) Operations Cheat Sheet

> **Quick reference for every operation supported by the Trisynth compiler.**

---

## 1. Arithmetic Operations

| Operation | Operator | Example | Result Type |
|---|---|---|---|
| Addition | `+` | `int x = 3 + 4;` | `int` |
| Subtraction | `-` | `int x = 10 - 3;` | `int` |
| Multiplication | `*` | `int x = 5 * 6;` | `int` |
| Integer Division | `/` | `int x = 10 / 3;` | `int` (truncates → 3) |
| Modulo | `%` | `int x = 10 % 3;` | `int` (→ 1) |
| Unary Minus | `-` | `int x = -5;` | `int` |

```c
void main() {
    int a = 20 + 5;     // 25
    int b = 20 - 5;     // 15
    int c = 20 * 5;     // 100
    int d = 20 / 5;     // 4
    int e = 20 % 6;     // 2
    int f = -7;         // -7
    print(a); print(b); print(c); print(d); print(e); print(f);
}
```

---

## 2. Relational / Comparison Operations

All comparison operators return `bool` (`true` or `false`).

| Operator | Meaning | Example |
|---|---|---|
| `==` | Equal | `x == 5` |
| `!=` | Not equal | `x != 0` |
| `<` | Less than | `x < 10` |
| `>` | Greater than | `x > 0` |
| `<=` | Less than or equal | `x <= 100` |
| `>=` | Greater than or equal | `x >= 1` |

```c
void main() {
    int x = 7;
    if (x == 7)  { print(1); }   // 1
    if (x != 3)  { print(1); }   // 1
    if (x < 10)  { print(1); }   // 1
    if (x > 5)   { print(1); }   // 1
    if (x <= 7)  { print(1); }   // 1
    if (x >= 7)  { print(1); }   // 1
}
```

---

## 3. Logical / Boolean Operations

Operands may be `bool` or `int` (nonzero counts as true); the result is `bool`. Uses **short-circuit evaluation** (the right operand is not evaluated when the left decides the result).

| Operator | Meaning | Example |
|---|---|---|
| `&&` | AND — both must be true | `a && b` |
| `\|\|` | OR — at least one true | `a \|\| b` |
| `!` | NOT — invert | `!a` |

```c
void main() {
    bool t = true;
    bool f = false;

    if (t && t)  { print(1); }   // 1
    if (t && f)  { print(0); } else { print(1); }  // 1 (false branch)
    if (t || f)  { print(1); }   // 1
    if (f || f)  { print(0); } else { print(1); }  // 1 (false branch)
    if (!f)      { print(1); }   // 1
    if (!t)      { print(0); } else { print(1); }  // 1 (false branch)
}
```

---

## 4. Shift Operations and Strength Reduction

You can write shifts directly with `<<` and `>>` (they bind looser than `+ -` and tighter than `< >`; for example `1 + 2 << 3` is `(1 + 2) << 3` = 24). There are no bitwise `&`, `|` or `^` operators.

The **Strength Reduction** optimizer also emits shifts for you: you write normal arithmetic and the compiler lowers it automatically:

| Written Code | Compiled IR | Condition |
|---|---|---|
| `x * 2` | `x << 1` | power of 2 |
| `x * 4` | `x << 2` | power of 2 |
| `x * 8` | `x << 3` | power of 2 |
| `x / 2` | `LT n x 0` / `ADD s x n` / `RSHIFT r s 1` | power of 2, non-constant `x` (negative dividends get a bias so the result truncates toward zero) |
| `x / 4` | `LT n x 0` / `LSHIFT hi n 2` / `SUB b hi n` / `ADD s x b` / `RSHIFT r s 2` | power of 2, non-constant `x` (bias = 3 for negative `x`) |
| `x * 0` | `0` | zero |
| `x * 1` | `x` | identity |

`x % 4`, `x * 3` and `x / 3` are not reduced. When every operand is a compile-time constant, the result is simply folded.

```c
void main() {
    int x = 3;
    int a = x * 4;    // strength-reduced to x << 2, then folded: 12
    int b = x * 8;    // strength-reduced to x << 3, then folded: 24
    print(a);   // 12
    print(b);   // 24
}
```

Because `x` is a known constant here, the final optimized IR is just `PRINT 12` / `PRINT 24`; no shift survives. To see the shifts in the output, use a value that is only known at run time, such as a function parameter or `readInt()`.

---

## 5. Increment / Decrement

Pre-increment and pre-decrement only. Valid on `int` variables and on `int` array elements (`++arr[i]`). They are expressions: `int y = ++x;` stores the new value in both `y` and `x`.

| Operator | Desugars to | Effect |
|---|---|---|
| `++x` | `x = x + 1` | Increments x by 1 |
| `--x` | `x = x - 1` | Decrements x by 1 |

```c
void main() {
    int x = 5;
    ++x;          // x is now 6
    print(x);     // 6
    --x;
    --x;          // x is now 4
    print(x);     // 4
}
```

> ❌ **NOT allowed**: `++(x+1)`, increment on `bool`, increment on `const`, and postfix `x++` / `x--`.

---

## 6. Assignment Operations

| Operation | Syntax | Notes |
|---|---|---|
| Declare + assign | `int x = expr;` | Most common |
| Reassign | `x = expr;` | Must be declared first |
| Array element assign | `arr[i] = expr;` | Index must be `int` |
| Const assign (once) | `const int x = 5;` | Cannot reassign later |

```c
void main() {
    int x = 10;          // declare + assign
    x = x + 5;          // reassign -> 15
    print(x);           // 15

    int arr[3];
    arr[0] = 100;
    arr[1] = arr[0] + 1;   // 101
    print(arr[1]);          // 101

    const int CAP = 255;
    print(CAP);             // 255
    // CAP = 300;           <- ERROR: Cannot assign to const
}
```

---

## 7. Variable Declarations

All variables must be declared **inside a function**. Global variables (including `const` and global arrays) are rejected with `E002 Semantic Error: Global variable '…' is not supported; declare it inside a function.`

```c
void main() {
// Plain declaration (value is undefined until assigned)
int x;
bool flag;

// Declaration with initializer
int y = 42;
bool active = true;

// Const (must initialize, cannot reassign)
const int MAX = 1000;
const bool DEBUG = false;

// Array (fixed positive size; elements are uninitialized until assigned)
int arr[10];
int buf[1];    // minimum valid size
}
```

---

## 8. Control Flow — if / else

```c
void main() {
    int x = 7;

    // Simple if
    if (x > 5) { print(1); }

    // if / else
    if (x == 10) {
        print(10);
    } else {
        print(0);     // prints 0
    }

    // Nested if / else-if chain
    if (x < 0) {
        print(-1);
    } else if (x == 0) {
        print(0);
    } else {
        print(1);     // prints 1
    }
}
```

---

## 9. Control Flow — while loop

```c
void main() {
    int i = 0;
    while (i < 5) {
        print(i);   // 0 1 2 3 4
        ++i;
    }
}
```

With `break` and `continue`:
```c
void main() {
    int i = 0;
    while (i < 10) {
        if (i == 7) { break; }      // exit loop
        if (i % 2 == 0) {
            ++i;
            continue;               // skip even numbers
        }
        print(i);   // 1 3 5
        ++i;
    }
}
```

---

## 10. Control Flow — for loop

```c
void main() {
    // Classic counting loop
    for (int i = 0; i < 5; ++i) {
        print(i);    // 0 1 2 3 4
    }

    // Countdown
    for (int j = 10; j > 0; --j) {
        print(j);    // 10 9 8 ... 1
    }

    // With break / continue
    for (int k = 0; k < 10; ++k) {
        if (k == 5) { break; }
        if (k == 2) { continue; }   // skip 2
        print(k);    // 0 1 3 4
    }
}
```

---

## 11. Functions

### Void function (no return value)
```c
void greet() {
    print(42);
}

void main() {
    greet();   // 42
}
```

### Value-returning function
```c
int add(int a, int b) {
    return a + b;
}

void main() {
    int result = add(3, 4);
    print(result);   // 7
}
```

### Recursive function
```c
int factorial(int n) {
    if (n <= 1) { return 1; }
    return n * factorial(n - 1);
}

void main() {
    print(factorial(5));   // 120
}
```

### Multiple parameters
```c
int power(int base, int exp) {
    if (exp <= 0) { return 1; }
    return base * power(base, exp - 1);
}

void main() {
    print(power(2, 10));   // 1024
}
```

---

## 12. Arrays

### Declaration & element access
```c
void main() {
    int arr[5];      // 5 elements, uninitialized until assigned
    arr[0] = 10;
    arr[1] = 20;
    int x = arr[0] + arr[1];
    print(x);        // 30
}
```

### Passing array to a function (by reference)
```c
void double_all(int arr[], int size) {
    int i = 0;
    while (i < size) {
        arr[i] = arr[i] * 2;
        ++i;
    }
}

void main() {
    int data[3];
    data[0] = 5;
    data[1] = 10;
    data[2] = 15;
    double_all(data, 3);
    print(data[0]);   // 10
    print(data[1]);   // 20
    print(data[2]);   // 30
}
```

### Function returning element from array
```c
int get_elem(int arr[], int idx) {
    return arr[idx];
}

void main() {
    int buf[4];
    buf[2] = 99;
    print(get_elem(buf, 2));   // 99
}
```

---

## 13. Scoping & const

```c
void main() {
    int x = 1;
    const int MAX = 500;

    {
        int x = 2;         // shadows outer x in this block only
        print(x);          // 2
        print(MAX);        // 500 — visible from outer scope
    }

    print(x);              // 1 — outer x restored
    print(MAX);            // 500 — const unchanged
}
```

---

## 14. I/O

```c
void main() {
    // Output — print(int/bool) prints the value then a newline (bool prints 1/0);
    // print(string) prints the text with no newline added
    print(42);
    print(1 + 2 * 3);

    // Input — reads one integer from stdin
    int n = readInt();
    print(n);              // echoes the number back
}
```

---

## 15. Constant Folding (Compile-Time Math)

The compiler evaluates constant expressions at compile time — zero runtime cost:

```c
void main() {
    int a = 3 * 4;          // folded → 12 (no MUL left in the optimized IR)
    int b = 100 - 50 + 10;  // folded → 60
    int c = 2 * 2 * 2 * 2;  // folded → 16
    print(a);   // 12
    print(b);   // 60
    print(c);   // 16
}
```

---

## 16. Complete Operator Precedence Table

| Priority | Operator(s) | Type | Associativity |
|---|---|---|---|
| 1 (highest) | `!`, unary `-`, `++`, `--` | Unary | Right |
| 2 | `*`, `/`, `%` | Multiplicative | Left |
| 3 | `+`, `-` | Additive | Left |
| 4 | `<<`, `>>` | Shift | Left |
| 5 | `<`, `>`, `<=`, `>=` | Relational | Left |
| 6 | `==`, `!=` | Equality | Left |
| 7 | `&&` | Logical AND | Left |
| 8 | `\|\|` | Logical OR | Left |
| 9 (lowest) | `=` | Assignment | Right |

---

## 17. What is NOT Supported

| Feature | Status |
|---|---|
| Floating point arithmetic | ❌ Not supported (`float` is not a keyword; `3.14` is a lexical error) |
| Pointers (`*`, `&`) | ❌ Not supported |
| Strings | ✅ Supported: `string` variables, arrays, parameters and return values, and `print`. `==` / `!=` compare pointers only; no indexing, concatenation or other operators |
| `switch` / `case` | ❌ Use `if/else if` chain |
| Ternary `? :` | ❌ Use `if/else` |
| `while(true)` infinite loop without `break` | ⚠️ Compiles, runs forever |
| Array as return type | ❌ Return elements individually |
| Nested arrays `int arr[3][3]` | ❌ Not supported |
| Post-increment `x++` | ❌ Use `++x` (pre-increment only) |
| Implicit int↔bool conversion | ❌ Type Error in assignments, initializers and call arguments. `if` / `while` conditions and `&&` / `||` operands do accept `int` (nonzero = true); a `for` condition must be `bool` |
| Dynamic array size `int arr[n]` | ❌ Size must be integer literal |
| Array out-of-bounds check | ❌ Undefined behavior at runtime |
| Global variables / global arrays | ❌ Rejected: declare variables inside a function |
| Nested function declarations | ❌ Rejected (functions must be top-level) |
| `char` type and `'a'` literals | ❌ `char` is a keyword but rejected by the analyzer (`Unsupported intrinsic type 'char'`); a character literal is lexed but the parser rejects it |
| `uint32` | ❌ Not a keyword |
| Bitwise `&`, `\|`, `^` | ❌ Lexical error (only `<<` and `>>` exist) |
| Modifying a `const` array element | ❌ Semantic error |

---

## 18. Native Strings & Character Pointers (Advanced)

Trisynth has a `string` type that behaves like a C `char*`: a string variable holds the address of a literal stored in the data section.

```c
void main() {
    // String Initialization
    string msg = "Compiler Running\n";
    print(msg);
    
    // String array: each element is a pointer to a literal
    string words[3];
    words[0] = "Apple\n";
    words[1] = "Banana\n";
    print(words[1]);   // prints 'Banana'
}
```

- Each distinct string literal is emitted once into the `.data` section as `str_N`.
- Assigning `words[0] = "Apple
"` stores the 64-bit address of that literal into the array slot.
- `print(string)` writes the text exactly as given (add `
` yourself for a newline).
- Elements of a `string` array that were never assigned hold garbage, so do not print them.
