from src.ir.instructions import Instruction, OpCode
from src.backend.x86_64.codegen import X86Generator

def test_backend_simple():
    # IR:
    # FUNC_START main
    # MOV x 10
    # ADD y x 5
    # PRINT y
    # FUNC_END main
    
    ir = [
        Instruction(OpCode.FUNC_START, arg1="main"),
        Instruction(OpCode.MOV, arg1=10, result="x"),
        Instruction(OpCode.ADD, arg1="x", arg2=5, result="y"),
        Instruction(OpCode.PRINT, arg1="y"),
        Instruction(OpCode.FUNC_END, arg1="main")
    ]
    
    gen = X86Generator()
    asm = gen.generate(ir)
    
    print(asm)
    
    assert "global main" in asm
    assert "sub rsp" in asm # Allocation
    assert "call printf" in asm
    assert "mov [rbp - 8], rax" in asm # x stored
    assert "mov [rbp - 16], rax" in asm # y stored

    assert "mov [rbp - 16], rax" in asm # y stored

def test_backend_loop():
    # IR:
    # FUNC_START main
    # MOV i 0
    # LABEL L0
    # LT t0 i 5
    # JMP_IF_FALSE t0 L1
    # ADD i i 1
    # JMP L0
    # LABEL L1
    # FUNC_END main
    
    ir = [
        Instruction(OpCode.FUNC_START, arg1="main"),
        Instruction(OpCode.MOV, arg1=0, result="i"),
        Instruction(OpCode.LABEL, arg1="L0"),
        Instruction(OpCode.LT, arg1="i", arg2=5, result="t0"), 
        Instruction(OpCode.JMP_IF_FALSE, arg1="t0", arg2="L1"),
        Instruction(OpCode.ADD, arg1="i", arg2=1, result="i"),
        Instruction(OpCode.JMP, arg1="L0"),
        Instruction(OpCode.LABEL, arg1="L1"),
        Instruction(OpCode.FUNC_END, arg1="main")
    ]
    
    gen = X86Generator()
    asm = gen.generate(ir)
    print(asm)
    
    assert "L0:" in asm
    assert "cmp rax, 5" in asm
    assert "setl al" in asm
    assert "jmp L0" in asm
    assert "je L1" in asm

    assert "je L1" in asm

def test_backend_math():
    # IR:
    # MOV a 100
    # LSHIFT b a 2  (100 << 2 = 400)
    # DIV c b 10    (400 / 10 = 40)
    # MOD d c 3     (40 % 3 = 1)
    
    ir = [
        Instruction(OpCode.FUNC_START, arg1="math_test"),
        Instruction(OpCode.MOV, arg1=100, result="a"),
        Instruction(OpCode.LSHIFT, arg1="a", arg2=2, result="b"),
        Instruction(OpCode.DIV, arg1="b", arg2=10, result="c"),
        Instruction(OpCode.MOD, arg1="c", arg2=3, result="d"),
        Instruction(OpCode.FUNC_END, arg1="math_test")
    ]
    
    gen = X86Generator()
    asm = gen.generate(ir)
    print(asm)
    
    assert "shl rax, 2" in asm
    assert "cqo" in asm
    assert "idiv rcx" in asm # Verify register usage for imm div
    assert "mov rax, rdx" in asm # Verify MOD takes RDX

if __name__ == "__main__":
    test_backend_simple()
    test_backend_loop()
    test_backend_math()
