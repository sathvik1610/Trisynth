section .data
    fmt_int db "%ld", 10, 0
    fmt_str db "%s", 0
    fmt_read_int db "%ld", 0
    str_0 db `--- TRISYNTH FINAL SHOWCASE ---`, 0
    str_1 db `System is ready. Computing factorials block:`, 0
    str_2 db `Factorial Results:`, 0
    str_3 db `--- SHOWCASE COMPLETE ---`, 0

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
; --- Function main ---
global main
main:
    push rbp
    mov rbp, rsp
    sub rsp, 144
    ; LOAD_STR t4 --- TRISYNTH FINAL SHOWCASE ---
    lea rax, [rel str_0]
    mov [rbp - 8], rax
    ; PRINT_STR t4
    mov rax, [rbp - 8]
    mov rsi, rax
    lea rdi, [rel fmt_str]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; LOAD_STR t5 System is ready. Computing factorials block:
    lea rax, [rel str_1]
    mov [rbp - 16], rax
    ; PRINT_STR t5
    mov rax, [rbp - 16]
    mov rsi, rax
    lea rdi, [rel fmt_str]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; ARR_DECL values_4 5
    ; MOV i_5 0
    mov rax, 0
    mov [rbp - 64], rax
    ; LABEL L2
L2:
    ; LT t6 i_5 5
    mov rax, [rbp - 64]
    cmp rax, 5
    setl al
    movzx rax, al
    mov [rbp - 72], rax
    ; JMP_IF_FALSE t6 L4
    mov rax, [rbp - 72]
    cmp rax, 0
    je L4
    ; ADD t7 i_5 1
    mov rax, [rbp - 64]
    mov rbx, rax
    add rbx, 1
    mov rax, rbx
    mov [rbp - 80], rax
    ; PARAM t7
    ; CALL t8 factorial 1
    mov rax, [rbp - 80]
    push rax
    call factorial
    add rsp, 8
    mov [rbp - 88], rax
    ; ASTORE t8 values_4 i_5
    mov rax, [rbp - 64]
    imul rax, 8
    lea rcx, [rbp - 56]
    add rcx, rax
    push rcx
    mov rax, [rbp - 88]
    mov r9, rax
    pop rcx
    mov [rcx], r9
    ; ADD t9 i_5 1
    mov rax, [rbp - 64]
    mov rbx, rax
    add rbx, 1
    mov rax, rbx
    mov [rbp - 96], rax
    ; MOV i_5 t9
    mov rax, [rbp - 96]
    mov [rbp - 64], rax
    ; JMP L2
    jmp L2
    ; LABEL L4
L4:
    ; LOAD_STR t10 Factorial Results:
    lea rax, [rel str_2]
    mov [rbp - 104], rax
    ; PRINT_STR t10
    mov rax, [rbp - 104]
    mov rsi, rax
    lea rdi, [rel fmt_str]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; MOV j_7 0
    mov rax, 0
    mov [rbp - 112], rax
    ; LABEL L5
L5:
    ; LT t11 j_7 5
    mov rax, [rbp - 112]
    cmp rax, 5
    setl al
    movzx rax, al
    mov [rbp - 120], rax
    ; JMP_IF_FALSE t11 L7
    mov rax, [rbp - 120]
    cmp rax, 0
    je L7
    ; ALOAD t12 values_4 j_7
    mov rax, [rbp - 112]
    imul rax, 8
    lea rcx, [rbp - 56]
    add rcx, rax
    mov rdx, [rcx]
    mov [rbp - 128], rdx
    ; PRINT t12
    mov rax, [rbp - 128]
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; ADD t13 j_7 1
    mov rax, [rbp - 112]
    mov rbx, rax
    add rbx, 1
    mov rax, rbx
    mov [rbp - 136], rax
    ; MOV j_7 t13
    mov rax, [rbp - 136]
    mov [rbp - 112], rax
    ; JMP L5
    jmp L5
    ; LABEL L7
L7:
    ; LOAD_STR t14 --- SHOWCASE COMPLETE ---
    lea rax, [rel str_3]
    mov [rbp - 144], rax
    ; PRINT_STR t14
    mov rax, [rbp - 144]
    mov rsi, rax
    lea rdi, [rel fmt_str]
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