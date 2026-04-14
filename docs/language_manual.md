# Trisynth Language Reference Manual

Welcome to the official master manual for the Trisynth programming language. This document defines the exact lexical structure, grammar, architectural behavior, and translation capabilities of Trisynth.

---

## 1. 📌 Introduction

### 1.1 Purpose of the Language
Trisynth exists to bridge the gap between high-level expressive programming and ultra-low-level bare-metal execution. Functioning as an educational but fully realized standalone compiler, Trisynth solves the problem of "black-box" compilation by handling all custom intermediate representations (IR), aggressive semantic analysis, and direct instruction emission explicitly without external monoliths like LLVM.

### 1.2 Design Goals
- **Transparency**: Every phase of the compiler (Tokens $\rightarrow$ AST $\rightarrow$ IR $\rightarrow$ ASM) can be inspected via flags.
- **Performance**: Capable of Ahead-Of-Time (AOT) compilation utilizing significant optimization techniques (CSE, Constant Folding, Dead-Code Elimination).
- **Safety**: Fully static type resolution, block-scoping, and immutable variables ensure logical stability at compile time.
- **Portability**: Native code generators seamlessly switch output between `x86-64` (Intel/AMD) and `RISC-V`.

### 1.3 Key Features
- **Statically Typed**: Types (`int`, `string`, `bool`) are resolved deterministically before any code generation occurs.
- **Immutable Bounds**: Fully supports the `const` keyword natively validated via semantic firewall to prevent mutable overwrite.
- **Architecture-Agnostic IR**: Three-Address Code (TAC) intermediate language naturally maps to infinite pseudo-registers prior to hardware commitment.

### 1.4 Competitive Positioning
- **Compared to C:** Trisynth offers a stricter, predictable runtime subset. It eliminates undefined behavior associated with raw, unstructured pointer arithmetic, favoring bounded static array access mapped safely to the functional stack.
- **Compared to LLVM-based Compilers:** Trisynth prioritizes architectural transparency over monolithic scaling. Instead of abstracting output via the massive LLVM infrastructure, Trisynth natively drives its own IR and optimizer down to raw executable instructions instantly, making it the perfect vessel for studying compiler engineering from Lexer to Linker.

---

## 2. 🧱 Overall Language Structure

### 2.1 Program Structure
- **Entry Point**: Program execution strictly begins at the `main` function (e.g., `void main()`). 
- **File Structure**: Source files are `.tri` extensions containing a sequence of function or variable declarations.

### 2.2 Execution Model
Trisynth is a strictly **Compiled, Multi-Pass AOT** language.
1. **Pass 1 (Lex & Parse)**: Raw characters are streamed into an Abstract Syntax Tree (AST).
2. **Pass 2 (Semantic Analysis)**: The semantic engine verifies scope blocks to lock variable bindings and guarantees type validity.
3. **Pass 3 (IR Generation)**: Flattens the AST into generic Three Address Codes mapping to pseudo-registers.
4. **Pass 4 (Optimization)**: Strength reduction, Constant Folding, and Dead Code mapping execute linearly on the IR.
5. **Pass 5 (Codegen)**: Direct NASM strings (x86-64) or Assembly strings (RISC-V) are emitted.

---

## 3. 🔤 Lexical Structure

### 3.1 Character Set
Trisynth files are decoded using the standard **ASCII** character set. 

### 3.2 Tokens
Trisynth consists of rigidly defined token categories:
- **Keywords**: Strictly reserved dictionary bindings.
- **Identifiers**: Names representing variables, arrays, or functions.
- **Literals**: Hard-coded constant integer and string sequence values.
- **Operators**: Mathematical, bitwise, boolean short-circuits, and unary mutators. 
- **Delimiters**: Structural wrappers (`{`, `}`, `(`, `)`, `;`).

### 3.3 Keywords
The exact reserved words:
`if`, `else`, `while`, `for`, `break`, `continue`, `return`, `int`, `void`, `const`, `print`, `readInt`, `string`, `true`, `false`

### 3.4 Identifiers
Identifiers must start with a letter tracking to unlimited alpha-numeric combinations alongside underscores.
> **Regex Definition**:
> `Identifier → [a-zA-Z_][a-zA-Z0-9_]*`

