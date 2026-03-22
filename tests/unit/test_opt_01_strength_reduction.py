import pytest
from src.ir.instructions import Instruction, OpCode
from src.optimization.strength_reduction import StrengthReduction

def _opt(ir):
    return StrengthReduction().run(ir)

def test_power_of_two_multiplication():
    ir = [
        Instruction(OpCode.MUL, arg1="x", arg2=8, result="t0"),
        Instruction(OpCode.MUL, arg1=16, arg2="y", result="t1")
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.LSHIFT
    assert opt[0].arg2 == 3
    assert opt[0].result == "t0"
    
    assert opt[1].opcode == OpCode.LSHIFT
    assert opt[1].arg2 == 4
    assert opt[1].result == "t1"

def test_power_of_two_division():
    ir = [
        Instruction(OpCode.DIV, arg1="x", arg2=4, result="t0")
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.RSHIFT
    assert opt[0].arg1 == "x"
    assert opt[0].arg2 == 2

def test_zero_identities():
    ir = [
        Instruction(OpCode.MUL, arg1="x", arg2=0, result="t0"),
        Instruction(OpCode.MUL, arg1=0, arg2="y", result="t1"),
        Instruction(OpCode.SUB, arg1="x", arg2="x", result="t2")
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.MOV and opt[0].arg1 == 0
    assert opt[1].opcode == OpCode.MOV and opt[1].arg1 == 0
    assert opt[2].opcode == OpCode.MOV and opt[2].arg1 == 0

def test_one_identities():
    ir = [
        Instruction(OpCode.MUL, arg1="x", arg2=1, result="t0"),
        Instruction(OpCode.DIV, arg1="y", arg2=1, result="t1")
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.MOV and opt[0].arg1 == "x"
    assert opt[1].opcode == OpCode.MOV and opt[1].arg1 == "y"

def test_noop_add_sub():
    ir = [
        Instruction(OpCode.ADD, arg1="x", arg2=0, result="t0"),
        Instruction(OpCode.SUB, arg1="y", arg2=0, result="t1")
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.MOV and opt[0].arg1 == "x"
    assert opt[1].opcode == OpCode.MOV and opt[1].arg1 == "y"

def test_peephole_self_assignment():
    ir = [
        Instruction(OpCode.MOV, arg1="x", arg2=None, result="x")
    ]
    opt = _opt(ir)
    assert len(opt) == 0
