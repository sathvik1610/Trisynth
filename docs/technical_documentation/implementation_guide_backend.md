# Trisynth Compiler — Backend & Code Generation

> **This document is a continuation of the main README.**
> It covers everything that happens **after the optimization passes** —
> from IR to native assembly for two architectures.

```bash
python src/main.py tests/programs/test01_fibonacci.tri                # x86-64 (default: --arch x86)
python src/main.py tests/programs/test01_fibonacci.tri --arch riscv   # RISC-V only
python src/main.py tests/programs/test01_fibonacci.tri --arch both    # both
```

---

## Table of Contents

1. [Where We Left Off — Optimized IR](#where-we-left-off--optimized-ir)
2. [Stage 6 — (no longer a pipeline stage)](#stage-6--no-longer-a-pipeline-stage)
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

All listings in this guide were regenerated from the following small program
(`demo.tri`):

```c
int helper(int a, int b) {
    if (a > b) { return a; }
    return b;
}

void main() {
    int x = 16;
    int y = 8;
    print(helper(5, 3));
    print(x * y);
}
```

After the six optimization passes (Strength Reduction, Common Subexpression
Elimination, Copy Propagation, Constant Folding, a second CSE cleanup, Dead
Code Elimination — each run once, in that order, see `src/main.py`), the IR
for this program shrinks from **20 instructions** (counting `FUNC_START` /
`FUNC_END`) to **15**:

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
PARAM 5
PARAM 3
CALL t1 helper 2
PRINT t1             ← result of helper(5, 3)
PRINT 128            ← x*y folded to 128 at compile time
FUNC_END main
```

This optimized IR is what both code generators receive as input.

---

## Stage 6 — (no longer a pipeline stage)

The compiler does **not** interpret the IR during a normal run. `IRInterpreter`
(`src/main.py`) is defined there but is only used as a helper by
`tests/unit/test_string_literals.py`. The `-v` output therefore numbers its
stages `[1] Tokens`, `[2] AST`, `[3] Semantic`, `[4] IR`, `[5] Optimization`,
`[7] X86-64` and `[8] RISC-V` — there is no `[6]`.

---

## Stage 7 — X86-64 Code Generation

**File:** `src/backend/codegen_x86.py`
**Class:** `X86Generator`
**Output:** `output.asm` (NASM syntax; assembled as ELF64 on Linux/WSL with `-f elf64`, and as `-f win64` in the native-Windows mode)

### Strategy

The backend is a **spill-everything, stack-slot** code generator. Every IR name —
a user variable like `x_2` or a compiler temporary like `t1` — gets a fixed slot in
the stack frame at `[rbp - N]`. Each IR instruction loads its operands into scratch
registers (`rax`, `rbx`, `rcx`, `rdx`), computes, and stores the result back to its
slot. There is no register allocation and no operand stack.

This keeps the code generator simple and correct at the cost of some performance,
which is acceptable for a compiler of this scope.

### Stack Frame Layout

```
High address
┌──────────────────────┐
│  caller's stack      │
│  arg1 at [rbp + 24]  │  ← second argument passed by caller
│  arg0 at [rbp + 16]  │  ← first argument passed by caller
│  return address      │  ← [rbp + 8], pushed by `call`
│  saved rbp           │  ← [rbp + 0], pushed by `push rbp`
├──────────────────────┤  ← rbp  (frame pointer, set by `mov rbp, rsp`)
│  local var 1         │  ← [rbp -  8]
│  local var 2         │  ← [rbp - 16]
│  local var 3         │  ← [rbp - 24]
│  ...                 │
└──────────────────────┤  ← rsp  (stack pointer, lowered by `sub rsp, N`)
Low address
```

Slot rules (`src/backend/common/stack_frame.py`):

- Every scalar, temporary, and `string` pointer takes one 8-byte slot.
- An array takes `size * 8` bytes; its base address is `[rbp - offset]` and element `i`
  lives at `base + i * 8`. Arrays are **not** zero-initialised.
- An array parameter (`int arr[]`) is an 8-byte slot holding the array's address
  (the caller passes the address); element accesses first load that pointer.
- The total frame size is rounded up to a multiple of 16.

### Function Prologue & Epilogue

Every function begins with:
```nasm
push rbp            ; save caller's frame pointer
mov  rbp, rsp       ; set our frame pointer to current stack top
sub  rsp, N         ; reserve N bytes for locals (only emitted when N > 0; N is a multiple of 16)
```

And ends with:
```nasm
.exit_funcname:
    mov  rsp, rbp   ; discard all locals by restoring stack pointer
    pop  rbp        ; restore caller's frame pointer
    ret             ; return to caller (pops return address into rip)
```

A `return` statement does not jump to `.exit_funcname`; it inlines the same
`mov rsp, rbp / pop rbp / ret` sequence. The trailing `.exit_funcname:` block is
the fall-through epilogue for functions that end without a `return`.

### Calling Convention

Arguments are pushed **right-to-left** on the stack before a `call`:
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

### Calling libc (`printf` / `scanf`)

The System V ABI requires `rsp` to be **16-byte aligned** before any `call`.
`rsp` is aligned immediately around each `printf` / `scanf` call and restored
right afterwards, so later pushes and argument clean-up stay consistent:

```nasm
mov rsi, rax            ; argument: the integer value to print
lea rdi, [rel fmt_int]  ; argument: pointer to "%ld\n" format string (RIP-relative)
xor rax, rax            ; rax = 0 (no vector registers used)
mov rbx, rsp            ; save current rsp before alignment
and rsp, -16            ; align rsp down to nearest 16-byte boundary
call printf             ; call C printf
mov rsp, rbx            ; restore rsp
```

Notes:

- The save register is `rbx`. It is callee-saved in the System V ABI, but generated
  functions do not save or restore it.
- Only libc calls are aligned this way; calls to user functions are not.
- `print` of a `string` uses the same sequence with `fmt_str` (`"%s"`, no newline).
- `readInt()` is a small routine emitted at the top of `.text` that calls `scanf`
  with `fmt_read_int` (`"%ld"`).

### Annotated Output (`demo.tri`)

Real output of `python src/main.py demo.tri --asm --arch x86`. Every IR instruction
is echoed as a `; comment` before its code.

```nasm
section .data
    fmt_int db "%ld", 10, 0
    fmt_str db "%s", 0
    fmt_read_int db "%ld", 0
    ; (string literals, if any, follow as: str_0 db `...`, 0)

section .text
    extern printf
    extern scanf

global readInt
readInt:
    push rbp
    mov rbp, rsp
    sub rsp, 16
    lea rsi, [rbp-8]
    lea rdi, [rel fmt_read_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call scanf
    mov rsp, rbx
    mov rax, [rbp-8]
    mov rsp, rbp
    pop rbp
    ret

; --- Function helper ---
global helper
helper:
    push rbp
    mov rbp, rsp
    sub rsp, 32                 ; a_0, b_1, t0 = 24 bytes, rounded up to 32
    ; LOAD_PARAM a_0 0
    mov rax, [rbp + 16]
    mov [rbp - 8], rax
    ; LOAD_PARAM b_1 1
    mov rax, [rbp + 24]
    mov [rbp - 16], rax
    ; GT t0 a_0 b_1
    mov rax, [rbp - 8]
    cmp rax, [rbp - 16]
    setg al
    movzx rax, al
    mov [rbp - 24], rax
    ; JMP_IF_FALSE t0 L0
    mov rax, [rbp - 24]
    cmp rax, 0
    je L0
    ; RETURN a_0
    mov rax, [rbp - 8]
    mov rsp, rbp
    pop rbp
    ret
    ; LABEL L0
L0:
    ; RETURN b_1
    mov rax, [rbp - 16]
    mov rsp, rbp
    pop rbp
    ret
.exit_helper:
    mov rsp, rbp
    pop rbp
    ret
; --- Function main ---
global main
main:
    push rbp
    mov rbp, rsp
    sub rsp, 16                 ; t1 = 8 bytes, rounded up to 16
    ; PARAM 5
    ; PARAM 3
    ; CALL t1 helper 2
    mov rax, 3
    push rax
    mov rax, 5
    push rax
    call helper
    add rsp, 16
    mov [rbp - 8], rax
    ; PRINT t1
    mov rax, [rbp - 8]
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

section .note.GNU-stack noalloc noexec nowrite progbits
```

(The `; (string literals ...)` line above is added here for explanation and is not
emitted by the compiler.)

---

## Stage 8 — RISC-V 64-bit Code Generation

**File:** `src/backend/riscv/codegen_riscv.py`
**Class:** `RISCVGenerator`
**Output:** `output_riscv.s` (GNU Assembler syntax)
**Architecture:** RV64. The generator uses only base integer instructions plus the
M extension (`mul`, `div`, `rem`) and the usual pseudo-instructions (`li`, `la`,
`call`, `j`, `ret`, `mv`). No `-march` is specified, so the toolchain default applies.

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
| `x11` | `a1` | Second argument to printf (the integer value); scanf buffer in `readInt` |

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

Slot rules are the same as on x86 (8-byte scalars, `size * 8` arrays, pointer slots
for array parameters), via the shared `StackFrame` class.

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

The locals area is rounded up to a multiple of 16 and is **at least 16 bytes** even for
a function with no locals; `N` is that size plus 16. `return` statements emit
`j .exit_funcname`. The RISC-V backend does not emit any stack-alignment code around
`printf` calls.

### How Comparisons Work (no flags register)

Unlike x86, RISC-V has **no flags register**. Every comparison produces
an integer result (0 or 1) in a register using dedicated instructions:

```
# a < b
slt  t0, t1(a), t0(b)     ; t0 = 1 if a < b

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

### Annotated Output (`demo.tri`)

Real output of `python src/main.py demo.tri --asm --arch riscv`. Each IR
instruction is echoed as a `# comment`.

```asm
.section .data
fmt_int: .string "%ld\n"
fmt_str: .string "%s"
fmt_read_int: .string "%ld"

.section .text
.globl readInt
readInt:
    addi sp, sp, -32
    sd   ra, 24(sp)
    sd   s0, 16(sp)
    addi s0, sp, 32
    la   a0, fmt_read_int
    addi a1, s0, -24
    call scanf
    ld   a0, -24(s0)
    ld   ra, 24(sp)
    ld   s0, 16(sp)
    addi sp, sp, 32
    ret

# --- Function helper ---
.globl helper
helper:
    addi sp, sp, -48            # 32 bytes locals + 16 for ra/s0
    sd   ra, 40(sp)
    sd   s0, 32(sp)
    addi s0, sp, 32
    # LOAD_PARAM a_0 0
    ld   t0, 16(s0)
    sd   t0, -8(s0)
    # LOAD_PARAM b_1 1
    ld   t0, 24(s0)
    sd   t0, -16(s0)
    # GT t0 a_0 b_1
    ld   t0, -8(s0)
    mv   t1, t0
    ld   t0, -16(s0)
    slt  t0, t0, t1
    sd   t0, -24(s0)
    # JMP_IF_FALSE t0 L0
    ld   t0, -24(s0)
    beqz t0, L0
    # RETURN a_0
    ld   t0, -8(s0)
    mv   a0, t0
    j    .exit_helper
    # LABEL L0
L0:
    # RETURN b_1
    ld   t0, -16(s0)
    mv   a0, t0
    j    .exit_helper
.exit_helper:
    ld   ra, 40(sp)
    ld   s0, 32(sp)
    addi sp, sp, 48
    ret
# --- Function main ---
.globl main
main:
    addi sp, sp, -32            # 16 bytes locals + 16 for ra/s0
    sd   ra, 24(sp)
    sd   s0, 16(sp)
    addi s0, sp, 16
    # PARAM 5
    # PARAM 3
    # CALL t1 helper 2
    li   t0, 3
    addi sp, sp, -8
    sd   t0, 0(sp)
    li   t0, 5
    addi sp, sp, -8
    sd   t0, 0(sp)
    call helper
    addi sp, sp, 16
    mv   t0, a0
    sd   t0, -8(s0)
    # PRINT t1
    ld   t0, -8(s0)
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

(The two `# ...` size remarks are explanatory additions, not compiler output.)

---

## X86-64 vs RISC-V Side-by-Side

| Operation | X86-64 (NASM) | RISC-V 64 (GNU AS) |
|-----------|--------------|---------------------|
| Load constant | `mov rax, 42` | `li t0, 42` |
| Load from stack | `mov rax, [rbp - 8]` | `ld t0, -8(s0)` |
| Store to stack | `mov [rbp - 8], rax` | `sd t0, -8(s0)` |
| Add | `mov rbx, rax` + `add rbx, [rbp - 16]` + `mov rax, rbx` | `add t0, t1, t0` |
| Multiply | `imul rax, [rbp - 16]` | `mul t0, t1, t0` |
| Divide | `cqo` + `idiv` | `div t0, t1, t0` |
| Modulo | `cqo` + `idiv` + `mov rax, rdx` | `rem t0, t1, t0` |
| Left shift (imm) | `shl rax, 2` | `slli t0, t0, 2` |
| Right shift (imm) | `sar rax, 1` | `srai t0, t0, 1` |
| Shift by variable | `shl/sar rax, cl` | `sll/sra t0, t1, t0` |
| Compare a > b | `cmp rax, [rbp - 16]` + `setg al` | `slt t0, t0(b), t1(a)` |
| Compare a == b | `cmp` + `sete al` | `sub` + `seqz` |
| Branch if false | `cmp rax, 0` + `je label` | `beqz t0, label` |
| Unconditional jump | `jmp label` | `j label` |
| Call function | `call func` | `call func` |
| Call clean-up | `add rsp, 8*n` | `addi sp, sp, 8*n` |
| Return value | `rax` | `a0` |
| Frame pointer | `rbp` | `s0` |
| Push argument | `push rax` | `addi sp,sp,-8` + `sd t0,0(sp)` |
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
| Python | 3 (the sources parse as Python 3.8-compatible; no minimum is enforced) |
| External packages | None for the compiler itself; `pytest` (see `requirements.txt`) only for the test suite |

---

## Running the Compiler

```bash
# Navigate to the project root (inside WSL or on Linux)
cd /mnt/d/GitHub/Trisynth     # WSL path to Windows drive
# or
cd ~/Trisynth                 # native Linux path

# Compile and run the x86-64 build (default is --arch x86)
python3 src/main.py tests/programs/test01_fibonacci.tri

# Run only the RISC-V build (needs riscv64-linux-gnu-gcc + qemu-riscv64)
python3 src/main.py tests/programs/test01_fibonacci.tri --arch riscv

# Run both builds
python3 src/main.py tests/programs/test01_fibonacci.tri --arch both

# Inspect individual stages without running
python3 src/main.py tests/programs/test01_fibonacci.tri --tokens
python3 src/main.py tests/programs/test01_fibonacci.tri --ast
python3 src/main.py tests/programs/test01_fibonacci.tri --ir
python3 src/main.py tests/programs/test01_fibonacci.tri --asm --arch x86
python3 src/main.py tests/programs/test01_fibonacci.tri --compare-asm
python3 src/main.py tests/programs/test01_fibonacci.tri -v          # everything

# Benchmark x86-64 vs RISC-V (QEMU)
python3 src/main.py tests/programs/test01_fibonacci.tri --benchmark

# Interactive mode (type code on stdin; finish with Ctrl+D / Ctrl+Z then Enter)
python3 src/main.py --demo
```

Both code generators always run, so after any run two output files appear in the
**current working directory**:
- `output.asm` — x86-64 NASM assembly
- `output_riscv.s` — RISC-V GNU AS assembly

`--arch` only chooses which one is printed (with `-v`/`--asm`) and which one is assembled and run.

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
# -o program : name of the final executable (the compiler itself also uses "program")
# -no-pie    : the generated code calls printf/scanf with a plain `call`, which
#              produces PC32 relocations that the linker rejects in a PIE
#              ("relocation R_X86_64_PC32 against symbol `scanf' can not be used
#              when making a PIE object"); -no-pie avoids that.

# Step 4 — Run
./program
# Expected output for tests/programs/test01_fibonacci.tri:
# 0
# 1
# 1
# 2
# 3
# 5
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
# (when you use --arch riscv, the compiler itself invokes `qemu-riscv64`)
#
# Expected output for tests/programs/test01_fibonacci.tri: 0 1 1 2 3 5, one per line.
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

Running `python src/main.py demo.tri -v` (default `--arch x86`) prints, in order:

1. the Trisynth banner and the `COMPILATION DETAILS` header;
2. `[1] Tokens` — the token table;
3. `[2] Abstract Syntax Tree (AST)`;
4. `[3] Semantic Analysis` — `Passed (No semantic errors)` plus the global symbol table;
5. `[4] Intermediate Representation (IR)`;
6. `[5] Optimization` — the initial IR, the IR after each of the six passes, then `Optimization Complete`;
7. `[7] X86-64 Code Generation (NASM)` — the assembly (`[8] RISC-V 64-bit Code Generation (GNU AS)` follows only with `--arch riscv` / `--arch both` or `--compare-asm`);
8. `PROGRAM OUTPUT`, then `[Toolchain: wsl]` (or `linux` / `windows_native`) and `[Invoking Native Assembler & Linker...]`, the program's stdout, and finally `Native Hardware Execution Complete` with the elapsed time.

The program's stdout for `demo.tri` is:

```
5
128
```

Without `-v`, only the program's stdout is printed. With `--arch both`, the program
is run natively on x86-64 and then under QEMU as RISC-V; both runs are expected to
print the same values (the RISC-V run could not be exercised when this guide was
checked, because no RISC-V cross-compiler was installed).
