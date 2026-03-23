import pytest
from src.ir.instructions import Instruction, OpCode
from src.optimization.copy_propagation import CopyPropagation

def _opt(ir):
    return CopyPropagation().run(ir)

def test_copy_propagation():
    ir = [
        Instruction(OpCode.MOV, arg1="a", arg2=None, result="b"),
        Instruction(OpCode.ADD, arg1="b", arg2="c", result="t0"),
        Instruction(OpCode.ASTORE, arg1="arr", arg2=0, result="b")
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.MOV
    assert opt[1].opcode == OpCode.ADD
    assert opt[1].arg1 == "a" # b replaced by a
    assert opt[2].opcode == OpCode.ASTORE
    assert opt[2].result == "a" # b replaced by a (result field is value in ASTORE)

def test_copy_invalidation_on_redefine():
    ir = [
        Instruction(OpCode.MOV, arg1="a", arg2=None, result="b"),
        Instruction(OpCode.MOV, arg1=5, arg2=None, result="a"), # redefining a invalidates b
        Instruction(OpCode.ADD, arg1="b", arg2="c", result="t0")
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.MOV
    assert opt[1].opcode == OpCode.MOV
    assert opt[2].opcode == OpCode.ADD
    assert opt[2].arg1 == "b" # Not replaced because a changed!

def test_copy_invalidation_target_redefine():
    ir = [
        Instruction(OpCode.MOV, arg1="a", arg2=None, result="b"),
        Instruction(OpCode.MOV, arg1="d", arg2=None, result="b"), # redefining b invalidates a
        Instruction(OpCode.ADD, arg1="b", arg2="c", result="t0")
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.MOV
    assert opt[1].opcode == OpCode.MOV
    assert opt[2].opcode == OpCode.ADD
    assert opt[2].arg1 == "d" # Replaced by d, not a

def test_control_flow_reset():
    ir = [
        Instruction(OpCode.MOV, arg1="a", arg2=None, result="b"),
        Instruction(OpCode.LABEL, arg1="L1", arg2=None, result=None),
        Instruction(OpCode.ADD, arg1="b", arg2="c", result="t0")
    ]
    opt = _opt(ir)
    assert opt[2].arg1 == "b" # Not replaced, label cleared cache
