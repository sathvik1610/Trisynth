# Project Folder Structure - Trisynth

This document outlines the folder structure of the Trisynth Compiler project.
The canonical top-level documents are `README.md`, `INSTALL.md`, `SETUP.md`,
`Language_Manual.md` and `Project_Report.md`.

```
Trisynth/
├── README.md, INSTALL.md, SETUP.md, Language_Manual.md, Project_Report.md
├── requirements.txt            # pytest only (used by the test suite)
├── .gitignore
├── setup.sh, setup.bat         # toolchain setup (Linux/WSL, Windows)
├── build_releases.py, build_deliverables.py, trisynth.spec   # packaging (PyInstaller)
├── bin/linux/nasm              # bundled nasm binary
├── output.asm, output_riscv.s  # generated into the current directory by main.py
│
├── src/
│   ├── main.py                 # CLI driver, IRInterpreter helper, nasm/gcc/qemu invocation
│   ├── my_program.tri
│   ├── frontend/
│   │   ├── lexer.py            # Lexical analysis
│   │   ├── token_type.py       # Token definitions
│   │   ├── parser.py           # Syntax analysis (AST generation)
│   │   └── ast.py              # AST node definitions
│   ├── semantic/
│   │   ├── analyzer.py         # Type checking & scope resolution
│   │   └── symbol_table.py     # Symbol table
│   ├── ir/
│   │   ├── ir_gen.py           # IR generation
│   │   └── instructions.py     # IR instruction definitions
│   ├── optimization/
│   │   ├── strength_reduction.py
│   │   ├── cse.py              # Common subexpression elimination
│   │   ├── copy_propagation.py
│   │   ├── constant_fold.py
│   │   ├── dead_code.py
│   │   └── optimizer.py        # Fixed-point driver class (main.py sets up its own pass list)
│   └── backend/
│       ├── codegen_x86.py      # x86-64 (NASM) generation
│       ├── riscv/
│       │   └── codegen_riscv.py   # RISC-V 64 (GNU AS) generation
│       └── common/
│           └── stack_frame.py  # Shared stack-slot allocator
│
├── tests/
│   ├── unit/                   # pytest suite (186 tests): lexer, parser, semantic, IR,
│   │                           #   optimizer passes, strings, whole pipeline
│   ├── programs/               # test01_fibonacci.tri ... test10_power.tri, mega_test.tri
│   ├── FinalDemo/              # 8 demonstration programs
│   ├── verification/           # debug_compliance.py
│   └── demo1_*.tri ... demo7_*.tri
│
├── examples/                   # *.nc sample programs
│
├── docs/
│   ├── folder_structure.md     # This file
│   ├── TEAM_GUIDE.md / .pdf    # Viva & architecture guide
│   ├── proposal.txt, *.pdf     # Proposal and reports
│   ├── technical_documentation/   # implementation_guide_backend.md, OPERATIONS_guide_try.md, language_manual.md
│   ├── deliverables/           # Installation_Manual, Language_Manual, Technical_Documentation (.md/.pdf)
│   ├── latex/
│   └── reports/
│
├── releases/                   # Zipped release builds
└── build/, dist/               # PyInstaller output (git-ignored)
```

The compiler writes its build artifacts into the **current working directory**:
`output.asm`, `output_riscv.s`, `output.o` (`.obj` on native Windows), `program`
(`program.exe` on native Windows) and `program_riscv`. Only `output/` (a directory
that is not currently present), `build/`, `dist/` and `.idea/` are git-ignored,
so these generated files are not ignored automatically.
