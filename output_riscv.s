.section .data
fmt_int: .string "%ld\n"

.section .text

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
# --- Function fibonacci ---
.globl fibonacci
fibonacci:
    addi sp, sp, -80
    sd   ra, 72(sp)
    sd   s0, 64(sp)
    addi s0, sp, 64
    # LOAD_PARAM n_1 0
    ld   t0, 16(s0)
    sd   t0, -8(s0)
    # LTE t4 n_1 0
    ld   t0, -8(s0)
    mv   t1, t0
    li   t0, 0
    slt  t0, t0, t1
    xori t0, t0, 1
    sd   t0, -16(s0)
    # JMP_IF_FALSE t4 L1
    ld   t0, -16(s0)
    beqz t0, L1
    # RETURN 0
    li   t0, 0
    mv   a0, t0
    j    .exit_fibonacci
    # LABEL L1
L1:
    # EQ t5 n_1 1
    ld   t0, -8(s0)
    mv   t1, t0
    li   t0, 1
    sub  t0, t1, t0
    seqz t0, t0
    sd   t0, -24(s0)
    # JMP_IF_FALSE t5 L2
    ld   t0, -24(s0)
    beqz t0, L2
    # RETURN 1
    li   t0, 1
    mv   a0, t0
    j    .exit_fibonacci
    # LABEL L2
L2:
    # SUB t6 n_1 1
    ld   t0, -8(s0)
    mv   t1, t0
    li   t0, 1
    sub  t0, t1, t0
    sd   t0, -32(s0)
    # PARAM t6
    # CALL t7 fibonacci 1
    ld   t0, -32(s0)
    addi sp, sp, -8
    sd   t0, 0(sp)
    call fibonacci
    addi sp, sp, 8
    mv   t0, a0
    sd   t0, -40(s0)
    # SUB t8 n_1 2
    ld   t0, -8(s0)
    mv   t1, t0
    li   t0, 2
    sub  t0, t1, t0
    sd   t0, -48(s0)
    # PARAM t8
    # CALL t9 fibonacci 1
    ld   t0, -48(s0)
    addi sp, sp, -8
    sd   t0, 0(sp)
    call fibonacci
    addi sp, sp, 8
    mv   t0, a0
    sd   t0, -56(s0)
    # ADD t10 t7 t9
    ld   t0, -40(s0)
    mv   t1, t0
    ld   t0, -56(s0)
    add  t0, t1, t0
    sd   t0, -64(s0)
    # RETURN t10
    ld   t0, -64(s0)
    mv   a0, t0
    j    .exit_fibonacci
.exit_fibonacci:
    ld   ra, 72(sp)
    ld   s0, 64(sp)
    addi sp, sp, 80
    ret
# --- Function gcd ---
.globl gcd
gcd:
    addi sp, sp, -64
    sd   ra, 56(sp)
    sd   s0, 48(sp)
    addi s0, sp, 48
    # LOAD_PARAM a_2 0
    ld   t0, 16(s0)
    sd   t0, -8(s0)
    # LOAD_PARAM b_3 1
    ld   t0, 24(s0)
    sd   t0, -16(s0)
    # LABEL L3
L3:
    # NEQ t11 b_3 0
    ld   t0, -16(s0)
    mv   t1, t0
    li   t0, 0
    sub  t0, t1, t0
    snez t0, t0
    sd   t0, -24(s0)
    # JMP_IF_FALSE t11 L4
    ld   t0, -24(s0)
    beqz t0, L4
    # MOV temp_4 b_3
    ld   t0, -16(s0)
    sd   t0, -32(s0)
    # MOD t12 a_2 b_3
    ld   t0, -8(s0)
    mv   t1, t0
    ld   t0, -16(s0)
    rem  t0, t1, t0
    sd   t0, -40(s0)
    # MOV b_3 t12
    ld   t0, -40(s0)
    sd   t0, -16(s0)
    # MOV a_2 temp_4
    ld   t0, -32(s0)
    sd   t0, -8(s0)
    # JMP L3
    j    L3
    # LABEL L4
L4:
    # RETURN a_2
    ld   t0, -8(s0)
    mv   a0, t0
    j    .exit_gcd
.exit_gcd:
    ld   ra, 56(sp)
    ld   s0, 48(sp)
    addi sp, sp, 64
    ret
# --- Function power_of_two ---
.globl power_of_two
power_of_two:
    addi sp, sp, -64
    sd   ra, 56(sp)
    sd   s0, 48(sp)
    addi s0, sp, 48
    # LOAD_PARAM n_5 0
    ld   t0, 16(s0)
    sd   t0, -8(s0)
    # MOV result_6 1
    li   t0, 1
    sd   t0, -16(s0)
    # MOV i_7 0
    li   t0, 0
    sd   t0, -24(s0)
    # LABEL L5
