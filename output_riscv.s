.section .data
fmt_int: .string "%ld\n"
fmt_str: .string "%s"

.section .text

# --- Function main ---
.globl main
main:
    addi sp, sp, -32
    sd   ra, 24(sp)
    sd   s0, 16(sp)
    addi s0, sp, 16
    # PRINT 205
    li   t0, 205
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PRINT 210
    li   t0, 210
    mv   a1, t0
    la   a0, fmt_int
    call printf
.exit_main:
    ld   ra, 24(sp)
    ld   s0, 16(sp)
    addi sp, sp, 32
    ret
