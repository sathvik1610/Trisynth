"""
Unit Tests for Optimization Phase (Week 6).
"""
import pytest
from src.ir.instructions import Instruction, OpCode
from src.optimization.optimizer import Optimizer
from src.optimization.constant_fold import ConstantFolding

def test_simple_constant_fold():
    # Input: ADD t0 10 20
    instr = Instruction(OpCode.ADD, arg1=10, arg2=20, result="t0")
    
    optimizer = Optimizer()
    optimizer.add_pass(ConstantFolding())
    
    optimized_ir = optimizer.optimize([instr])
    
    # Expected: MOV t0 30
    assert len(optimized_ir) == 1
    new_instr = optimized_ir[0]
    assert new_instr.opcode == OpCode.MOV
    assert new_instr.result == "t0"
    assert new_instr.arg1 == 30

def test_no_fold_variable():
    # Input: ADD t0 x 10 (x is variable, not constant)
    instr = Instruction(OpCode.ADD, arg1="x", arg2=10, result="t0")
    
    optimizer = Optimizer()
    optimizer.add_pass(ConstantFolding())
    
    optimized_ir = optimizer.optimize([instr])
    
    # Expected: No change
    assert len(optimized_ir) == 1
    assert optimized_ir[0].opcode == OpCode.ADD
    assert optimized_ir[0].arg1 == "x"

def test_mixed_optimization():
    # Input (Chain):
    # ADD t0 1 2  -> Should fold to MOV t0 3
    # SUB t1 t0 5 -> Cannot fold (t0 is var name in IR)
    
    ir = [
        Instruction(OpCode.ADD, arg1=1, arg2=2, result="t0"),
        Instruction(OpCode.SUB, arg1="t0", arg2=5, result="t1")
    ]
    
    optimizer = Optimizer()
    optimizer.add_pass(ConstantFolding())
    
    result = optimizer.optimize(ir)
    
    assert result[0].opcode == OpCode.MOV
    assert result[0].arg1 == 3
    
    assert result[1].opcode == OpCode.SUB
    # Notes: We don't propagate constants yet (Constant Propagation is separate).
    # So t0 remains t0 in the next instruction.
