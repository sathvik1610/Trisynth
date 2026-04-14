# Trisynth Compiler — Team Guide
### Backend, Code Generation & How to Run

---

# python src/main.py tests/complex_test.tri --arch x86    # x86 only
# python src/main.py tests/complex_test.tri --arch riscv  # RISC-V only
# python src/main.py tests/complex_test.tri --arch both   # both (default)

## What Happens After Optimization

The optimizer outputs a **clean, minimal IR** (Three-Address Code).
This IR is the single input to all downstream stages.

```
Optimized IR
     │
     ├──▶ [6] IR Interpreter   → Executes IR in Python to verify correctness
     │
     ├──▶ [7] X86-64 Codegen   → output.asm       (run on Linux/WSL x86 machine)
     │
     └──▶ [8] RISC-V Codegen   → output_riscv.s   (run on RISC-V board or via QEMU)
```

The IR interpreter runs **before** code generation purely as a sanity check.
If output is wrong there, the bug is in IR/optimizer — not in the backends.
If IR is correct but assembly output is wrong, the bug is in the codegen.

---

## How the IR Connects to Code Generation

Each IR instruction maps **directly** to one or more assembly instructions.
Both backends share the same `StackFrame` allocator (`src/backend/common/stack_frame.py`)
which assigns every variable a fixed byte offset on the stack.

The flow inside each backend:

```
1. Scan all IR instructions for the function
        ↓
2. StackFrame allocator assigns [rbp - N] / -(N)(s0) offsets to every variable
        ↓
3. Emit function prologue  (save frame pointer, reserve stack space)
        ↓
4. Walk IR instruction by instruction → emit assembly for each opcode
        ↓
5. Emit function epilogue  (restore frame pointer, return)
```

No register allocation — every variable lives on the stack.
Temporaries (`t0`, `t1`, ...) are stack-allocated, not kept in registers.

---

## X86-64 Backend

**File:** `src/backend/codegen.py` — class `X86Generator`
**Output:** `output.asm` (NASM syntax, ELF64)
**Assembler:** NASM + `gcc` linker

### Registers Used

| Register | Role |
|----------|------|
| `rbp` | Frame pointer — base for all `[rbp - N]` locals |
| `rsp` | Stack pointer |
| `rax` | Primary scratch — every load/store goes through here |
| `rbx` | Saved `rsp` before `printf` alignment |
| `rcx` | Divisor for `idiv` / shift count `cl` for `shl/sar` |
| `rdx` | Remainder output of `idiv` (used by MOD) |
| `r9` | Temp value register for ASTORE (avoids push/pop clobber) |
| `rdi`, `rsi` | `printf` arguments — format pointer and integer value |

### Stack Frame

```
[rbp + 24]  arg1 from caller
[rbp + 16]  arg0 from caller
[rbp +  0]  saved rbp  ← rbp points here
[rbp -  8]  local var 1
[rbp - 16]  local var 2  ...
```

### Key Design Decisions

- **`lea rdi, [rel fmt_int]`** — RIP-relative addressing required in 64-bit.
  Absolute `[fmt_int]` crashes with ASLR/PIE.
- **RSP save/restore around printf:**
  System V ABI requires 16-byte RSP alignment before any `call`.
  Plain `and rsp, -16` would corrupt `[rbp-N]` offsets permanently,
  so RSP is saved in `rbx`, aligned, call made, then restored.
- **Args pushed right-to-left** before `call`, cleaned with `add rsp, N` after.
- **Return value in `rax`**, stored to result slot immediately after `call`.
- **`"%ld"` format string** — required for 64-bit integers. `"%d"` truncates silently.

---

## RISC-V Backend

**File:** `src/backend/codegen_riscv.py` — class `RISCVGenerator`
**Output:** `output_riscv.s` (GNU AS syntax)
**ISA:** RV64GC (64-bit base + Multiply + Float + Compressed extensions)
**Assembler:** `riscv64-linux-gnu-gcc` (cross-compiler, runs on x86)
**Emulator:** `qemu-riscv64-static` (runs RISC-V binary on x86 host)

### Registers Used

| Register | ABI Name | Role |
|----------|----------|------|
| `x2` | `sp` | Stack pointer |
| `x8` | `s0` | Frame pointer — base for all `-(N)(s0)` locals |
| `x1` | `ra` | Return address — saved/restored in prologue/epilogue |
| `x5` | `t0` | Primary scratch (equivalent to `rax`) |
| `x6` | `t1` | Secondary scratch |
| `x7` | `t2` | Address register for ASTORE |
| `x10` | `a0` | Return value / printf format string arg |
| `x11` | `a1` | printf integer value arg |

