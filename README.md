# Trisynth Compiler

**Trisynth** is a custom-built native compiler for **NanoC**, a minimal C-like programming language designed for educational purposes.  
This project focuses on demonstrating the complete compiler pipeline, from source code analysis to native code generation.

---

## Project Overview

The goal of this project is to design and implement a modular compiler that translates NanoC programs into native executable code.  
The compiler follows a structured, phase-wise architecture inspired by classical compiler design principles.

The compilation pipeline includes:
- Lexical analysis
- Syntax analysis
- Semantic analysis
- Intermediate Representation (IR) generation
- IR-level optimizations
- Native assembly code generation

The compiler generates architecture-specific assembly code, which is assembled into an executable using an external assembler.

---

## About NanoC

**NanoC** is a small, statically typed, imperative programming language with a C-like syntax.  
It is intentionally minimal to ensure that all compiler phases can be implemented completely and correctly within a semester.

### Key Characteristics
- Integer-only data type
- Block-structured syntax
- Explicit variable declarations
- Simple control flow constructs
- Single entry point (`main`)

NanoC avoids advanced features such as pointers, arrays, functions, and floating-point arithmetic to reduce complexity and keep the focus on compiler construction.

---

## Language Features

- Data Type: `int`
- Arithmetic operations: `+ - * /`
- Relational operations: `< > <= >= == !=`
- Control flow:
  - `if` / `else`
  - `while`
- Built-in output statement: `print`
- Single program entry point: `main`

---

## Compiler Architecture

Trisynth is implemented using a **modular architecture**, where each compiler phase is implemented as a separate component.

### Compilation Pipeline

```

Source Code (NanoC)
↓
Lexical Analysis
↓
Parsing (AST Generation)
↓
Semantic Analysis
↓
Intermediate Representation (IR)
↓
IR Optimization
↓
Assembly Generation
↓
Assembler (NASM / GAS)
↓
Native Executable

```

---

## Project Structure

```

minic-compiler/
│
├── README.md
│
├── docs/
│   ├── language_spec.md
│   ├── grammar.md
│   └── design.md
│
├── src/
│   ├── main.py
│   │
│   ├── lexer/
│   │   ├── tokens.py
│   │   └── lexer.py
│   │
│   ├── parser/
│   │   └── parser.py
│   │
│   ├── ast/
│   │   └── nodes.py
│   │
│   ├── semantic/
│   │   └── analyzer.py
│   │
│   ├── ir/
│   │   └── ir_generator.py
│   │
│   ├── optimizer/
│   │   └── passes.py
│   │
│   └── backend/
│       └── asm_gen.py
│
├── tests/
│   ├── lexer_test.mc
│   ├── parser_test.mc
│   └── sample_program.mc
│
└── output/
├── program.asm
└── program.out

````

---

## Technology Stack

- **Implementation Language:** Python 3
- **Target Architectures:** x86-64 / RISC-V
- **Assembler:** NASM or GNU Assembler (GAS)
- **Operating System:** Linux

## How to Run (Week 2)

### 1. Run the Compiler (Interactive Mode)
Run the main entry point without arguments to start the interactive session.

```bash
python -m src.main
```

### 2. Run the Compiler (File Mode)
```bash
python -m src.main path/to/source.nc
```

### 3. Run Automated Tests
The project uses `pytest` for verification.

```bash
python -m pytest
```

### 3. Usage inside Python
```python
from src.frontend.lexer import Lexer
from src.frontend.parser import Parser

code = "int x = 10;"
tokens = Lexer(code).tokenize()
ast = Parser(tokens).parse()
print(ast)
````

3. The lexer outputs the token stream to standard output.

---

## Example NanoC Program

```c
int main() {
    int x = 5;
    int y = 10;
    int z = x + y;
    print(z);
}
```

---

## Design Philosophy

The NanoC language and Trisynth compiler are intentionally minimal.
The focus of the project is not on language richness, but on **clarity, correctness, and completeness of the compiler pipeline**.

This approach ensures:

* Clear demonstration of compiler concepts
* Manageable implementation complexity
* Strong alignment with compiler theory taught in class

---

## Future Extensions

The modular design of Trisynth allows for potential future extensions, such as:

* Additional optimization passes
* Support for functions
* Alternative backend targets
* Transpilation to high-level languages

These features are not part of the current scope.

---

## Contributors

* V. Chitraksh (CS23B054)
* P. Sathvik (CS23B042)
* S. Danish Dada (CS23B047)




