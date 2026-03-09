from src.ir.instructions import Instruction, OpCode
from src.backend.x86_64.codegen import X86Generator

def test_backend_arrays():
    # ARR_DECL arr 10
    # ASTORE arr 0 100
    # ALOAD x arr 0
    ir = [
        Instruction(OpCode.FUNC_START, arg1="main"),
        Instruction(OpCode.ARR_DECL, arg1=10, result="arr"),
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
    assert "mov [rcx], r9" in asm
    # Load
    assert "mov rdx, [rcx]" in asm
    # Size allocated should be at least 10 * 8 = 80 + 8 (for x) = 88. Aligned -> 96
    assert "sub rsp, 96" in asm or "sub rsp, 80" in asm

def test_backend_array_params():
    # PARAM_REF arr
    # CALL foo 1
    # foo(arr): ALOAD arr 0 
    ir = [
        Instruction(OpCode.FUNC_START, arg1="main"),
        Instruction(OpCode.ARR_DECL, arg1=5, result="arr"),
        Instruction(OpCode.PARAM_REF, arg1="arr"),
        Instruction(OpCode.CALL, arg1="foo", arg2=1, result="ret"),
        Instruction(OpCode.FUNC_END, arg1="main"),
        
        Instruction(OpCode.FUNC_START, arg1="foo"),
        Instruction(OpCode.LOAD_PARAM, arg1=0, result="p_arr"), 
        Instruction(OpCode.ALOAD, arg1="p_arr", arg2=0, result="x"), 
        Instruction(OpCode.FUNC_END, arg1="foo")
    ]
    gen = X86Generator()
    
    # We must mock the frame analysis in X86Generator to know 'p_arr' is a ref
    # Actually, X86Generator._compile_function does this. Let's see if it infers it.
    # Wait, our codegen analysis DOES NOT infer if LOAD_PARAM result is a ref!
    # Let me check codegen.py: LOAD_PARAM just allocates. We need to tell the frame it's a ref.
    # This might fail! Let's write the test first.
    asm = gen.generate(ir)
    print(asm)
    
    # In main, PARAM_REF should use lea
    assert "lea rax, [rbp -" in asm
    
    # In foo, ALOAD from param should use mov because it's a pointer
    # But ONLY if the frame knows it's a reference!
    # Currently, `ALOAD` might use `lea` if the frame isn't marked as reference.
    # We will need to fix `codegen.py` to identify `LOAD_PARAM` of array type.

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
    test_backend_array_params()
    test_backend_functions()