### 3.5 Literals
Integer literals are 64-bit signed values existing within the standard mathematical range: `[-2^63, 2^63 - 1]`. Lexical overflow results in a compile-time error due to overflow. String literals are demarcated via double quotes `"text"`.

### 3.6 Comments
Trisynth supports standard non-nesting C-style ignore blocks:
- **Single-line**: `// This is a line comment`
- **Multi-line**: `/* This ignores large blocks */`

---

## 4. 📐 Syntax (Grammar)

The language parses via standard recursive descent mechanics represented by the following fully explicit EBNF formulation.

```ebnf
program        ::= declaration*
declaration    ::= var_decl | func_decl
var_decl       ::= ("const")? ("int" | "string" | "bool") Identifier ("[" Integer "]")? ("=" expression)? ";"
func_decl      ::= ("int" | "void" | "string" | "bool") Identifier "(" param_list? ")" block
param_list     ::= type Identifier ("," type Identifier)*

block          ::= "{" statement* "}"
statement      ::= var_decl 
                 | expr_stmt 
                 | if_stmt 
                 | while_stmt 
                 | for_stmt 
                 | return_stmt 
                 | print_stmt
                 | break_stmt
                 | continue_stmt

if_stmt        ::= "if" "(" expression ")" block ("else" block)?
while_stmt     ::= "while" "(" expression ")" block
for_stmt       ::= "for" "(" (var_decl | expr_stmt)? ";" expression? ";" expression? ")" block
break_stmt     ::= "break" ";"
continue_stmt  ::= "continue" ";"
expr_stmt      ::= expression ";"
print_stmt     ::= "print" "(" expression ")" ";"
return_stmt    ::= "return" expression? ";"

expression     ::= assignment | logical_or
assignment     ::= Identifier ("[" expression "]")? "=" expression

logical_or     ::= logical_and ("||" logical_and)*
logical_and    ::= equality ("&&" equality)*
equality       ::= relational (("==" | "!=") relational)*
relational     ::= shift (("<" | ">" | "<=" | ">=") shift)*
shift          ::= additive (("<<" | ">>") additive)*
additive       ::= multiplicative (("+" | "-") multiplicative)*
multiplicative ::= unary (("*" | "/" | "%") unary)*
unary          ::= ("-" | "!" | "++" | "--") unary | primary
primary        ::= Integer | StringLiteral | Identifier | "(" expression ")" | function_call
Integer        ::= [0-9]+
```

---

## 5. 📊 Data Types

### 5.1 Primitive Types
Currently, Trisynth natively supports:
- `int`: 64-bit signed integer values.
- `bool`: Intrinsic truth tracking mapping via true/false evaluations natively.
- `string`: Fully functional literal allocations generated safely into `.data` blocks.
- `void`: Used purely to declare functions returning no stack value.

### 5.2 Composite Types & Arrays
- **Static 1D Arrays**: Supported strictly via contiguous block allocations nested directly into the local execution stack frame without needing a heap. 

**Execution and Edge Cases:**
```c
int matrix[10];
matrix[0] = 5;

// ⚠️ EDGE CASE: Generates explicit runtime boundary fault
// Does not get caught at compile-time currently due to lack of bounds analysis
matrix[500] = 10; 

// ❌ E003: Invalid Usage (Dynamically sized constraints)
int size = 5;
int dynamic_arr[size]; // Arrays MUST be bounded by static literal components
```

*Limitation*: Multi-dimensional nested matrices (e.g., `int matrix[5][5];`) and dynamically sized array lengths are explicitly excluded to force simple, deterministic memory offset load operations natively.

### 5.3 Strings Support
Unlike basic C constructs, Trisynth actively tokenizes and pushes string literals properly into assembly generation, emitting explicit AST load instructions (`OpCode.LOAD_STR`) mapping into the hardware string heap automatically.

```c
string welcome = "Hello Evaluator";
print(welcome); // Maps to [rel str_0] dynamically 
```

### 5.4 Unsupported Type Hard-Block
`float` and `char` syntaxes intentionally trigger hard `E002` violations specifically intercepted by the Semantic analyzer. These bounds protect underlying X86 `imul`/base registers from unpredictable ASM crashes.

