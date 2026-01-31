from typing import List, Union
import math
from src.ir.instructions import Instruction, OpCode

class StrengthReduction:
    """
    Optimization Pass: Strength Reduction
    
    Replaces expensive arithmetic operations with cheaper ones.
    - MUL x, 2^k -> LSHIFT x, k
    - DIV x, 2^k -> RSHIFT x, k
    - MUL x, 0 -> MOV x, 0
    - ADD x, 0 -> MOV x, x (Identity)
    """
    def run(self, instructions: List[Instruction]) -> List[Instruction]:
        optimized = []
        for instr in instructions:
            reduced = self._reduce(instr)
            optimized.append(reduced)
        return optimized

    def _reduce(self, instr: Instruction) -> Instruction:
        if instr.opcode == OpCode.MUL:
            return self._reduce_mul(instr)
        elif instr.opcode == OpCode.DIV:
            return self._reduce_div(instr)
        elif instr.opcode == OpCode.ADD:
            return self._reduce_add(instr)
        return instr

    def _reduce_mul(self, instr: Instruction) -> Instruction:
        # MUL dest, src1, src2
        # Check if either operand is power of 2
        
        # Case 1: src2 is constant
        if self._is_power_of_two(instr.arg2):
            power = self._get_power(instr.arg2)
            # MUL x, 8 -> LSHIFT x, 3
            return Instruction(OpCode.LSHIFT, arg1=instr.arg1, arg2=power, result=instr.result)
        
        # Case 2: src1 is constant (Commutative)
        if self._is_power_of_two(instr.arg1):
            power = self._get_power(instr.arg1)
            # MUL 8, x -> LSHIFT x, 3
            return Instruction(OpCode.LSHIFT, arg1=instr.arg2, arg2=power, result=instr.result)
            
        # Case 3: Zero
        if instr.arg1 == 0 or instr.arg2 == 0:
            return Instruction(OpCode.MOV, arg1=0, result=instr.result)
            
        return instr

    def _reduce_div(self, instr: Instruction) -> Instruction:
        # DIV dest, src1, src2
        # Only optimizes if optimization divisor (arg2) is constant power of 2
        
        if self._is_power_of_two(instr.arg2):
            power = self._get_power(instr.arg2)
            # DIV x, 8 -> RSHIFT x, 3
            return Instruction(OpCode.RSHIFT, arg1=instr.arg1, arg2=power, result=instr.result)
            
        return instr
        
    def _reduce_add(self, instr: Instruction) -> Instruction:
        # ADD dest, src1, src2
        # Identity: x + 0 -> MOV dest, x
        if instr.arg1 == 0:
            return Instruction(OpCode.MOV, arg1=instr.arg2, result=instr.result)
        if instr.arg2 == 0:
            return Instruction(OpCode.MOV, arg1=instr.arg1, result=instr.result)
        return instr

    def _is_power_of_two(self, val: Union[str, int, float, None]) -> bool:
        if not isinstance(val, int) or val <= 0:
            return False
        return (val & (val - 1) == 0) and val != 0

    def _get_power(self, val: int) -> int:
        return int(math.log2(val))
