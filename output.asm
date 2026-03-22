section .data
    fmt_int db "%ld", 10, 0

section .text
    extern printf
    extern scanf

; --- Function factorial ---
global factorial
factorial:
    push rbp
    mov rbp, rsp
    sub rsp, 48
    ; LOAD_PARAM n_0 0
    mov rax, [rbp + 16]
    mov [rbp - 8], rax
    ; LTE t0 n_0 1
    mov rax, [rbp - 8]
    cmp rax, 1
    setle al
    movzx rax, al
    mov [rbp - 16], rax
    ; JMP_IF_FALSE t0 L0
    mov rax, [rbp - 16]
    cmp rax, 0
    je L0
    ; RETURN 1
    mov rax, 1
    mov rsp, rbp
    pop rbp
    ret
    ; LABEL L0
L0:
    ; SUB t1 n_0 1
    mov rax, [rbp - 8]
    sub rax, 1
    mov [rbp - 24], rax
    ; PARAM t1
    ; CALL t2 factorial 1
    mov rax, [rbp - 24]
    push rax
    call factorial
    add rsp, 8
    mov [rbp - 32], rax
    ; MUL t3 n_0 t2
    mov rax, [rbp - 8]
    imul rax, [rbp - 32]
    mov [rbp - 40], rax
    ; RETURN t3
    mov rax, [rbp - 40]
    mov rsp, rbp
    pop rbp
    ret
.exit_factorial:
    mov rsp, rbp
    pop rbp
    ret
; --- Function fibonacci ---
global fibonacci
fibonacci:
    push rbp
    mov rbp, rsp
    sub rsp, 64
    ; LOAD_PARAM n_1 0
    mov rax, [rbp + 16]
    mov [rbp - 8], rax
    ; LTE t4 n_1 0
    mov rax, [rbp - 8]
    cmp rax, 0
    setle al
    movzx rax, al
    mov [rbp - 16], rax
    ; JMP_IF_FALSE t4 L1
    mov rax, [rbp - 16]
    cmp rax, 0
    je L1
    ; RETURN 0
    mov rax, 0
    mov rsp, rbp
    pop rbp
    ret
    ; LABEL L1
L1:
    ; EQ t5 n_1 1
    mov rax, [rbp - 8]
    cmp rax, 1
    sete al
    movzx rax, al
    mov [rbp - 24], rax
    ; JMP_IF_FALSE t5 L2
    mov rax, [rbp - 24]
    cmp rax, 0
    je L2
    ; RETURN 1
    mov rax, 1
    mov rsp, rbp
    pop rbp
    ret
    ; LABEL L2
L2:
    ; SUB t6 n_1 1
    mov rax, [rbp - 8]
    sub rax, 1
    mov [rbp - 32], rax
    ; PARAM t6
    ; CALL t7 fibonacci 1
    mov rax, [rbp - 32]
    push rax
    call fibonacci
    add rsp, 8
    mov [rbp - 40], rax
    ; SUB t8 n_1 2
    mov rax, [rbp - 8]
    sub rax, 2
    mov [rbp - 48], rax
    ; PARAM t8
    ; CALL t9 fibonacci 1
    mov rax, [rbp - 48]
    push rax
    call fibonacci
    add rsp, 8
    mov [rbp - 56], rax
    ; ADD t10 t7 t9
    mov rax, [rbp - 40]
    mov rbx, rax
    add rbx, [rbp - 56]
    mov rax, rbx
    mov [rbp - 64], rax
    ; RETURN t10
    mov rax, [rbp - 64]
    mov rsp, rbp
    pop rbp
    ret
.exit_fibonacci:
    mov rsp, rbp
    pop rbp
    ret
; --- Function gcd ---
global gcd
gcd:
    push rbp
    mov rbp, rsp
    sub rsp, 48
    ; LOAD_PARAM a_2 0
    mov rax, [rbp + 16]
    mov [rbp - 8], rax
    ; LOAD_PARAM b_3 1
    mov rax, [rbp + 24]
    mov [rbp - 16], rax
    ; LABEL L3
L3:
    ; NEQ t11 b_3 0
    mov rax, [rbp - 16]
    cmp rax, 0
    setne al
    movzx rax, al
    mov [rbp - 24], rax
    ; JMP_IF_FALSE t11 L4
    mov rax, [rbp - 24]
    cmp rax, 0
    je L4
    ; MOV temp_4 b_3
    mov rax, [rbp - 16]
    mov [rbp - 32], rax
    ; MOD t12 a_2 b_3
    mov rax, [rbp - 8]
    cqo
    idiv qword [rbp - 16]
    mov rax, rdx
    mov [rbp - 40], rax
    ; MOV b_3 t12
    mov rax, [rbp - 40]
    mov [rbp - 16], rax
    ; MOV a_2 temp_4
    mov rax, [rbp - 32]
    mov [rbp - 8], rax
    ; JMP L3
    jmp L3
    ; LABEL L4
