# Trisynth Compiler — Backend & Code Generation

> **This document is a continuation of the main README.**
> It covers everything that happens **after the optimization passes** —
> from IR to native assembly for two architectures.

---

## Table of Contents

1. [Where We Left Off — Optimized IR](#where-we-left-off--optimized-ir)
2. [Stage 6 — IR Interpreter (Verification)](#stage-6--ir-interpreter-verification)
3. [Stage 7 — X86-64 Code Generation](#stage-7--x86-64-code-generation)
4. [Stage 8 — RISC-V 64-bit Code Generation](#stage-8--risc-v-64-bit-code-generation)
5. [X86-64 vs RISC-V Side-by-Side](#x86-64-vs-risc-v-side-by-side)
6. [Requirements](#requirements)
7. [Running the Compiler](#running-the-compiler)
8. [Building & Running X86-64 Output](#building--running-x86-64-output)
9. [Building & Running RISC-V Output](#building--running-risc-v-output)
10. [Full Example — What You Should See](#full-example--what-you-should-see)

---

## Where We Left Off — Optimized IR

After all six optimization passes run, the IR is stripped down to only what is
essential for execution. For example, the `complex_test.tri` program goes from
**50+ IR instructions** down to just **7**:

```
FUNC_START helper
LOAD_PARAM a_0 0
LOAD_PARAM b_1 1
GT t0 a_0 b_1
JMP_IF_FALSE t0 L0
RETURN a_0
LABEL L0
RETURN b_1
FUNC_END helper

FUNC_START main
PRINT 316          ← entire expression folded to a constant at compile time
PARAM 5
PARAM 3
CALL t14 helper 2
PRINT t14          ← result of helper(5, 3)
PRINT 128          ← x*y folded to 128
PRINT 128
FUNC_END main
```

This optimized IR is what both code generators receive as input.

---

## Stage 6 — IR Interpreter (Verification)

Before emitting any assembly, the compiler **executes the IR directly** in Python.
This is a safety net — if the interpreter output matches the expected values,
the optimized IR is correct and safe to lower to assembly.

```
[6] Execution:
316
5
128
128

  ✅ Execution Complete
```

If this stage fails, there is a bug in the IR or optimizer — **not** in the
code generators. This separation makes debugging much easier.

---

## Stage 7 — X86-64 Code Generation

**File:** `src/backend/codegen.py`
**Class:** `X86Generator`
**Output:** `output.asm` (NASM syntax, ELF64 format)

### Strategy

The backend uses a **pure stack machine** approach. Every variable — whether a
user variable like `x_2` or a compiler temporary like `t14` — lives in a fixed
slot on the stack at `[rbp - N]`. There is no register allocation.

This keeps the code generator simple and correct at the cost of some performance,
which is acceptable for a compiler of this scope.

### Stack Frame Layout

```
High address
┌──────────────────────┐
│  caller's stack      │
│  arg1 at [rbp + 24]  │  ← second argument passed by caller
│  arg0 at [rbp + 16]  │  ← first argument passed by caller
│  return address      │  ← pushed by `call` instruction
├──────────────────────┤  ← rbp  (frame pointer, set by `push rbp / mov rbp, rsp`)
│  local var 1         │  ← [rbp -  8]
│  local var 2         │  ← [rbp - 16]
│  local var 3         │  ← [rbp - 24]
│  ...                 │
└──────────────────────┤  ← rsp  (stack pointer, lowered by `sub rsp, N`)
Low address
```

### Function Prologue & Epilogue

Every function begins with:
```nasm
push rbp            ; save caller's frame pointer
mov  rbp, rsp       ; set our frame pointer to current stack top
sub  rsp, N         ; reserve N bytes for local variables
```

And ends with:
```nasm
.exit_funcname:
    mov  rsp, rbp   ; discard all locals by restoring stack pointer
    pop  rbp        ; restore caller's frame pointer
    ret             ; return to caller (pops return address into rip)
```

### Calling Convention

Arguments are pushed **right-to-left** before a `call`:
```nasm
; call helper(5, 3)
mov rax, 3          ; load second argument (rightmost first)
push rax            ; push it onto the stack
mov rax, 5          ; load first argument
push rax            ; push it
call helper         ; push return address, jump to helper
add rsp, 16         ; clean up 2 args × 8 bytes = 16 bytes after return
mov [rbp - 8], rax  ; store return value (rax) into result slot
```

Inside the callee, parameters are loaded from above the frame pointer:
```nasm
mov rax, [rbp + 16]  ; first arg  (a)
mov rax, [rbp + 24]  ; second arg (b)
```

### Printf Alignment Fix

The System V ABI requires `rsp` to be **16-byte aligned** before any `call`.
A naïve `and rsp, -16` would silently corrupt `[rbp - N]` addressing.
The fix saves and restores `rsp` around every `printf` call:

```nasm
mov rsi, rax            ; argument: the integer value to print
lea rdi, [rel fmt_int]  ; argument: pointer to "%ld\n" format string (RIP-relative)
xor rax, rax            ; rax = 0 (required by printf ABI: no vector registers used)
mov rbx, rsp            ; save current rsp before alignment
and rsp, -16            ; align rsp down to nearest 16-byte boundary
call printf             ; call C printf
mov rsp, rbx            ; restore rsp exactly — [rbp-N] offsets remain valid
```

### Complete Annotated Output (complex_test.tri)

```nasm
section .data
    fmt_int db "%ld", 10, 0     ; format string: "%ld\n" + null terminator

section .text
    extern printf               ; declare printf from C standard library
    extern scanf                ; declare scanf (used by readInt())

; ── helper function ─────────────────────────────────────────────────────────

global helper                   ; make symbol visible to linker
helper:
    push rbp                    ; save caller's rbp
    mov  rbp, rsp               ; establish our frame pointer
    sub  rsp, 32                ; reserve 32 bytes: a(8) + b(8) + t0(8) + pad(8)

    ; LOAD_PARAM a_0  (index 0 → [rbp + 16])
    mov rax, [rbp + 16]         ; load first argument from caller's stack
    mov [rbp - 8], rax          ; store into local slot for a_0

    ; LOAD_PARAM b_1  (index 1 → [rbp + 24])
    mov rax, [rbp + 24]         ; load second argument
    mov [rbp - 16], rax         ; store into local slot for b_1

    ; GT t0  a_0  b_1   (t0 = a > b)
    mov rax, [rbp - 8]          ; load a_0
    cmp rax, [rbp - 16]         ; compare a with b
    setg al                     ; al = 1 if a > b, else 0
    movzx rax, al               ; zero-extend al → rax
    mov [rbp - 24], rax         ; store result into t0

    ; JMP_IF_FALSE t0  L0
    mov rax, [rbp - 24]         ; load condition (t0)
    cmp rax, 0                  ; is it false (zero)?
    je  L0                      ; if false, jump to L0 (return b)

    ; RETURN a_0
    mov rax, [rbp - 8]          ; load a into rax (return value register)
    mov rsp, rbp                ; tear down frame
    pop rbp
    ret                         ; return to caller

L0:
    ; RETURN b_1
    mov rax, [rbp - 16]         ; load b into rax
    mov rsp, rbp
    pop rbp
    ret

.exit_helper:                   ; fallthrough epilogue (unreachable here, but emitted for safety)
    mov rsp, rbp
    pop rbp
    ret

; ── main function ────────────────────────────────────────────────────────────

global main
main:
    push rbp
    mov  rbp, rsp
    sub  rsp, 16                ; reserve 16 bytes for t14 (call result)

    ; PRINT 316  (constant folded by optimizer)
    mov rax, 316                ; load immediate constant
    mov rsi, rax                ; printf arg2: the integer value
    lea rdi, [rel fmt_int]      ; printf arg1: format string pointer (RIP-relative)
    xor rax, rax                ; rax=0: no floating-point args
    mov rbx, rsp                ; save rsp before alignment
    and rsp, -16                ; align to 16-byte boundary
    call printf
    mov rsp, rbx                ; restore rsp

    ; PARAM 5 / PARAM 3 / CALL t14 helper 2
    mov rax, 3                  ; push second argument (3) first (right-to-left)
    push rax
    mov rax, 5                  ; push first argument (5)
    push rax
    call helper                 ; call helper(5, 3)
    add rsp, 16                 ; clean up 2 × 8 = 16 bytes of arguments
    mov [rbp - 8], rax          ; store return value into t14

    ; PRINT t14
    mov rax, [rbp - 8]          ; load t14 (= 5, since helper(5,3) returns 5)
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx

    ; PRINT 128  (x*y = 16*8 = 128, folded at compile time)
    mov rax, 128
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx

    ; PRINT 128
    mov rax, 128
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx

.exit_main:
    mov rsp, rbp
    pop rbp
    ret
```

---

## Stage 8 — RISC-V 64-bit Code Generation

**File:** `src/backend/codegen_riscv.py`
**Class:** `RISCVGenerator`
**Output:** `output_riscv.s` (GNU Assembler syntax)
**Architecture:** RV64GC (RISC-V 64-bit, General + Compressed extensions)

### What is RV64GC?

| Component | Meaning |
|-----------|---------|
| **RV64** | 64-bit base integer instruction set. All registers are 64-bit. |
| **G** | General-purpose shorthand for IMAFD (Integer, Multiply, Atomic, Float, Double) |
| **C** | Compressed instructions — 16-bit encodings for common operations (reduces code size) |

This is the standard ISA used by:
- **SiFive HiFive** development boards
- **StarFive VisionFive** single-board computers
- **QEMU** `virt` machine target
- Most Linux RISC-V distributions

### Key Registers Used

| Register | ABI Name | Role in this compiler |
|----------|----------|-----------------------|
| `x2` | `sp` | Stack pointer |
| `x8` | `s0` / `fp` | Frame pointer (our base for all locals) |
| `x1` | `ra` | Return address (saved/restored in prologue/epilogue) |
| `x5` | `t0` | Primary scratch — used like `rax` in x86 |
| `x6` | `t1` | Secondary scratch — used like `rbx` in x86 |
| `x7` | `t2` | Tertiary scratch — address holding for ASTORE |
| `x10` | `a0` | First argument / return value (for printf and function returns) |
| `x11` | `a1` | Second argument to printf (the integer value) |

### Stack Frame Layout

```
High address
┌──────────────────────────┐
│  caller's stack          │
│  arg1 at  24(s0)         │  ← second argument passed by caller
│  arg0 at  16(s0)         │  ← first argument passed by caller
├──────────────────────────┤
│  saved ra at  8(s0)      │  ← return address saved in prologue
│  saved s0 at  0(s0)      │  ← caller's frame pointer saved here
├──────────────────────────┤  ← s0  (frame pointer)
│  local var 1  -8(s0)     │
│  local var 2  -16(s0)    │
│  local var 3  -24(s0)    │
│  ...                     │
└──────────────────────────┤  ← sp
Low address
```

### Function Prologue & Epilogue

```asm
funcname:
    addi sp, sp, -N         ; grow stack by N bytes (locals + 16 for ra/s0)
    sd   ra, (N-8)(sp)      ; save return address
    sd   s0, (N-16)(sp)     ; save caller's frame pointer
    addi s0, sp, (N-16)     ; set s0 = our frame pointer

.exit_funcname:
    ld   ra, (N-8)(sp)      ; restore return address
    ld   s0, (N-16)(sp)     ; restore frame pointer
    addi sp, sp, N          ; shrink stack back
    ret                     ; return (pseudoinstruction for jalr x0, ra, 0)
```

### How Comparisons Work (no flags register)

Unlike x86, RISC-V has **no flags register**. Every comparison produces
an integer result (0 or 1) in a register using dedicated instructions:

```
# a > b
slt  t0, t0(b), t1(a)     ; t0 = 1 if b < a  (i.e. a > b)

# a == b
sub  t0, t1(a), t0(b)     ; t0 = a - b
seqz t0, t0               ; t0 = 1 if t0 == 0  (i.e. a == b)

# a != b
sub  t0, t1(a), t0(b)
snez t0, t0               ; t0 = 1 if t0 != 0

# a <= b  (not a single instruction — derived)
slt  t0, t0(b), t1(a)     ; t0 = (b < a)
xori t0, t0, 1            ; t0 = NOT (b < a) = (a <= b)

# a >= b
slt  t0, t1(a), t0(b)     ; t0 = (a < b)
xori t0, t0, 1            ; t0 = NOT (a < b) = (a >= b)
```

### Complete Annotated Output (complex_test.tri)

```asm
.section .data
fmt_int: .string "%ld\n"        ; format string for printf

.section .text

# ── helper function ──────────────────────────────────────────────────────────

.globl helper
helper:
    addi sp, sp, -48            ; grow stack: 32 bytes locals + 16 for ra/s0
    sd   ra, 40(sp)             ; save return address
    sd   s0, 32(sp)             ; save caller's frame pointer
    addi s0, sp, 32             ; s0 = frame pointer

    # LOAD_PARAM a_0  (index 0 → 16(s0))
    ld   t0, 16(s0)             ; load first argument from caller's stack
    sd   t0, -8(s0)             ; store into local slot for a_0

    # LOAD_PARAM b_1  (index 1 → 24(s0))
    ld   t0, 24(s0)             ; load second argument
    sd   t0, -16(s0)            ; store into local slot for b_1

    # GT t0  a_0  b_1   (t0 = a > b)
    ld   t0, -8(s0)             ; load a_0 into t0
    mv   t1, t0                 ; copy a into t1
    ld   t0, -16(s0)            ; load b_1 into t0
    slt  t0, t0, t1             ; t0 = 1 if b < a  (equivalent to a > b)
    sd   t0, -24(s0)            ; store result into t0's slot

    # JMP_IF_FALSE t0  L0
    ld   t0, -24(s0)            ; load condition
    beqz t0, L0                 ; branch to L0 if condition is zero (false)

    # RETURN a_0
    ld   t0, -8(s0)             ; load a_0
    mv   a0, t0                 ; move return value into a0
    j    .exit_helper           ; jump to epilogue

L0:
    # RETURN b_1
    ld   t0, -16(s0)            ; load b_1
    mv   a0, t0                 ; move return value into a0
    j    .exit_helper

.exit_helper:
    ld   ra, 40(sp)             ; restore return address
    ld   s0, 32(sp)             ; restore frame pointer
    addi sp, sp, 48             ; shrink stack
    ret                         ; return to caller

# ── main function ─────────────────────────────────────────────────────────────

.globl main
main:
    addi sp, sp, -32            ; 16 bytes locals + 16 for ra/s0
    sd   ra, 24(sp)
    sd   s0, 16(sp)
    addi s0, sp, 16

    # PRINT 316
    li   t0, 316                ; load constant 316
    mv   a1, t0                 ; printf second arg: the integer value
    la   a0, fmt_int            ; printf first arg: format string address
    call printf

    # PARAM 5 / PARAM 3 / CALL t14 helper 2
    li   t0, 3                  ; second argument (rightmost pushed first)
    addi sp, sp, -8             ; grow stack for one argument
    sd   t0, 0(sp)              ; push 3

    li   t0, 5                  ; first argument
    addi sp, sp, -8
    sd   t0, 0(sp)              ; push 5

    call helper                 ; call helper — args at 0(sp) and 8(sp)
    addi sp, sp, 16             ; clean up 2 × 8 = 16 bytes
    mv   t0, a0                 ; move return value from a0 into t0
    sd   t0, -8(s0)             ; store into t14's stack slot

    # PRINT t14
    ld   t0, -8(s0)             ; load t14 (= 5)
    mv   a1, t0
    la   a0, fmt_int
    call printf

    # PRINT 128
    li   t0, 128
    mv   a1, t0
    la   a0, fmt_int
    call printf

    # PRINT 128
    li   t0, 128
    mv   a1, t0
    la   a0, fmt_int
    call printf

.exit_main:
    ld   ra, 24(sp)
    ld   s0, 16(sp)
    addi sp, sp, 32
    ret
```

---

## X86-64 vs RISC-V Side-by-Side

| Operation | X86-64 (NASM) | RISC-V 64 (GNU AS) |
|-----------|--------------|---------------------|
| Load constant | `mov rax, 42` | `li t0, 42` |
| Load from stack | `mov rax, [rbp - 8]` | `ld t0, -8(s0)` |
| Store to stack | `mov [rbp - 8], rax` | `sd t0, -8(s0)` |
| Add | `add rax, rbx` | `add t0, t1, t0` |
| Multiply | `imul rax, rbx` | `mul t0, t1, t0` |
| Left shift (imm) | `shl rax, 2` | `slli t0, t0, 2` |
| Right shift (imm) | `sar rax, 1` | `srai t0, t0, 1` |
| Compare a > b | `cmp rax, rbx` + `setg al` | `slt t0, t0(b), t1(a)` |
| Compare a == b | `cmp` + `sete al` | `sub` + `seqz` |
| Branch if false | `cmp rax, 0` + `je label` | `beqz t0, label` |
| Unconditional jump | `jmp label` | `j label` |
| Call function | `call func` | `call func` |
| Return value | `rax` | `a0` |
| Frame pointer | `rbp` | `s0` |
| Push to stack | `push rax` | `addi sp,sp,-8` + `sd t0,0(sp)` |
| Pop from stack | `pop rax` | `ld t0,0(sp)` + `addi sp,sp,8` |
| Return | `ret` | `ret` |

---

## Requirements

### For X86-64

| Tool | Purpose | Install |
|------|---------|---------|
| `nasm` | Assembles `.asm` → `.o` object file | `sudo apt install nasm` |
| `gcc` | Links `.o` + libc → executable | `sudo apt install gcc` |

### For RISC-V

| Tool | Purpose | Install |
|------|---------|---------|
| `gcc-riscv64-linux-gnu` | Cross-compiler: assembles + links RISC-V `.s` on x86 host | `sudo apt install gcc-riscv64-linux-gnu` |
| `qemu-user-static` | Emulates RISC-V CPU to run the binary on your x86 machine | `sudo apt install qemu-user-static` |

### Python

| Requirement | Version |
|-------------|---------|
| Python | 3.8 or higher |
| External packages | None — standard library only |

---

## Running the Compiler

```bash
# Navigate to the project root (inside WSL or on Linux)
cd /mnt/d/GitHub/Custom-Native-Compiler   # WSL path to Windows drive
# or
cd ~/Custom-Native-Compiler               # native Linux path

# Run both code generators (default)
python3 src/main.py tests/complex_test.tri

# Run x86-64 code generation only
python3 src/main.py tests/complex_test.tri --arch x86

# Run RISC-V code generation only
python3 src/main.py tests/complex_test.tri --arch riscv

# Run both explicitly
python3 src/main.py tests/complex_test.tri --arch both

# Interactive mode (type code directly)
python3 src/main.py --demo
```

After running, two output files appear in the project root:
- `output.asm` — x86-64 NASM assembly
- `output_riscv.s` — RISC-V GNU AS assembly

---

## Building & Running X86-64 Output

### On WSL (Ubuntu on Windows)

```bash
# Step 1 — Install tools (one time only)
sudo apt-get update
# Refreshes the package index from Ubuntu servers — do this before any install.

sudo apt install nasm gcc -y
# nasm : NASM assembler for x86-64
# gcc  : GNU C compiler used here as linker to attach the C runtime (printf etc.)
# -y   : auto-accept the install prompt

# Step 2 — Assemble the .asm file into an ELF64 object file
nasm -f elf64 output.asm -o output.o
# -f elf64  : output format is 64-bit ELF (the standard Linux object format)
# output.asm: our generated assembly source
# -o output.o : name of the object file to produce

# Step 3 — Link the object file into an executable
gcc output.o -o program -no-pie
# output.o   : the object file from nasm
# -o program : name of the final executable (avoid naming it "output" — 
#              there may already be a folder with that name in the project)
# -no-pie    : disable Position Independent Executable — our assembly uses
#              absolute addressing which is incompatible with PIE

# Step 4 — Run
./program
# Expected output:
# 316
# 5
# 128
# 128
```

### On Native Linux (Ubuntu / Debian)

Identical commands — no differences. WSL and native Ubuntu use the same
package manager and tool names.

---

## Building & Running RISC-V Output

### On WSL or Ubuntu (cross-compilation path)

This is the recommended approach. You compile on your x86 machine but
produce a RISC-V binary, then run it under QEMU CPU emulation.

```bash
# Step 1 — Install tools (one time only)
sudo apt-get update
# Refresh package list — required before installing any new packages.

sudo apt install gcc-riscv64-linux-gnu -y
# gcc-riscv64-linux-gnu : The RISC-V cross-compiler toolchain.
#   Includes:
#     riscv64-linux-gnu-as      (assembler)
#     riscv64-linux-gnu-ld      (linker)
#     riscv64-linux-gnu-gcc     (full compiler + linker frontend)
#   "Cross-compiler" means: runs on x86, produces RISC-V machine code.

sudo apt-get update --fix-missing
# Sometimes package mirrors are temporarily inconsistent.
# --fix-missing retries failed downloads and skips broken entries.

sudo apt install qemu-user-static -y
# qemu-user-static : QEMU in user-mode emulation.
#   Runs a single RISC-V ELF binary on an x86 machine by translating
#   RISC-V instructions to x86 on the fly.
#   "Static" version has no external dependencies — more reliable in WSL.

# Step 2 — Assemble + link in one command
riscv64-linux-gnu-gcc output_riscv.s -o program_riscv -static
# riscv64-linux-gnu-gcc : the cross-compiler frontend
# output_riscv.s        : our generated RISC-V assembly source
# -o program_riscv      : name of the output binary
# -static               : statically link libc into the binary.
#                         Required for qemu-user — the emulator cannot
#                         load dynamic libraries from a different architecture.

# Step 3 — Run under QEMU
qemu-riscv64-static ./program_riscv
# qemu-riscv64-static : emulates a RISC-V 64-bit CPU
# ./program_riscv     : the statically linked RISC-V binary to execute
#
# Expected output:
# 316
# 5
# 128
# 128
```

### On a Native RISC-V Board or VM

If you have a RISC-V device (e.g. StarFive VisionFive 2, SiFive Unmatched,
or a RISC-V QEMU full-system VM):

```bash
# No cross-compiler needed — use the native gcc
gcc output_riscv.s -o program_riscv
# gcc on a RISC-V machine already targets RISC-V natively.
# No -static needed since libc is available natively.

./program_riscv
# Run directly — no emulator needed.
```

---

## Full Example — What You Should See

Running the full pipeline on `complex_test.tri`:

```
==================================
           PROGRAM OUTPUT
==================================

316
5
128
128

==================================
         COMPILATION DETAILS
==================================

[1] Tokens:        ... (token table)
[2] AST:           ... (tree printout)
[3] Semantic:      ✅ Passed
[4] IR:            ... (raw three-address code)
[5] Optimization:  ... (6 pass results)
                   ✅ Optimization Complete
[6] Execution:     316 / 5 / 128 / 128
                   ✅ Execution Complete
[7] X86-64:        ... (NASM assembly)
                   ✅ Assembly written to 'output.asm'
[8] RISC-V:        ... (GNU AS assembly)
                   ✅ Assembly written to 'output_riscv.s'
```

Both `output.asm` and `output_riscv.s` produce identical output when
assembled and executed:
```
316
5
128
128
```
