section .data
    fmt_int db "%ld", 10, 0
    fmt_str db "%s", 0
    fmt_read_int db "%ld", 0

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

; --- Function main ---
global main
main:
    push rbp
    mov rbp, rsp
    ; PRINT 12
    mov rax, 12
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PRINT 24
    mov rax, 24
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PRINT 48
    mov rax, 48
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PRINT 3
    mov rax, 3
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PRINT 1
    mov rax, 1
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