L5:
    # LT t13 i_7 n_5
    ld   t0, -24(s0)
    mv   t1, t0
    ld   t0, -8(s0)
    slt  t0, t1, t0
    sd   t0, -32(s0)
    # JMP_IF_FALSE t13 L6
    ld   t0, -32(s0)
    beqz t0, L6
    # LSHIFT t14 result_6 1
    ld   t0, -16(s0)
    slli t0, t0, 1
    sd   t0, -40(s0)
    # MOV result_6 t14
    ld   t0, -40(s0)
    sd   t0, -16(s0)
    # ADD t15 i_7 1
    ld   t0, -24(s0)
    mv   t1, t0
    li   t0, 1
    add  t0, t1, t0
    sd   t0, -48(s0)
    # MOV i_7 t15
    ld   t0, -48(s0)
    sd   t0, -24(s0)
    # JMP L5
    j    L5
    # LABEL L6
L6:
    # RETURN result_6
    ld   t0, -16(s0)
    mv   a0, t0
    j    .exit_power_of_two
.exit_power_of_two:
    ld   ra, 56(sp)
    ld   s0, 48(sp)
    addi sp, sp, 64
    ret
# --- Function max ---
.globl max
max:
    addi sp, sp, -48
    sd   ra, 40(sp)
    sd   s0, 32(sp)
    addi s0, sp, 32
    # LOAD_PARAM a_8 0
    ld   t0, 16(s0)
    sd   t0, -8(s0)
    # LOAD_PARAM b_9 1
    ld   t0, 24(s0)
    sd   t0, -16(s0)
    # GT t16 a_8 b_9
    ld   t0, -8(s0)
    mv   t1, t0
    ld   t0, -16(s0)
    slt  t0, t0, t1
    sd   t0, -24(s0)
    # JMP_IF_FALSE t16 L7
    ld   t0, -24(s0)
    beqz t0, L7
    # RETURN a_8
    ld   t0, -8(s0)
    mv   a0, t0
    j    .exit_max
    # LABEL L7
L7:
    # RETURN b_9
    ld   t0, -16(s0)
    mv   a0, t0
    j    .exit_max
.exit_max:
    ld   ra, 40(sp)
    ld   s0, 32(sp)
    addi sp, sp, 48
    ret
# --- Function min ---
.globl min
min:
    addi sp, sp, -48
    sd   ra, 40(sp)
    sd   s0, 32(sp)
    addi s0, sp, 32
    # LOAD_PARAM a_10 0
    ld   t0, 16(s0)
    sd   t0, -8(s0)
    # LOAD_PARAM b_11 1
    ld   t0, 24(s0)
    sd   t0, -16(s0)
    # LT t17 a_10 b_11
    ld   t0, -8(s0)
    mv   t1, t0
    ld   t0, -16(s0)
    slt  t0, t1, t0
    sd   t0, -24(s0)
    # JMP_IF_FALSE t17 L8
    ld   t0, -24(s0)
    beqz t0, L8
    # RETURN a_10
    ld   t0, -8(s0)
    mv   a0, t0
    j    .exit_min
    # LABEL L8
L8:
    # RETURN b_11
    ld   t0, -16(s0)
    mv   a0, t0
    j    .exit_min
.exit_min:
    ld   ra, 40(sp)
    ld   s0, 32(sp)
    addi sp, sp, 48
    ret
