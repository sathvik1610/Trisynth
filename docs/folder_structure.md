# Project Folder Structure - Trisynth

This document outlines the organized folder structure for the Trisynth Compiler project.

```
Trisynth/
├── .git/
├── .gitignore             # Git ignore file
├── README.md              # Project overview and instructions
├── requirements.txt       # Python dependencies
│
├── docs/                  # Documentation
│   ├── folder_structure.md # This file
│   ├── language_spec.md    # Language specification (NanoC)
│   └── proposal.txt        # Original project proposal
│
├── src/                   # Source Code
│   ├── frontend/          # Frontend Analysis
│   │   ├── lexer.py       # Lexical Analysis
│   │   ├── token_type.py  # Token definitions
│   │   ├── parser.py      # Syntax Analysis (AST generation)
│   │   └── ast.py         # AST Node definitions
│   │
│   ├── semantic/          # Semantic Analysis
│   │   ├── analyzer.py    # Type checking & scope resolution
│   │   └── symbol_table.py # Symbol table implementation
│   │
│   ├── ir/                # Intermediate Representation
│   │   ├── ir_gen.py      # IR Generation logic
│   │   └── instructions.py # IR Instruction definitions
│   │
│   ├── optimization/      # Optimization Passes
│   │   ├── optimizer.py   # Main optimizer driver
│   │   └── constant_fold.py # Constant Folding pass
│   │
│   ├── backend/           # Backend Synthesis
│   │   ├── codegen_x86.py # x86-64 Assembly generation
│   │   └── codegen_riscv.py # RISC-V Assembly generation (optional)
│   │
│   └── main.py            # Compiler entry point (CLI driver)
│
├── tests/                 # Test Suite
│   ├── unit/              # Unit tests for independent modules
│   └── integration/       # End-to-end compiler tests
│
└── output/                # Build Artifacts (Ignored by git)
    ├── *.s                # Generated Assembly files
    ├── *.o                # Object files
    └── *.exe              # Final executables
```