```c
float pi = 3.14; 
// ❌ E002: Semantic Error: Unsupported intrinsic type 'float'
```

### 5.5 Precise Type Checking Rules
Trisynth semantic rules enforce strict logic matching prior to any generation.

**Assignment Consistency Rules:**
`int ← int       ✅`
`string ← int    ❌`
`int ← const int ✅`

---

## 6. 🔢 Variables and Declarations

### 6.1 Variable Declaration Syntax
Standard declarations bind to static types and can optionally consume literal initializers instantly.
```c
int count;
string name = "John";
const int absolute_max = 500;
```

### 6.2 Immutability Firewall (`const`)
Binding a variable structurally with the `const` keyword signals the Semantic Analyzer to restrict any overlapping assignments anywhere within the scope recursively.

```c
const int bounds = 100;
bounds = 50; 
// ❌ E002 Semantic Error: Cannot assign to const variable 'bounds'
```

### 6.3 Scope Rules & Shadowing
The Trisynth analyzer utilizes deeply layered Symbol Tables tracking every block entry correctly:
- **Block Encasement**: Each block (`{}`) automatically structures and instantiates a new local symbol scope mapping identifiers.
- **Lookup Mechanics**: Identity resolution checks from the absolute nearest Scope outward: `Current Scope → Parent Scope → Global Scope`.
- **Shadowing**: IS permitted logically; locally bound states can supersede identically named variables declared previously.

---

## 7. 🧮 Expressions and Operators

### 7.1 Operator Precedence Table (Descending Order)
| Operator | Description | Associativity |
| :------- | :---------- | :------------ |
| `()` `[]` | Grouping, Array Indexing | Left-to-Right |
| `++` `--` | Unary Pre-Mutators | Right-to-Left |
| `*` `/` `%` | Multiplication, Division, Modulo | Left-to-Right |
| `+` `-` | Addition, Subtraction | Left-to-Right |
| `<<` `>>` | Bitwise Shifts | Left-to-Right |
| `<` `>` `<=` `>=` | Relational Evaluations | Left-to-Right |
| `==` `!=` | Equality | Left-to-Right |
| `&&` | Short-Circuit Logical AND | Left-to-Right |
| `\|\|` | Short-Circuit Logical OR | Left-to-Right |
| `=` | Assignment Tracking | Right-to-Left |

### 7.2 Short-Circuit Logical Execution
Trisynth maps boolean combinations intelligently creating explicit sequence jumps in IR guaranteeing functions on false conditions don't execute!

---

## 8. 🔁 Control Flow

### 8.1 Conditional Statements
Branching structures compile utilizing comparison registers followed strictly by `JMP_IF_FALSE` intermediate opcodes.
```c
if (val < 10 && val > 0) {
    print(val);
} else {
    print("Invalid");
}
```

### 8.2 Loops & State Manipulation
Trisynth formally incorporates `while` and standard `for` loop construction mappings. Furthermore, nested AST depths gracefully permit dynamic cycle manipulation via `break` and `continue`.

**Valid Usage vs Execution Edge Cases:**
```c
// Valid standard deterministic looping
for (int count = 0; count < 10; ++count) {
    if (count == 5) {
        continue; // Bypasses loop payload safely bridging outer scope label
    }
    print(count);
}

// ⚠️ EDGE CASE: Deliberate Logic Saturation (Infinite Loops)
while (true) {
    print("Locked Process");
    break; // Loop tracked cleanly via Stack Exit popping
}
```

---

## 9. 🧩 Functions

### 9.1 Function Declarations
Functions form independent stack boundaries bounding local variables explicitly.
```c
int calculate_sum(int a, int b) {
    return a + b;
}
```

### 9.2 Parameters
Trisynth parameters are evaluated logically **By Value**. Copies are loaded directly into sequential pseudo-registers leading directly over to `rdi/rsi/rdx` and standard system stacks strictly adhering formal consistency with the **System V ABI**.

---

## 10. 🧠 Memory Model

1. **Stack Emulation Exclusivity**: 
   Trisynth completely ignores "Heap allocations" or traditional Garbage Collection penalties. All declarations compile directly against **StackFrames**.
   