# --- Function main ---
.globl main
main:
    addi sp, sp, -544
    sd   ra, 536(sp)
    sd   s0, 528(sp)
    addi s0, sp, 528
    # PARAM 5
    # CALL t18 factorial 1
    li   t0, 5
    addi sp, sp, -8
    sd   t0, 0(sp)
    call factorial
    addi sp, sp, 8
    mv   t0, a0
    sd   t0, -8(s0)
    # PRINT t18
    ld   t0, -8(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PARAM 7
    # CALL t19 factorial 1
    li   t0, 7
    addi sp, sp, -8
    sd   t0, 0(sp)
    call factorial
    addi sp, sp, 8
    mv   t0, a0
    sd   t0, -16(s0)
    # PRINT t19
    ld   t0, -16(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PARAM 8
    # CALL t20 fibonacci 1
    li   t0, 8
    addi sp, sp, -8
    sd   t0, 0(sp)
    call fibonacci
    addi sp, sp, 8
    mv   t0, a0
    sd   t0, -24(s0)
    # PRINT t20
    ld   t0, -24(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PARAM 10
    # CALL t21 fibonacci 1
    li   t0, 10
    addi sp, sp, -8
    sd   t0, 0(sp)
    call fibonacci
    addi sp, sp, 8
    mv   t0, a0
    sd   t0, -32(s0)
    # PRINT t21
    ld   t0, -32(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # ARR_DECL arr_12 5
    # ASTORE 10 arr_12 0
    li   t0, 0
    slli t0, t0, 3
    addi t1, s0, -72
    add  t1, t1, t0
    mv   t2, t1
    li   t0, 10
    sd   t0, 0(t2)
    # ASTORE 20 arr_12 1
    li   t0, 1
    slli t0, t0, 3
    addi t1, s0, -72
    add  t1, t1, t0
    mv   t2, t1
    li   t0, 20
    sd   t0, 0(t2)
    # ASTORE 30 arr_12 2
    li   t0, 2
    slli t0, t0, 3
    addi t1, s0, -72
    add  t1, t1, t0
    mv   t2, t1
    li   t0, 30
    sd   t0, 0(t2)
    # ASTORE 40 arr_12 3
    li   t0, 3
    slli t0, t0, 3
    addi t1, s0, -72
    add  t1, t1, t0
    mv   t2, t1
    li   t0, 40
    sd   t0, 0(t2)
    # ASTORE 50 arr_12 4
    li   t0, 4
    slli t0, t0, 3
    addi t1, s0, -72
    add  t1, t1, t0
    mv   t2, t1
    li   t0, 50
    sd   t0, 0(t2)
    # MOV total_13 0
    li   t0, 0
    sd   t0, -120(s0)
    # MOV i_14 0
    li   t0, 0
    sd   t0, -128(s0)
    # LABEL L9
L9:
    # LT t22 i_14 5
    ld   t0, -128(s0)
    mv   t1, t0
    li   t0, 5
    slt  t0, t1, t0
    sd   t0, -136(s0)
    # JMP_IF_FALSE t22 L10
    ld   t0, -136(s0)
    beqz t0, L10
    # ALOAD t23 arr_12 i_14
    ld   t0, -128(s0)
    slli t0, t0, 3
    addi t1, s0, -72
    add  t1, t1, t0
    ld   t0, 0(t1)
    sd   t0, -144(s0)
    # ADD t24 total_13 t23
    ld   t0, -120(s0)
    mv   t1, t0
    ld   t0, -144(s0)
    add  t0, t1, t0
    sd   t0, -152(s0)
    # MOV total_13 t24
    ld   t0, -152(s0)
    sd   t0, -120(s0)
    # ADD t25 i_14 1
    ld   t0, -128(s0)
    mv   t1, t0
    li   t0, 1
    add  t0, t1, t0
    sd   t0, -160(s0)
    # MOV i_14 t25
    ld   t0, -160(s0)
    sd   t0, -128(s0)
    # JMP L9
    j    L9
    # LABEL L10
L10:
    # PRINT total_13
    ld   t0, -120(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # ARR_DECL sarr_15 5
    # ASTORE 5 sarr_15 0
    li   t0, 0
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    mv   t2, t1
    li   t0, 5
    sd   t0, 0(t2)
    # ASTORE 3 sarr_15 1
    li   t0, 1
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    mv   t2, t1
    li   t0, 3
    sd   t0, 0(t2)
    # ASTORE 1 sarr_15 2
    li   t0, 2
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    mv   t2, t1
    li   t0, 1
    sd   t0, 0(t2)
    # ASTORE 4 sarr_15 3
    li   t0, 3
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    mv   t2, t1
    li   t0, 4
    sd   t0, 0(t2)
    # ASTORE 2 sarr_15 4
    li   t0, 4
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    mv   t2, t1
    li   t0, 2
    sd   t0, 0(t2)
    # MOV p_16 0
    li   t0, 0
    sd   t0, -248(s0)
    # LABEL L11
L11:
    # LT t26 p_16 4
    ld   t0, -248(s0)
    mv   t1, t0
    li   t0, 4
    slt  t0, t1, t0
    sd   t0, -256(s0)
    # JMP_IF_FALSE t26 L12
    ld   t0, -256(s0)
    beqz t0, L12
    # MOV q_17 0
    li   t0, 0
    sd   t0, -264(s0)
    # LABEL L13
L13:
    # SUB t27 4 p_16
    li   t0, 4
    mv   t1, t0
    ld   t0, -248(s0)
    sub  t0, t1, t0
    sd   t0, -272(s0)
    # LT t28 q_17 t27
    ld   t0, -264(s0)
    mv   t1, t0
    ld   t0, -272(s0)
    slt  t0, t1, t0
    sd   t0, -280(s0)
    # JMP_IF_FALSE t28 L14
    ld   t0, -280(s0)
    beqz t0, L14
    # ALOAD t29 sarr_15 q_17
    ld   t0, -264(s0)
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    ld   t0, 0(t1)
    sd   t0, -288(s0)
    # ADD t30 q_17 1
    ld   t0, -264(s0)
    mv   t1, t0
    li   t0, 1
    add  t0, t1, t0
    sd   t0, -296(s0)
    # ALOAD t31 sarr_15 t30
    ld   t0, -296(s0)
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    ld   t0, 0(t1)
    sd   t0, -304(s0)
    # GT t32 t29 t31
    ld   t0, -288(s0)
    mv   t1, t0
    ld   t0, -304(s0)
    slt  t0, t0, t1
    sd   t0, -312(s0)
    # JMP_IF_FALSE t32 L15
    ld   t0, -312(s0)
    beqz t0, L15
    # ALOAD t33 sarr_15 q_17
    ld   t0, -264(s0)
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    ld   t0, 0(t1)
    sd   t0, -320(s0)
    # ALOAD t35 sarr_15 t30
    ld   t0, -296(s0)
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    ld   t0, 0(t1)
    sd   t0, -328(s0)
    # ASTORE t35 sarr_15 q_17
    ld   t0, -264(s0)
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    mv   t2, t1
    ld   t0, -328(s0)
    sd   t0, 0(t2)
    # ASTORE t33 sarr_15 t30
    ld   t0, -296(s0)
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    mv   t2, t1
    ld   t0, -320(s0)
    sd   t0, 0(t2)
    # LABEL L15
L15:
    # ADD t37 q_17 1
    ld   t0, -264(s0)
    mv   t1, t0
    li   t0, 1
    add  t0, t1, t0
    sd   t0, -336(s0)
    # MOV q_17 t37
    ld   t0, -336(s0)
    sd   t0, -264(s0)
    # JMP L13
    j    L13
    # LABEL L14
L14:
    # ADD t38 p_16 1
    ld   t0, -248(s0)
    mv   t1, t0
    li   t0, 1
    add  t0, t1, t0
    sd   t0, -344(s0)
    # MOV p_16 t38
    ld   t0, -344(s0)
    sd   t0, -248(s0)
    # JMP L11
    j    L11
    # LABEL L12
L12:
    # ALOAD t39 sarr_15 0
    li   t0, 0
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    ld   t0, 0(t1)
    sd   t0, -352(s0)
    # PRINT t39
    ld   t0, -352(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # ALOAD t40 sarr_15 1
    li   t0, 1
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    ld   t0, 0(t1)
    sd   t0, -360(s0)
    # PRINT t40
    ld   t0, -360(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # ALOAD t41 sarr_15 2
    li   t0, 2
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    ld   t0, 0(t1)
    sd   t0, -368(s0)
    # PRINT t41
    ld   t0, -368(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # ALOAD t42 sarr_15 3
    li   t0, 3
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    ld   t0, 0(t1)
    sd   t0, -376(s0)
    # PRINT t42
    ld   t0, -376(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # ALOAD t43 sarr_15 4
    li   t0, 4
    slli t0, t0, 3
    addi t1, s0, -200
    add  t1, t1, t0
    ld   t0, 0(t1)
    sd   t0, -384(s0)
    # PRINT t43
    ld   t0, -384(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PARAM 48
    # PARAM 18
    # CALL t44 gcd 2
    li   t0, 18
    addi sp, sp, -8
    sd   t0, 0(sp)
    li   t0, 48
    addi sp, sp, -8
    sd   t0, 0(sp)
    call gcd
    addi sp, sp, 16
    mv   t0, a0
    sd   t0, -392(s0)
    # PRINT t44
    ld   t0, -392(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PARAM 100
    # PARAM 75
    # CALL t45 gcd 2
    li   t0, 75
    addi sp, sp, -8
    sd   t0, 0(sp)
    li   t0, 100
    addi sp, sp, -8
    sd   t0, 0(sp)
    call gcd
    addi sp, sp, 16
    mv   t0, a0
    sd   t0, -400(s0)
    # PRINT t45
    ld   t0, -400(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # MOV sum_19 0
    li   t0, 0
    sd   t0, -408(s0)
    # MOV j_20 1
    li   t0, 1
    sd   t0, -416(s0)
    # LABEL L16
L16:
    # LTE t46 j_20 10
    ld   t0, -416(s0)
    mv   t1, t0
    li   t0, 10
    slt  t0, t0, t1
    xori t0, t0, 1
    sd   t0, -424(s0)
    # JMP_IF_FALSE t46 L17
    ld   t0, -424(s0)
    beqz t0, L17
    # ADD t47 sum_19 j_20
    ld   t0, -408(s0)
    mv   t1, t0
    ld   t0, -416(s0)
    add  t0, t1, t0
    sd   t0, -432(s0)
    # MOV sum_19 t47
    ld   t0, -432(s0)
    sd   t0, -408(s0)
    # ADD t48 j_20 1
    ld   t0, -416(s0)
    mv   t1, t0
    li   t0, 1
    add  t0, t1, t0
    sd   t0, -440(s0)
    # MOV j_20 t48
    ld   t0, -440(s0)
    sd   t0, -416(s0)
    # JMP L16
    j    L16
    # LABEL L17
L17:
    # PRINT sum_19
    ld   t0, -408(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # MOV fsum_21 0
    li   t0, 0
    sd   t0, -448(s0)
    # MOV k_22 1
    li   t0, 1
    sd   t0, -456(s0)
    # LABEL L18
L18:
    # LTE t49 k_22 5
    ld   t0, -456(s0)
    mv   t1, t0
    li   t0, 5
    slt  t0, t0, t1
    xori t0, t0, 1
    sd   t0, -464(s0)
    # JMP_IF_FALSE t49 L20
    ld   t0, -464(s0)
    beqz t0, L20
    # MUL t50 k_22 k_22
    ld   t0, -456(s0)
    mv   t1, t0
    ld   t0, -456(s0)
    mul  t0, t1, t0
    sd   t0, -472(s0)
    # ADD t51 fsum_21 t50
    ld   t0, -448(s0)
    mv   t1, t0
    ld   t0, -472(s0)
    add  t0, t1, t0
    sd   t0, -480(s0)
    # MOV fsum_21 t51
    ld   t0, -480(s0)
    sd   t0, -448(s0)
    # ADD t52 k_22 1
    ld   t0, -456(s0)
    mv   t1, t0
    li   t0, 1
    add  t0, t1, t0
    sd   t0, -488(s0)
    # MOV k_22 t52
    ld   t0, -488(s0)
    sd   t0, -456(s0)
    # JMP L18
    j    L18
    # LABEL L20
L20:
    # PRINT fsum_21
    ld   t0, -448(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PRINT 32
    li   t0, 32
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PRINT 64
    li   t0, 64
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PRINT 8
    li   t0, 8
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PRINT 84
    li   t0, 84
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PRINT 52
    li   t0, 52
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PRINT 60
    li   t0, 60
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PARAM 12
    # PARAM 8
    # CALL t64 gcd 2
    li   t0, 8
    addi sp, sp, -8
    sd   t0, 0(sp)
    li   t0, 12
    addi sp, sp, -8
    sd   t0, 0(sp)
    call gcd
    addi sp, sp, 16
    mv   t0, a0
    sd   t0, -496(s0)
    # PARAM t64
    # CALL t65 factorial 1
    ld   t0, -496(s0)
    addi sp, sp, -8
    sd   t0, 0(sp)
    call factorial
    addi sp, sp, 8
    mv   t0, a0
    sd   t0, -504(s0)
    # PRINT t65
    ld   t0, -504(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PARAM 8
    # CALL t66 power_of_two 1
    li   t0, 8
    addi sp, sp, -8
    sd   t0, 0(sp)
    call power_of_two
    addi sp, sp, 8
    mv   t0, a0
    sd   t0, -512(s0)
    # PRINT t66
    ld   t0, -512(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PARAM 42
    # PARAM 17
    # CALL t67 max 2
    li   t0, 17
    addi sp, sp, -8
    sd   t0, 0(sp)
    li   t0, 42
    addi sp, sp, -8
    sd   t0, 0(sp)
    call max
    addi sp, sp, 16
    mv   t0, a0
    sd   t0, -520(s0)
    # PRINT t67
    ld   t0, -520(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PARAM 42
    # PARAM 17
    # CALL t68 min 2
    li   t0, 17
    addi sp, sp, -8
    sd   t0, 0(sp)
    li   t0, 42
    addi sp, sp, -8
    sd   t0, 0(sp)
    call min
    addi sp, sp, 16
    mv   t0, a0
    sd   t0, -528(s0)
    # PRINT t68
    ld   t0, -528(s0)
    mv   a1, t0
    la   a0, fmt_int
    call printf
    # PRINT 9
    li   t0, 9
    mv   a1, t0
    la   a0, fmt_int
    call printf
.exit_main:
    ld   ra, 536(sp)
    ld   s0, 528(sp)
    addi sp, sp, 544
    ret
