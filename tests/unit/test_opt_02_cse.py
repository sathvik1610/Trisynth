import pytest
from src.ir.instructions import Instruction, OpCode
from src.optimization.cse import CommonSubexpressionElimination

def _opt(ir):
    return CommonSubexpressionElimination().run(ir)

def test_basic_cse():
    ir = [
        Instruction(OpCode.MUL, arg1="x", arg2="y", result="t0"),
        Instruction(OpCode.MUL, arg1="x", arg2="y", result="t1")
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.MUL
    assert opt[1].opcode == OpCode.MOV
    assert opt[1].arg1 == "t0"
    assert opt[1].result == "t1"

def test_commutative_cse():
    ir = [
        Instruction(OpCode.ADD, arg1="x", arg2="y", result="t0"),
        Instruction(OpCode.ADD, arg1="y", arg2="x", result="t1")
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.ADD
    assert opt[1].opcode == OpCode.MOV
    assert opt[1].arg1 == "t0"
    assert opt[1].result == "t1"

def test_invalidation_on_redefine():
    # Bug 5 test: arithmetic redefining a variable must invalidate old cache
    ir = [
        Instruction(OpCode.ADD, arg1="a", arg2="b", result="x"),
        Instruction(OpCode.ADD, arg1="c", arg2="d", result="x"), # redefines x
        Instruction(OpCode.ADD, arg1="a", arg2="b", result="y")  # should not CSE to x
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.ADD
    assert opt[1].opcode == OpCode.ADD
    assert opt[2].opcode == OpCode.ADD # No CSE matched because x was overwritten!
    assert opt[2].result == "y"

def test_invalidation_of_operands():
    ir = [
        Instruction(OpCode.ADD, arg1="a", arg2="b", result="t0"),
        Instruction(OpCode.MOV, arg1=5, arg2=None, result="a"), # redefines operand
        Instruction(OpCode.ADD, arg1="a", arg2="b", result="t1")
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.ADD
    assert opt[1].opcode == OpCode.MOV
    assert opt[2].opcode == OpCode.ADD # No CSE matched because operand a changed!

def test_control_flow_reset():
    ir = [
        Instruction(OpCode.ADD, arg1="a", arg2="b", result="t0"),
        Instruction(OpCode.LABEL, arg1="L1", arg2=None, result=None),
        Instruction(OpCode.ADD, arg1="a", arg2="b", result="t1")
    ]
    opt = _opt(ir)
    assert opt[0].opcode == OpCode.ADD
    assert opt[1].opcode == OpCode.LABEL
    assert opt[2].opcode == OpCode.ADD # No CSE across labels
