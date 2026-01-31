from src.ir.instructions import Instruction, OpCode
from src.backend.x86_64.codegen import X86Generator

def test_backend_arrays():
    # ASTORE arr 0 100
    # ALOAD x arr 0
    ir = [
        Instruction(OpCode.FUNC_START, arg1="main"),
        Instruction(OpCode.ASTORE, arg1="arr", arg2=0, result=100),
        Instruction(OpCode.ALOAD, arg1="arr", arg2=0, result="x"),
        Instruction(OpCode.FUNC_END, arg1="main")
    ]
    gen = X86Generator()
    asm = gen.generate(ir)
    print("--- Array ASM ---")
    print(asm)
    
    assert "imul rax, 8" in asm
    # Address calc
    assert "lea rcx, [rbp -" in asm
    # Store
    assert "mov [rcx], rax" in asm
    # Load
    assert "mov rdx, [rcx]" in asm

def test_backend_functions():
    # PARAM 10
    # PARAM 20
    # CALL foo 2
    ir = [
        Instruction(OpCode.FUNC_START, arg1="main"),
        Instruction(OpCode.PARAM, arg1=10),
        Instruction(OpCode.PARAM, arg1=20),
        Instruction(OpCode.CALL, arg1="foo", arg2=2, result="ret"),
        Instruction(OpCode.FUNC_END, arg1="main"),
        
        Instruction(OpCode.FUNC_START, arg1="foo"),
        Instruction(OpCode.LOAD_PARAM, arg1=0, result="p1"), # Should be 10
        Instruction(OpCode.LOAD_PARAM, arg1=1, result="p2"), # Should be 20
        Instruction(OpCode.FUNC_END, arg1="foo")
    ]
    gen = X86Generator()
    asm = gen.generate(ir)
    print("--- Function ASM ---")
    print(asm)
    
    # 1. Check Pushing (Reverse)
    # 20 first, then 10?
    # List is [10, 20]. Reversed: 20, 10.
    # Push 20 (rax=20), Push 10 (rax=10).
    # Search for pattern
    import re
    # Pattern: mov rax, 20 ... push rax ... mov rax, 10 ... push rax
    p20 = asm.find("mov rax, 20")
    push1 = asm.find("push rax", p20)
    p10 = asm.find("mov rax, 10", push1)
    push2 = asm.find("push rax", p10)
    
    assert p20 != -1 and p10 != -1
    assert p20 < push1 < p10 < push2
    
    # 2. Check Cleanup
    assert "add rsp, 16" in asm
    
    # 3. Check LOAD_PARAM
    assert "mov rax, [rbp + 16]" in asm # p1 (index 0)
    assert "mov rax, [rbp + 24]" in asm # p2 (index 1)

if __name__ == "__main__":
    test_backend_arrays()
    test_backend_functions()
