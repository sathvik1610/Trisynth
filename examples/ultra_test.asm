section .data
    fmt_int db "%d", 10, 0

section .text
    extern printf
    extern scanf

; --- Function main ---
global main
main:
    push rbp
    mov rbp, rsp
    sub rsp, 112
    ; PRINT 11111
    mov rax, 11111
    mov rsi, rax
    lea rdi, [fmt_int]
    xor rax, rax
    call printf
    ; MOV i_2 0
    mov rax, 0
    mov [rbp - 8], rax
    ; LABEL L0
L0:
    ; LT t0 i_2 10
    mov rax, [rbp - 8]
    cmp rax, 10
    setl al
    movzx rax, al
    mov [rbp - 16], rax
    ; JMP_IF_FALSE t0 L2
    mov rax, [rbp - 16]
    cmp rax, 0
    je L2
    ; LSHIFT t1 i_2 2
    mov rax, [rbp - 8]
    shl rax, 2
    mov [rbp - 24], rax
    ; ASTORE t1 data_1 i_2
    mov rax, [rbp - 8]
    imul rax, 8
    lea rcx, [rbp - 120]
    add rcx, rax
    push rcx
    mov rax, [rbp - 24]
    pop rcx
    mov [rcx], rax
    ; LABEL L1
L1:
    ; ADD t2 i_2 1
    mov rax, [rbp - 8]
    mov rbx, rax
    add rbx, 1
    mov rax, rbx
    mov [rbp - 32], rax
    ; MOV i_2 t2
    mov rax, [rbp - 32]
    mov [rbp - 8], rax
    ; JMP L0
    jmp L0
    ; LABEL L2
L2:
    ; PARAM 0
    ; PARAM 0
    ; CALL t3 find_target 2
    mov rax, 0
    push rax
    mov rax, 0
    push rax
    call find_target
    add rsp, 16
    mov [rbp - 40], rax
    ; MOV found_idx_3 t3
    mov rax, [rbp - 40]
    mov [rbp - 48], rax
    ; PRINT found_idx_3
    mov rax, [rbp - 48]
    mov rsi, rax
    lea rdi, [fmt_int]
    xor rax, rax
    call printf
    ; PRINT 222
    mov rax, 222
    mov rsi, rax
    lea rdi, [fmt_int]
    xor rax, rax
    call printf
    ; PRINT 999
    mov rax, 999
    mov rsi, rax
    lea rdi, [fmt_int]
    xor rax, rax
    call printf
    ; MOV k_6 0
    mov rax, 0
    mov [rbp - 56], rax
    ; LABEL L3
L3:
    ; JMP_IF_FALSE 1 L4
    mov rax, 1
    cmp rax, 0
    je L4
    ; GTE t5 k_6 10
    mov rax, [rbp - 56]
    cmp rax, 10
    setge al
    movzx rax, al
    mov [rbp - 64], rax
    ; JMP_IF_FALSE t5 L5
    mov rax, [rbp - 64]
    cmp rax, 0
    je L5
    ; JMP L4
    jmp L4
    ; JMP L5
    jmp L5
    ; LABEL L5
L5:
    ; RSHIFT t6 k_6 1
    mov rax, [rbp - 56]
    sar rax, 1
    mov [rbp - 72], rax
    ; MOV half_7 t6
    mov rax, [rbp - 72]
    mov [rbp - 80], rax
    ; MOD t7 half_7 2
    mov rax, [rbp - 80]
    cqo
    mov rcx, 2
    idiv rcx
    mov rax, rdx
    mov [rbp - 88], rax
    ; NEQ t8 t7 0
    mov rax, [rbp - 88]
    cmp rax, 0
    setne al
    movzx rax, al
    mov [rbp - 96], rax
    ; JMP_IF_FALSE t8 L6
    mov rax, [rbp - 96]
    cmp rax, 0
    je L6
    ; ADD t9 k_6 1
    mov rax, [rbp - 56]
    mov rbx, rax
    add rbx, 1
    mov rax, rbx
    mov [rbp - 104], rax
    ; MOV k_6 t9
    mov rax, [rbp - 104]
    mov [rbp - 56], rax
    ; JMP L3
    jmp L3
    ; JMP L6
    jmp L6
    ; LABEL L6
L6:
    ; PRINT half_7
    mov rax, [rbp - 80]
    mov rsi, rax
    lea rdi, [fmt_int]
    xor rax, rax
    call printf
    ; ADD t10 k_6 1
    mov rax, [rbp - 56]
    mov rbx, rax
    add rbx, 1
    mov rax, rbx
    mov [rbp - 112], rax
    ; MOV k_6 t10
    mov rax, [rbp - 112]
    mov [rbp - 56], rax
    ; JMP L3
    jmp L3
    ; LABEL L4
L4:
    ; PRINT 40
    mov rax, 40
    mov rsi, rax
    lea rdi, [fmt_int]
    xor rax, rax
    call printf
.exit_main:
    mov rsp, rbp
    pop rbp
    ret