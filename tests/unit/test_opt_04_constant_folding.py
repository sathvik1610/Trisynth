import pytest
from src.ir.instructions import Instruction, OpCode
from src.optimization.constant_fold import ConstantFolding

def _opt(ir):
    return ConstantFolding().run(ir)

def test_basic_arithmetic():
    ir = [
        Instruction(OpCode.ADD, arg1=5, arg2=10, result="t0"),
        Instruction(OpCode.MUL, arg1="t0", arg2=2, result="t1")
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.MOV
    assert opt[0].arg1 == 15
    assert opt[1].opcode == OpCode.MOV
    assert opt[1].arg1 == 30

def test_branch_elimination():
    ir = [
        Instruction(OpCode.GT, arg1=10, arg2=5, result="t0"),
        Instruction(OpCode.JMP_IF_FALSE, arg1="t0", arg2="L1", result=None)
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.MOV
    assert opt[0].arg1 == 1 # True
    # Branch is dropped entirely because condition is 1 (never taken)
    assert len(opt) == 1

def test_branch_conversion():
    ir = [
        Instruction(OpCode.LT, arg1=10, arg2=5, result="t0"),
        Instruction(OpCode.JMP_IF_FALSE, arg1="t0", arg2="L1", result=None)
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.MOV
    assert opt[0].arg1 == 0 # False
    # Branch converted to unconditional JMP
    assert opt[1].opcode == OpCode.JMP
    assert opt[1].arg1 == "L1"

def test_global_constants_cross_label():
    ir = [
        Instruction(OpCode.FUNC_START, arg1="main", arg2=None, result=None),
        Instruction(OpCode.MOV, arg1=10, arg2=None, result="x"), # single assignment in entry block
        Instruction(OpCode.LABEL, arg1="L1", arg2=None, result=None),
        Instruction(OpCode.ADD, arg1="x", arg2=5, result="t0")
    ]
    opt = _opt(ir)
    assert opt[3].opcode == OpCode.MOV
    assert opt[3].arg1 == 15 # x successfully propagated across label!

def test_bug6_cross_function_leak():
    ir = [
        Instruction(OpCode.FUNC_START, arg1="main", arg2=None, result=None),
        Instruction(OpCode.MOV, arg1=10, arg2=None, result="t0"),
        Instruction(OpCode.FUNC_START, arg1="foo", arg2=None, result=None),
        Instruction(OpCode.ADD, arg1="t0", arg2=5, result="t1") # different t0
    ]
    opt = _opt(ir)
    assert opt[3].opcode == OpCode.ADD # t0 was not leaked!

def test_bug7_dominance_bypass():
    ir = [
        Instruction(OpCode.FUNC_START, arg1="main", arg2=None, result=None),
        Instruction(OpCode.LABEL, arg1="L1", arg2=None, result=None),
        Instruction(OpCode.MOV, arg1=10, arg2=None, result="x"), # single assignment NOT in entry block
        Instruction(OpCode.LABEL, arg1="L2", arg2=None, result=None),
        Instruction(OpCode.ADD, arg1="x", arg2=5, result="t0")
    ]
    opt = _opt(ir)
    assert opt[4].opcode == OpCode.ADD # x was NOT promoted to global constant
