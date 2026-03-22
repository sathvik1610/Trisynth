import pytest
from src.ir.instructions import Instruction, OpCode
from src.optimization.dead_code import DeadCodeElimination

def _opt(ir):
    return DeadCodeElimination().run(ir)

def test_unused_variable_removal():
    ir = [
        Instruction(OpCode.FUNC_START, arg1="main", arg2=None, result=None),
        Instruction(OpCode.MOV, arg1=10, arg2=None, result="x"), # unused
        Instruction(OpCode.MOV, arg1=20, arg2=None, result="y"), # used
        Instruction(OpCode.PRINT, arg1="y", arg2=None, result=None)
    ]
    opt = _opt(ir)
    assert len(opt) == 3
    assert opt[1].result == "y" # x was removed

def test_unreachable_code_removal():
    ir = [
        Instruction(OpCode.FUNC_START, arg1="main", arg2=None, result=None),
        Instruction(OpCode.RETURN, arg1=None, arg2=None, result=None),
        Instruction(OpCode.PRINT, arg1=999, arg2=None, result=None) # dead code
    ]
    opt = _opt(ir)
    assert len(opt) == 2 # PRINT removed

def test_bug8_dead_label_reachability():
    ir = [
        Instruction(OpCode.FUNC_START, arg1="main", arg2=None, result=None),
        Instruction(OpCode.RETURN, arg1=None, arg2=None, result=None),
        Instruction(OpCode.LABEL, arg1="DeadLabel", arg2=None, result=None),
        Instruction(OpCode.JMP, arg1="TargetLabel", arg2=None, result=None),
        Instruction(OpCode.LABEL, arg1="TargetLabel", arg2=None, result=None),
        Instruction(OpCode.PRINT, arg1=999, arg2=None, result=None)
    ]
    opt = _opt(ir)
    # The true fixed-point Phase 0a reachability should see that DeadLabel is never targeted
    # As a result, TargetLabel is also never targeted by reachable code!
    # Therefore, PRINT 999 is dead code and should be eliminated!
    assert len(opt) == 2
    assert opt[0].opcode == OpCode.FUNC_START
    assert opt[1].opcode == OpCode.RETURN
    # It beautifully culls all dead labels and dead jump bridges!
