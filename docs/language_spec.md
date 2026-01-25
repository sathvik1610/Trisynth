


# Language Specification: NanoC (Custom Subset)

## 1. Introduction

NanoC is a simple, statically typed, imperative programming language designed for educational purposes.  
The language is intentionally minimal to enable the complete implementation of all major compiler phases, including lexical analysis, parsing, semantic analysis, intermediate representation generation, optimization, and native code generation.

NanoC follows a C-like syntax to ensure familiarity while avoiding complex features that are unnecessary for demonstrating compiler construction concepts.

---

## 2. Design Goals

The primary design goals of NanoC are:

- Simplicity of syntax and semantics
- Ease of lexical and syntactic analysis
- Clear mapping to an intermediate representation
- Suitability for native code generation
- Feasibility of full compiler implementation within a semester

---

## 3. Program Structure

- Every NanoC program consists of a single entry point: `main`.
- Execution begins from the `main` block.
- Statements are grouped using braces `{ }`.

### Example:
```c
int main() {
    int x = 5;
    print(x);
}
````

---

## 4. Data Types

NanoC supports the following data type:

* `int` : 32-bit signed integer

No floating-point types, strings, arrays, or user-defined types are supported.

---

## 5. Variables and Declarations

* Variables must be declared before use.
* All variables are statically typed.
* Initialization during declaration is optional.

### Syntax:

```c
int x;
int y = 10;
```

---

## 6. Expressions

NanoC supports arithmetic and relational expressions.

### Arithmetic Operators:

* `+`  (addition)
* `-`  (subtraction)
* `*`  (multiplication)
* `/`  (division)

### Relational Operators:

* `<`, `>`, `<=`, `>=`, `==`, `!=`

### Example:

```c
x = (a + b) * 2;
```

---

## 7. Control Flow Statements

### 7.1 Conditional Statement

NanoC supports `if` and `if-else` constructs.

```c
if (x > y) {
    print(x);
} else {
    print(y);
}
```

### 7.2 Iteration Statement

NanoC supports the `while` loop.

```c
while (x > 0) {
    x = x - 1;
}
```

---

## 8. Input / Output

NanoC provides a built-in output statement:

* `print(expression);`

This prints the evaluated value of the expression to standard output.

```c
print(x);
```

---

## 9. Lexical Structure

### 9.1 Keywords

```
int, if, else, while, print, main
```

---

### 9.2 Identifiers

* Identifiers must start with a letter or underscore.
* May contain letters, digits, and underscores.

```
[a-zA-Z_][a-zA-Z0-9_]*
```

---

### 9.3 Integer Literals

* Sequence of digits representing non-negative integers.

```
[0-9]+
```

---

### 9.4 Operators

```
+  -  *  /  =  ==  <  >  <=  >=  !=
```

---

### 9.5 Delimiters

```
;  (  )  {  }
```

---

### 9.6 Comments

* Single-line comments start with `//` and continue until the end of the line.

```c
// This is a comment
```

---

## 10. Whitespace

Whitespace characters (spaces, tabs, newlines) are ignored except as separators between tokens.

---

## 11. Error Handling (Lexical Level)

* Any unrecognized character is reported as a lexical error.
* The lexer reports the invalid character and its position in the source code.

---

## 12. Limitations

The following features are intentionally not supported in NanoC:

* Floating-point numbers
* Strings
* Arrays
* User-defined functions
* Pointers
* Recursion

These limitations help keep the language suitable for demonstrating compiler principles without unnecessary complexity.

---

## 13. Conclusion

NanoC provides a clean and minimal language design that is sufficient to demonstrate all major phases of compiler construction. Its simplicity ensures that the focus remains on compiler architecture and implementation rather than language complexity.