L4:
    ; RETURN a_2
    mov rax, [rbp - 8]
    mov rsp, rbp
    pop rbp
    ret
.exit_gcd:
    mov rsp, rbp
    pop rbp
    ret
; --- Function power_of_two ---
global power_of_two
power_of_two:
    push rbp
    mov rbp, rsp
    sub rsp, 48
    ; LOAD_PARAM n_5 0
    mov rax, [rbp + 16]
    mov [rbp - 8], rax
    ; MOV result_6 1
    mov rax, 1
    mov [rbp - 16], rax
    ; MOV i_7 0
    mov rax, 0
    mov [rbp - 24], rax
    ; LABEL L5
L5:
    ; LT t13 i_7 n_5
    mov rax, [rbp - 24]
    cmp rax, [rbp - 8]
    setl al
    movzx rax, al
    mov [rbp - 32], rax
    ; JMP_IF_FALSE t13 L6
    mov rax, [rbp - 32]
    cmp rax, 0
    je L6
    ; LSHIFT t14 result_6 1
    mov rax, [rbp - 16]
    shl rax, 1
    mov [rbp - 40], rax
    ; MOV result_6 t14
    mov rax, [rbp - 40]
    mov [rbp - 16], rax
    ; ADD t15 i_7 1
    mov rax, [rbp - 24]
    mov rbx, rax
    add rbx, 1
    mov rax, rbx
    mov [rbp - 48], rax
    ; MOV i_7 t15
    mov rax, [rbp - 48]
    mov [rbp - 24], rax
    ; JMP L5
    jmp L5
    ; LABEL L6
L6:
    ; RETURN result_6
    mov rax, [rbp - 16]
    mov rsp, rbp
    pop rbp
    ret
.exit_power_of_two:
    mov rsp, rbp
    pop rbp
    ret
; --- Function max ---
global max
max:
    push rbp
    mov rbp, rsp
    sub rsp, 32
    ; LOAD_PARAM a_8 0
    mov rax, [rbp + 16]
    mov [rbp - 8], rax
    ; LOAD_PARAM b_9 1
    mov rax, [rbp + 24]
    mov [rbp - 16], rax
    ; GT t16 a_8 b_9
    mov rax, [rbp - 8]
    cmp rax, [rbp - 16]
    setg al
    movzx rax, al
    mov [rbp - 24], rax
    ; JMP_IF_FALSE t16 L7
    mov rax, [rbp - 24]
    cmp rax, 0
    je L7
    ; RETURN a_8
    mov rax, [rbp - 8]
    mov rsp, rbp
    pop rbp
    ret
    ; LABEL L7
L7:
    ; RETURN b_9
    mov rax, [rbp - 16]
    mov rsp, rbp
    pop rbp
    ret
.exit_max:
    mov rsp, rbp
    pop rbp
    ret
; --- Function min ---
global min
min:
    push rbp
    mov rbp, rsp
    sub rsp, 32
    ; LOAD_PARAM a_10 0
    mov rax, [rbp + 16]
    mov [rbp - 8], rax
    ; LOAD_PARAM b_11 1
    mov rax, [rbp + 24]
    mov [rbp - 16], rax
    ; LT t17 a_10 b_11
    mov rax, [rbp - 8]
    cmp rax, [rbp - 16]
    setl al
    movzx rax, al
    mov [rbp - 24], rax
    ; JMP_IF_FALSE t17 L8
    mov rax, [rbp - 24]
    cmp rax, 0
    je L8
    ; RETURN a_10
    mov rax, [rbp - 8]
    mov rsp, rbp
    pop rbp
    ret
    ; LABEL L8
L8:
    ; RETURN b_11
    mov rax, [rbp - 16]
    mov rsp, rbp
    pop rbp
    ret
.exit_min:
    mov rsp, rbp
    pop rbp
    ret
