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
    
    # constant propagation enabled!
    # SUB t1 3 5 -> MOV t1 -2
    assert result[1].opcode == OpCode.MOV
    assert result[1].arg1 == -2

def test_constant_propagation():
    # Input:
    # 1. MOV x 10
    # 2. ADD y x 5  -> Should become ADD y 10 5 -> MOV y 15
    # 3. PRINT y    -> Should become PRINT 15
    
    ir = [
        Instruction(OpCode.MOV, arg1=10, result="x"),
        Instruction(OpCode.ADD, arg1="x", arg2=5, result="y"),
        Instruction(OpCode.PRINT, arg1="y")
    ]
    
    optimizer = Optimizer()
    optimizer.add_pass(ConstantFolding())
    # Note: We need DCE to see the full effect of removal, 
    # but strictly checking ConstantFolding phase:
    
    result = optimizer.optimize(ir)
    
    # 1. MOV x 10 (remains, strictly speaking, unless DCE removes it)
    # 2. MOV y 15 (folded)
    # 3. PRINT 15 (propagated)
    
    assert result[1].opcode == OpCode.MOV
    assert result[1].arg1 == 15
    
    assert result[2].opcode == OpCode.PRINT
    assert result[2].arg1 == 15

from src.optimization.dead_code import DeadCodeElimination

def test_dead_code_elimination():
    # Input:
    # 1. ADD t0 1 2   (unused)
    # 2. MOV x 100    (used by print)
    # 3. PRINT x
    
    ir = [
        Instruction(OpCode.ADD, arg1=1, arg2=2, result="t0"),
        Instruction(OpCode.MOV, arg1=100, result="x"),
        Instruction(OpCode.PRINT, arg1="x")
    ]
    
    optimizer = Optimizer()
    optimizer.add_pass(DeadCodeElimination())
    
    result = optimizer.optimize(ir)
    
    # Expected: ADD should be removed. MOV and PRINT remain.
    assert len(result) == 2
    ops = [instr.opcode for instr in result]
    assert OpCode.ADD not in ops
    assert OpCode.MOV in ops
    assert OpCode.PRINT in ops

def test_dead_code_chain():
    # Input:
    # 1. MOV a 10
    # 2. MOV b a  (b unused -> dead)
    # 3. (Implicit) After b removed, 'a' is unused -> dead
    # 4. PRINT c
    
    ir = [
        Instruction(OpCode.MOV, arg1=10, result="a"),
        Instruction(OpCode.MOV, arg1="a", result="b"),
        Instruction(OpCode.PRINT, arg1="c")
    ]
    
    optimizer = Optimizer()
    optimizer.add_pass(DeadCodeElimination())
    
    result = optimizer.optimize(ir)
    
    # Expected: Only PRINT c remains.
    assert len(result) == 1
    assert result[0].opcode == OpCode.PRINT

from src.optimization.dead_code import DeadCodeElimination

def test_dce_preserves_astore_input():
    # Regression test for ASTORE using 'result' field as input
    # t1 = 10 * 20
    # ASTORE arr 0 t1
    # t1 should NOT be removed.
    
    t1 = "t1"
    arr = "arr"
    idx = "0"
    
    instrs = [
        # Definition of t1
        Instruction(OpCode.MUL, arg1=10, arg2=20, result=t1),
        # Use of t1 in ASTORE (stored in result field)
        Instruction(OpCode.ASTORE, arg1=arr, arg2=idx, result=t1)
    ]
    
    optimizer = Optimizer()
    optimizer.add_pass(DeadCodeElimination())
    opt_instrs = optimizer.optimize(instrs)
    
    # Both instructions must remain
    assert len(opt_instrs) == 2
    assert opt_instrs[0].opcode == OpCode.MUL
    assert opt_instrs[1].opcode == OpCode.ASTORE