### Stack Frame

```
s0 + 24   arg1 from caller
s0 + 16   arg0 from caller
s0 +  8   saved ra
s0 +  0   saved s0  ← s0 points here
s0 -  8   local var 1
s0 - 16   local var 2  ...
```

### Key Design Decisions

- **No flags register** — comparisons produce integer 0 or 1 directly:
  - `slt t0, a, b` → t0 = (a < b)
  - GT: swap operands of `slt`
  - EQ: `sub` then `seqz`
  - NEQ: `sub` then `snez`
  - LTE / GTE: `slt` then `xori t0, t0, 1` to invert
- **Branch:** `beqz t0, label` replaces x86's `cmp + je`.
- **Jump:** `j label` (pseudoinstruction for `jal x0, label`).
- **`ret`** is a pseudoinstruction for `jalr x0, ra, 0`.
- **Args pushed right-to-left** via `addi sp,sp,-8` + `sd t0,0(sp)`,
  cleaned with `addi sp,sp,N` after call.
- **Return value in `a0`**, moved to `t0` then stored to result slot.
- **`-static` flag required** when linking — QEMU user-mode cannot load
  shared libraries from a different architecture.

---

## First-Time Setup

### WSL (Windows) & Ubuntu (Native Linux)
Commands are identical on both — same package manager, same tool names.

```bash
# Refresh package index — always do this first before installing anything
sudo apt-get update

# x86-64 tools
sudo apt install nasm gcc -y
# nasm : assembles .asm → ELF64 object file
# gcc  : links object file + libc → executable

# RISC-V cross-compiler (runs on x86, produces RISC-V binaries)
sudo apt install gcc-riscv64-linux-gnu -y

# RISC-V emulator (run RISC-V binaries on your x86 machine)
sudo apt-get update --fix-missing   # fixes stale/broken mirror entries
sudo apt install qemu-user-static -y
```

---

## Running the Compiler

```bash
# WSL — navigate to project root
cd /mnt/d/GitHub/Custom-Native-Compiler

# Native Linux
cd ~/Custom-Native-Compiler

# Generate both x86 and RISC-V output (default)
python3 src/main.py tests/complex_test.tri

# x86-64 only
python3 src/main.py tests/complex_test.tri --arch x86

# RISC-V only
python3 src/main.py tests/complex_test.tri --arch riscv
```

This produces `output.asm` and `output_riscv.s` in the project root.

---

## Building & Running the Output

### X86-64 — WSL or Ubuntu

```bash
# Assemble .asm → object file
nasm -f elf64 output.asm -o output.o
# -f elf64 : 64-bit ELF object format (standard Linux format)

# Link object file + libc → executable
gcc output.o -o program -no-pie
# -no-pie : disable Position Independent Executable
#           our assembly uses non-PIE addressing — required flag

# Run
./program
```

### RISC-V — WSL or Ubuntu (cross-compile + emulate)

```bash
# Assemble + link in one step using the cross-compiler
riscv64-linux-gnu-gcc output_riscv.s -o program_riscv -static
# -static : embed libc into the binary
#           required because QEMU user-mode cannot load
#           dynamic libraries from a different architecture

# Run under RISC-V CPU emulator
qemu-riscv64-static ./program_riscv
```

### RISC-V — Native RISC-V Board or VM

```bash
# No cross-compiler, no emulator needed
gcc output_riscv.s -o program_riscv
./program_riscv
```

---

## Files Added / Modified

| File | Status | What changed |
|------|--------|-------------|
| `src/backend/codegen.py` | Modified | Fixed duplicate methods, None guard, LSHIFT typo, `%ld` format, RIP-relative `lea`, RSP save/restore around `printf` |
| `src/backend/codegen_riscv.py` | **New** | Full RISC-V 64-bit backend |
| `src/ir/ir_gen.py` | Modified | `FUNC_END` now always emitted unconditionally (was skipped when last instruction was `RETURN`, causing entire functions to vanish) |
| `src/optimization/dead_code.py` | Modified | `FUNC_START`, `FUNC_END`, `LABEL` are forced reachable and never stripped by DCE |
| `src/main.py` | Modified | Added `--arch` flag, Stage 8 RISC-V codegen, updated function signatures |