; --- Function main ---
global main
main:
    push rbp
    mov rbp, rsp
    sub rsp, 528
    ; PARAM 5
    ; CALL t18 factorial 1
    mov rax, 5
    push rax
    call factorial
    add rsp, 8
    mov [rbp - 8], rax
    ; PRINT t18
    mov rax, [rbp - 8]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PARAM 7
    ; CALL t19 factorial 1
    mov rax, 7
    push rax
    call factorial
    add rsp, 8
    mov [rbp - 16], rax
    ; PRINT t19
    mov rax, [rbp - 16]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PARAM 8
    ; CALL t20 fibonacci 1
    mov rax, 8
    push rax
    call fibonacci
    add rsp, 8
    mov [rbp - 24], rax
    ; PRINT t20
    mov rax, [rbp - 24]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PARAM 10
    ; CALL t21 fibonacci 1
    mov rax, 10
    push rax
    call fibonacci
    add rsp, 8
    mov [rbp - 32], rax
    ; PRINT t21
    mov rax, [rbp - 32]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; ARR_DECL arr_12 5
    ; ASTORE 10 arr_12 0
    mov rax, 0
    imul rax, 8
    lea rcx, [rbp - 72]
    add rcx, rax
    push rcx
    mov rax, 10
    mov r9, rax
    pop rcx
    mov [rcx], r9
    ; ASTORE 20 arr_12 1
    mov rax, 1
    imul rax, 8
    lea rcx, [rbp - 72]
    add rcx, rax
    push rcx
    mov rax, 20
    mov r9, rax
    pop rcx
    mov [rcx], r9
    ; ASTORE 30 arr_12 2
    mov rax, 2
    imul rax, 8
    lea rcx, [rbp - 72]
    add rcx, rax
    push rcx
    mov rax, 30
    mov r9, rax
    pop rcx
    mov [rcx], r9
    ; ASTORE 40 arr_12 3
    mov rax, 3
    imul rax, 8
    lea rcx, [rbp - 72]
    add rcx, rax
    push rcx
    mov rax, 40
    mov r9, rax
    pop rcx
    mov [rcx], r9
    ; ASTORE 50 arr_12 4
    mov rax, 4
    imul rax, 8
    lea rcx, [rbp - 72]
    add rcx, rax
    push rcx
    mov rax, 50
    mov r9, rax
    pop rcx
    mov [rcx], r9
    ; MOV total_13 0
    mov rax, 0
    mov [rbp - 120], rax
    ; MOV i_14 0
    mov rax, 0
    mov [rbp - 128], rax
    ; LABEL L9
L9:
    ; LT t22 i_14 5
    mov rax, [rbp - 128]
    cmp rax, 5
    setl al
    movzx rax, al
    mov [rbp - 136], rax
    ; JMP_IF_FALSE t22 L10
    mov rax, [rbp - 136]
    cmp rax, 0
    je L10
    ; ALOAD t23 arr_12 i_14
    mov rax, [rbp - 128]
    imul rax, 8
    lea rcx, [rbp - 72]
    add rcx, rax
    mov rdx, [rcx]
    mov [rbp - 144], rdx
    ; ADD t24 total_13 t23
    mov rax, [rbp - 120]
    mov rbx, rax
    add rbx, [rbp - 144]
    mov rax, rbx
    mov [rbp - 152], rax
    ; MOV total_13 t24
    mov rax, [rbp - 152]
    mov [rbp - 120], rax
    ; ADD t25 i_14 1
    mov rax, [rbp - 128]
    mov rbx, rax
    add rbx, 1
    mov rax, rbx
    mov [rbp - 160], rax
    ; MOV i_14 t25
    mov rax, [rbp - 160]
    mov [rbp - 128], rax
    ; JMP L9
    jmp L9
    ; LABEL L10
L10:
    ; PRINT total_13
    mov rax, [rbp - 120]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; ARR_DECL sarr_15 5
    ; ASTORE 5 sarr_15 0
    mov rax, 0
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    push rcx
    mov rax, 5
    mov r9, rax
    pop rcx
    mov [rcx], r9
    ; ASTORE 3 sarr_15 1
    mov rax, 1
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    push rcx
    mov rax, 3
    mov r9, rax
    pop rcx
    mov [rcx], r9
    ; ASTORE 1 sarr_15 2
    mov rax, 2
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    push rcx
    mov rax, 1
    mov r9, rax
    pop rcx
    mov [rcx], r9
    ; ASTORE 4 sarr_15 3
    mov rax, 3
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    push rcx
    mov rax, 4
    mov r9, rax
    pop rcx
    mov [rcx], r9
    ; ASTORE 2 sarr_15 4
    mov rax, 4
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    push rcx
    mov rax, 2
    mov r9, rax
    pop rcx
    mov [rcx], r9
    ; MOV p_16 0
    mov rax, 0
    mov [rbp - 248], rax
    ; LABEL L11
