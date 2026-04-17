# NanoC Operations Cheat Sheet

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

Operands must be `bool`. Uses **short-circuit evaluation**.

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

## 4. Bitwise / Shift Operations (Optimizer)

These are emitted by the **Strength Reduction** optimizer — you write normal arithmetic and the compiler lowers it automatically:

| Written Code | Compiled IR | Condition |
|---|---|---|
| `x * 2` | `x << 1` | power of 2 |
| `x * 4` | `x << 2` | power of 2 |
| `x * 8` | `x << 3` | power of 2 |
| `x / 2` | `x >> 1` | power of 2 |
| `x / 4` | `x >> 2` | power of 2 |
| `x * 0` | `0` | zero |
| `x * 1` | `x` | identity |

```c
void main() {
    int x = 3;
    int a = x * 4;    // compiled: x << 2 = 12
    int b = x * 8;    // compiled: x << 3 = 24
    int c = x / 2;    // wait -- x=3, 3/2=1 (integer div, then >> 1 => 1)
    print(a);   // 12
    print(b);   // 24
}
```

---

## 5. Increment / Decrement

Pre-increment and pre-decrement only. **Only valid on `int` variables.**

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

> ❌ **NOT allowed**: `++arr[0]`, `++(x+1)`, increment on `bool`, increment on `const`.

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
    x = x + 5;          // reassign → 15
    print(x);           // 15

    int arr[3];
    arr[0] = 100;
    arr[1] = arr[0] + 1;   // 101
    print(arr[1]);          // 101

    const int CAP = 255;
    print(CAP);             // 255
    // CAP = 300;           ← ERROR: Cannot assign to const
}
```

---

## 7. Variable Declarations

```c
// Plain declaration (value is undefined until assigned)
int x;
bool flag;

// Declaration with initializer
int y = 42;
bool active = true;

// Const (must initialize, cannot reassign)
const int MAX = 1000;
const bool DEBUG = false;

// Array (fixed positive size, elements = 0 by default)
int arr[10];
int buf[1];    // minimum valid size
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
    int arr[5];      // 5 elements, all 0
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
    // Output — prints value then newline
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
    int a = 3 * 4;          // folded → 12 (no MUL in IR)
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
| 1 (highest) | `!`, `++`, `--` | Unary | Right |
| 2 | `*`, `/`, `%` | Multiplicative | Left |
| 3 | `+`, `-` | Additive | Left |
| 4 | `<`, `>`, `<=`, `>=` | Relational | Left |
| 5 | `==`, `!=` | Equality | Left |
| 6 | `&&` | Logical AND | Left |
| 7 | `\|\|` | Logical OR | Left |
| 8 (lowest) | `=` | Assignment | Right |

---

## 17. What is NOT Supported

| Feature | Status |
|---|---|
| Floating point arithmetic | ❌ Lexed but not fully executed |
| Pointers (`*`, `&`) | ❌ Not supported |
| Strings | ✅ Fully mapped mapping natively evaluating C-style static boundaries loading dynamically! |
| `switch` / `case` | ❌ Use `if/else if` chain |
| Ternary `? :` | ❌ Use `if/else` |
| `while(true)` infinite loop without `break` | ⚠️ Compiles, runs forever |
| Array as return type | ❌ Return elements individually |
| Nested arrays `int arr[3][3]` | ❌ Not supported |
| Post-increment `x++` | ❌ Use `++x` (pre-increment only) |
| Implicit int↔bool conversion | ❌ Type Error at compile time |
| Dynamic array size `int arr[n]` | ❌ Size must be integer literal |
| Array out-of-bounds check | ❌ Undefined behavior at runtime |

---

## 18. Native Strings & Character Pointers (Advanced)

Trisynth strictly mimics exact C-layer behaviors natively extracting literal allocations dynamically without external string classes implicitly!

```c
void main() {
    // String Initialization
    string msg = "Compiler Running\n";
    print(msg);
    
    // String arrays allocating pointers sequentially!
    string words[3];
    words[0] = "Apple\n";
    words[1] = "Banana\n";
    print(words[1]);   // prints 'Banana'
}
```

- When allocating `words[0] = "Apple"`, Trisynth dynamically registers an embedded `.data` segment literal `str_X`.
- It then physically extracts the raw 64-bit AMD64/RISC-V pointer mapping cleanly into the `words` stack offset natively mirroring standard C `char*` interactions flawlessly!
