.section .data
fmt_int: .string "%ld\n"
fmt_str: .string "%s"
fmt_read_int: .string "%ld"
str_0: .string "--- TRISYNTH FINAL SHOWCASE ---"
str_1: .string "System is ready. Computing factorials block:"
str_2: .string "Factorial Results:"
str_3: .string "--- SHOWCASE COMPLETE ---"

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

# --- Function factorial ---
.globl factorial
factorial:
    addi sp, sp, -64
    sd   ra, 56(sp)
    sd   s0, 48(sp)
    addi s0, sp, 48
    # LOAD_PARAM n_0 0
    ld   t0, 16(s0)
    sd   t0, -8(s0)
    # LTE t0 n_0 1
    ld   t0, -8(s0)
    mv   t1, t0
    li   t0, 1
    slt  t0, t0, t1
    xori t0, t0, 1
    sd   t0, -16(s0)
    # JMP_IF_FALSE t0 L0
    ld   t0, -16(s0)
    beqz t0, L0
    # RETURN 1
    li   t0, 1
    mv   a0, t0
    j    .exit_factorial
    # LABEL L0
L0:
    # SUB t1 n_0 1
    ld   t0, -8(s0)
    mv   t1, t0
    li   t0, 1
    sub  t0, t1, t0
    sd   t0, -24(s0)
    # PARAM t1
    # CALL t2 factorial 1
    ld   t0, -24(s0)
    addi sp, sp, -8
    sd   t0, 0(sp)
    call factorial
    addi sp, sp, 8
    mv   t0, a0
    sd   t0, -32(s0)
    # MUL t3 n_0 t2
    ld   t0, -8(s0)
    mv   t1, t0
    ld   t0, -32(s0)
    mul  t0, t1, t0
    sd   t0, -40(s0)
    # RETURN t3
    ld   t0, -40(s0)
    mv   a0, t0
    j    .exit_factorial
.exit_factorial:
    ld   ra, 56(sp)
    ld   s0, 48(sp)
    addi sp, sp, 64
    ret
# --- Function main ---
.globl main
main:
    addi sp, sp, -160
    sd   ra, 152(sp)
    sd   s0, 144(sp)
    addi s0, sp, 144
    # LOAD_STR t4 --- TRISYNTH FINAL SHOWCASE ---
    la   t0, str_0
    sd   t0, -8(s0)
    # PRINT_STR t4
    ld   t0, -8(s0)
    mv   a1, t0
    la   a0, fmt_str
    call printf
    # LOAD_STR t5 System is ready. Computing factorials block:
    la   t0, str_1
    sd   t0, -16(s0)
    # PRINT_STR t5
    ld   t0, -16(s0)
    mv   a1, t0
    la   a0, fmt_str
    call printf
    # ARR_DECL values_4 5
    # MOV i_5 0
    li   t0, 0
    sd   t0, -64(s0)
    # LABEL L2
L2:
    # LT t6 i_5 5
    ld   t0, -64(s0)
    mv   t1, t0
    li   t0, 5
    slt  t0, t1, t0
    sd   t0, -72(s0)
    # JMP_IF_FALSE t6 L4
    ld   t0, -72(s0)
    beqz t0, L4
    # ADD t7 i_5 1
    ld   t0, -64(s0)
    mv   t1, t0
    li   t0, 1
    add  t0, t1, t0
    sd   t0, -80(s0)
    # PARAM t7
    # CALL t8 factorial 1
    ld   t0, -80(s0)
    addi sp, sp, -8
    sd   t0, 0(sp)
    call factorial
    addi sp, sp, 8
    mv   t0, a0
    sd   t0, -88(s0)
    # ASTORE t8 values_4 i_5
    ld   t0, -64(s0)
    slli t0, t0, 3
    addi t1, s0, -56
    add  t1, t1, t0
    mv   t2, t1
    ld   t0, -88(s0)
    sd   t0, 0(t2)
    # ADD t9 i_5 1
    ld   t0, -64(s0)
    mv   t1, t0
    li   t0, 1
    add  t0, t1, t0
    sd   t0, -96(s0)
    # MOV i_5 t9
    ld   t0, -96(s0)
    sd   t0, -64(s0)
    # JMP L2
    j    L2
    # LABEL L4
L4:
    # LOAD_STR t10 Factorial Results:
    la   t0, str_2
    sd   t0, -104(s0)
    # PRINT_STR t10
    ld   t0, -104(s0)
    mv   a1, t0
    la   a0, fmt_str
    call printf
    # MOV j_7 0
    li   t0, 0
    sd   t0, -112(s0)
    # LABEL L5
L5:
    # LT t11 j_7 5
    ld   t0, -112(s0)
    mv   t1, t0
    li   t0, 5
    slt  t0, t1, t0
    sd   t0, -120(s0)
    # JMP_IF_FALSE t11 L7
    ld   t0, -120(s0)
    beqz t0, L7
    # ALOAD t12 values_4 j_7
    ld   t0, -112(s0)
    slli t0, t0, 3
    addi t1, s0, -56
    add  t1, t1, t0
    ld   t0, 0(t1)
    sd   t0, -128(s0)
    # PRINT t12
    ld   t0, -128(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # ADD t13 j_7 1
    ld   t0, -112(s0)
    mv   t1, t0
    li   t0, 1
    add  t0, t1, t0
    sd   t0, -136(s0)
    # MOV j_7 t13
    ld   t0, -136(s0)
    sd   t0, -112(s0)
    # JMP L5
    j    L5
    # LABEL L7
L7:
    # LOAD_STR t14 --- SHOWCASE COMPLETE ---
    la   t0, str_3
    sd   t0, -144(s0)
    # PRINT_STR t14
    ld   t0, -144(s0)
    mv   a1, t0
    la   a0, fmt_str
    call printf
.exit_main:
    ld   ra, 152(sp)
    ld   s0, 144(sp)
    addi sp, sp, 160
    ret