L11:
    ; LT t26 p_16 4
    mov rax, [rbp - 248]
    cmp rax, 4
    setl al
    movzx rax, al
    mov [rbp - 256], rax
    ; JMP_IF_FALSE t26 L12
    mov rax, [rbp - 256]
    cmp rax, 0
    je L12
    ; MOV q_17 0
    mov rax, 0
    mov [rbp - 264], rax
    ; LABEL L13
L13:
    ; SUB t27 4 p_16
    mov rax, 4
    sub rax, [rbp - 248]
    mov [rbp - 272], rax
    ; LT t28 q_17 t27
    mov rax, [rbp - 264]
    cmp rax, [rbp - 272]
    setl al
    movzx rax, al
    mov [rbp - 280], rax
    ; JMP_IF_FALSE t28 L14
    mov rax, [rbp - 280]
    cmp rax, 0
    je L14
    ; ALOAD t29 sarr_15 q_17
    mov rax, [rbp - 264]
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    mov rdx, [rcx]
    mov [rbp - 288], rdx
    ; ADD t30 q_17 1
    mov rax, [rbp - 264]
    mov rbx, rax
    add rbx, 1
    mov rax, rbx
    mov [rbp - 296], rax
    ; ALOAD t31 sarr_15 t30
    mov rax, [rbp - 296]
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    mov rdx, [rcx]
    mov [rbp - 304], rdx
    ; GT t32 t29 t31
    mov rax, [rbp - 288]
    cmp rax, [rbp - 304]
    setg al
    movzx rax, al
    mov [rbp - 312], rax
    ; JMP_IF_FALSE t32 L15
    mov rax, [rbp - 312]
    cmp rax, 0
    je L15
    ; ALOAD t33 sarr_15 q_17
    mov rax, [rbp - 264]
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    mov rdx, [rcx]
    mov [rbp - 320], rdx
    ; ALOAD t35 sarr_15 t30
    mov rax, [rbp - 296]
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    mov rdx, [rcx]
    mov [rbp - 328], rdx
    ; ASTORE t35 sarr_15 q_17
    mov rax, [rbp - 264]
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    push rcx
    mov rax, [rbp - 328]
    mov r9, rax
    pop rcx
    mov [rcx], r9
    ; ASTORE t33 sarr_15 t30
    mov rax, [rbp - 296]
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    push rcx
    mov rax, [rbp - 320]
    mov r9, rax
    pop rcx
    mov [rcx], r9
    ; LABEL L15
L15:
    ; ADD t37 q_17 1
    mov rax, [rbp - 264]
    mov rbx, rax
    add rbx, 1
    mov rax, rbx
    mov [rbp - 336], rax
    ; MOV q_17 t37
    mov rax, [rbp - 336]
    mov [rbp - 264], rax
    ; JMP L13
    jmp L13
    ; LABEL L14
L14:
    ; ADD t38 p_16 1
    mov rax, [rbp - 248]
    mov rbx, rax
    add rbx, 1
    mov rax, rbx
    mov [rbp - 344], rax
    ; MOV p_16 t38
    mov rax, [rbp - 344]
    mov [rbp - 248], rax
    ; JMP L11
    jmp L11
    ; LABEL L12
L12:
    ; ALOAD t39 sarr_15 0
    mov rax, 0
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    mov rdx, [rcx]
    mov [rbp - 352], rdx
    ; PRINT t39
    mov rax, [rbp - 352]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; ALOAD t40 sarr_15 1
    mov rax, 1
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    mov rdx, [rcx]
    mov [rbp - 360], rdx
    ; PRINT t40
    mov rax, [rbp - 360]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; ALOAD t41 sarr_15 2
    mov rax, 2
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    mov rdx, [rcx]
    mov [rbp - 368], rdx
    ; PRINT t41
    mov rax, [rbp - 368]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; ALOAD t42 sarr_15 3
    mov rax, 3
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    mov rdx, [rcx]
    mov [rbp - 376], rdx
    ; PRINT t42
    mov rax, [rbp - 376]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; ALOAD t43 sarr_15 4
    mov rax, 4
    imul rax, 8
    lea rcx, [rbp - 200]
    add rcx, rax
    mov rdx, [rcx]
    mov [rbp - 384], rdx
    ; PRINT t43
    mov rax, [rbp - 384]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PARAM 48
    ; PARAM 18
    ; CALL t44 gcd 2
    mov rax, 18
    push rax
    mov rax, 48
    push rax
    call gcd
    add rsp, 16
    mov [rbp - 392], rax
    ; PRINT t44
    mov rax, [rbp - 392]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PARAM 100
    ; PARAM 75
    ; CALL t45 gcd 2
    mov rax, 75
    push rax
    mov rax, 100
    push rax
    call gcd
    add rsp, 16
    mov [rbp - 400], rax
    ; PRINT t45
    mov rax, [rbp - 400]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; MOV sum_19 0
    mov rax, 0
    mov [rbp - 408], rax
    ; MOV j_20 1
    mov rax, 1
    mov [rbp - 416], rax
    ; LABEL L16