2. **Variable Allocation**: 
   When declaring `int x;`, the code generator natively shifts the functional `rsp` stack boundary precisely exactly one frame deeper mapped backward (`[rbp - offset]`). Pseudo-memory is naturally "cleaned" automatically simply by returning the base `rsp` to `rbp` during the hardware Epilogue phase.

---

## 11. ⚠️ Error Handling

### 11.1 Compile-Time Errors
- **Syntax Errors**: Unmatched delimiters or misspelled keywords correctly halt execution immediately with contextual line-numbers via the Parser boundary.
- **Type/Semantic Errors**: Firing during AST analysis—using variables before they form their binding scope triggers fatal symbol table violations stopping output compilation dead.

### 11.2 Exteme Edge Cases & Structural Validations
1. **Division by Zero**: Intercepted formally; compiling literal `10 / 0` triggers a fatal compile-time block, whereas runtime zero division generates an OS-level mathematical exception fault flawlessly.
2. **Array Out-Of-Bounds**: Fails explicitly at runtime via unmapped memory traversal, demonstrating classic raw unabstracted C-level mapping speeds without heavy runtime limit boundary checking constraints.

### 11.3 Invalid Programs and Explicit Error Classification
Trisynth abstracts syntax and logical faults into industrial-grade classifications intercepting them seamlessly with contextual line tracking:

```c
// E001: Undeclared Variable Binding
x = 10;
// ❌ E001: Undefined variable 'x' at line 2

// E002: Type/Semantic Mismatch
int a;
a = "hello"; 
// ❌ E002: Type mismatch assigning to strongly-typed 'int' identifier at line 7

// E003: Structural Syntax Failure
int z = 5
// ❌ E003: Expected ';' after expression at line 9
```

---

## 12. 🛠️ Standard Library

Trisynth actively provides core system routines directly invoking standard OS bindings generated statically inside `.text` headers.

### 12.1 Built-in Functions

- `print(value)`: Generically adapts outputs string text dynamically via `extern printf` formatting, mapping identical values directly down to strings implicitly.
- `readInt()`: Actively interrupts programmatic flow, capturing console keyboard standard input dynamically feeding via an internally generated `extern scanf` listener seamlessly returning 64-bit bounds outputs!

---

## 13. ⚙️ AST and Intermediate Representation

Trisynth bridges high level scripts towards Hardware Emission strictly using layered structures handling both Object hierarchies AND Assembly simulations natively.

### 13.1 Abstract Syntax Tree (AST) Formations

Evaluating deeply parsed syntaxes yields structural dependency graphs internally identifying exactly what instructions possess parent-child evaluations explicitly.

**Transforming `a = b + c`:**
```text
        =
      /   \
     a     +
          / \
         b   c
```

### 13.2 Intermediate Representation (Three-Address Code)

Before compiling strictly down towards the NASM or RISC-V output channels, the AST flattens producing highly expressive IR enabling pure optimization logic scaling. 

Rather than messy nested AST graphs, instructions map structurally into linear opcodes:
- `OpCode.ALOAD`: Load Array boundaries onto generic pseudo states.
- `OpCode.ASTORE`: Bind literal outputs immediately structurally into Array layouts.
- `OpCode.JMP_IF_FALSE`: Conditional control routing.
- `OpCode.ADD`: Explicit arithmetic addition tracking three independent registers `(target, arg1, arg2)`.

---

## 14. 💻 Compiler Usage

Trisynth can be easily commanded from external CLI scripts passing structural runtime flags generating varying layers of AST / ASM tracking natively.

**Core Commands:**
```bash
# General Output Compilation 
trisynth input.tri

# Emitting AST structure tree exclusively
trisynth --ast file.tri

# Emitting flattened TAC Intermediate Representation
trisynth --ir file.tri

# Display side-by-side Cross Compiled Architectural Logic Output (x86 & RISC-V)
trisynth --compare-asm file.tri
```

---

## 15. 📎 Appendix

### A. Core Reserved Words Table
| Keyword | Description |
| :------ | :---------- |
| `int`, `string` | Primary hardware bindings natively validated and emitted. |
| `const` | Absolute immutability restriction. |
| `for`, `while` | Bounded iteration wrappers cleanly mapping looping depths. |
| `break`, `continue`| Loop architectural traversal bounds manipulators. |
| `print`, `readInt` | Standard I/O external linkage interceptors. |


