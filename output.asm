section .data
    fmt_int db "%ld", 10, 0
    fmt_str db "%s", 0

section .text
    extern printf
    extern scanf

; --- Function main ---
global main
main:
    push rbp
    mov rbp, rsp
    ; PRINT 205
    mov rax, 205
    mov rsi, rax
    lea rdi, [rel fmt_int]
    xor rax, rax
    mov rbx, rsp
    and rsp, -16
    call printf
    mov rsp, rbx
    ; PRINT 210
    mov rax, 210
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