L16:
    ; LTE t46 j_20 10
    mov rax, [rbp - 416]
    cmp rax, 10
    setle al
    movzx rax, al
    mov [rbp - 424], rax
    ; JMP_IF_FALSE t46 L17
    mov rax, [rbp - 424]
    cmp rax, 0
    je L17
    ; ADD t47 sum_19 j_20
    mov rax, [rbp - 408]
    mov rbx, rax
    add rbx, [rbp - 416]
    mov rax, rbx
    mov [rbp - 432], rax
    ; MOV sum_19 t47
    mov rax, [rbp - 432]
    mov [rbp - 408], rax
    ; ADD t48 j_20 1
    mov rax, [rbp - 416]
    mov rbx, rax
    add rbx, 1
    mov rax, rbx
    mov [rbp - 440], rax
    ; MOV j_20 t48
    mov rax, [rbp - 440]
    mov [rbp - 416], rax
    ; JMP L16
    jmp L16
    ; LABEL L17
L17:
    ; PRINT sum_19
    mov rax, [rbp - 408]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; MOV fsum_21 0
    mov rax, 0
    mov [rbp - 448], rax
    ; MOV k_22 1
    mov rax, 1
    mov [rbp - 456], rax
    ; LABEL L18
L18:
    ; LTE t49 k_22 5
    mov rax, [rbp - 456]
    cmp rax, 5
    setle al
    movzx rax, al
    mov [rbp - 464], rax
    ; JMP_IF_FALSE t49 L20
    mov rax, [rbp - 464]
    cmp rax, 0
    je L20
    ; MUL t50 k_22 k_22
    mov rax, [rbp - 456]
    imul rax, [rbp - 456]
    mov [rbp - 472], rax
    ; ADD t51 fsum_21 t50
    mov rax, [rbp - 448]
    mov rbx, rax
    add rbx, [rbp - 472]
    mov rax, rbx
    mov [rbp - 480], rax
    ; MOV fsum_21 t51
    mov rax, [rbp - 480]
    mov [rbp - 448], rax
    ; ADD t52 k_22 1
    mov rax, [rbp - 456]
    mov rbx, rax
    add rbx, 1
    mov rax, rbx
    mov [rbp - 488], rax
    ; MOV k_22 t52
    mov rax, [rbp - 488]
    mov [rbp - 456], rax
    ; JMP L18
    jmp L18
    ; LABEL L20
L20:
    ; PRINT fsum_21
    mov rax, [rbp - 448]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PRINT 32
    mov rax, 32
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PRINT 64
    mov rax, 64
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PRINT 8
    mov rax, 8
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PRINT 84
    mov rax, 84
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PRINT 52
    mov rax, 52
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PRINT 60
    mov rax, 60
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PARAM 12
    ; PARAM 8
    ; CALL t64 gcd 2
    mov rax, 8
    push rax
    mov rax, 12
    push rax
    call gcd
    add rsp, 16
    mov [rbp - 496], rax
    ; PARAM t64
    ; CALL t65 factorial 1
    mov rax, [rbp - 496]
    push rax
    call factorial
    add rsp, 8
    mov [rbp - 504], rax
    ; PRINT t65
    mov rax, [rbp - 504]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PARAM 8
    ; CALL t66 power_of_two 1
    mov rax, 8
    push rax
    call power_of_two
    add rsp, 8
    mov [rbp - 512], rax
    ; PRINT t66
    mov rax, [rbp - 512]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PARAM 42
    ; PARAM 17
    ; CALL t67 max 2
    mov rax, 17
    push rax
    mov rax, 42
    push rax
    call max
    add rsp, 16
    mov [rbp - 520], rax
    ; PRINT t67
    mov rax, [rbp - 520]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PARAM 42
    ; PARAM 17
    ; CALL t68 min 2
    mov rax, 17
    push rax
    mov rax, 42
    push rax
    call min
    add rsp, 16
    mov [rbp - 528], rax
    ; PRINT t68
    mov rax, [rbp - 528]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PRINT 9
    mov rax, 9
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