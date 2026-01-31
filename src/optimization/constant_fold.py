from typing import List, Union
from src.ir.instructions import Instruction, OpCode

class ConstantFolding:
    """
    Optimization Pass: Constant Folding
    
    Evaluates arithmetic operations with constant operands at compile time.
    IR Format handled: OP dest src1 src2
    """
    def run(self, instructions: List[Instruction]) -> List[Instruction]:
        optimized = []
        for instr in instructions:
            folded_instr = self._fold(instr)
            optimized.append(folded_instr)
        return optimized

    def _fold(self, instr: Instruction) -> Instruction:
        # We only look for arithmetic ops: ADD, SUB, MUL, DIV
        if instr.opcode not in (OpCode.ADD, OpCode.SUB, OpCode.MUL, OpCode.DIV):
            return instr

        # Check if operands are literals (int or float)
        # Note: In our IR, operands can be strings (vars) or numbers (literals).
        # We check types explicitly.
        
        val1 = instr.arg1
        val2 = instr.arg2
        
        if not (self._is_constant(val1) and self._is_constant(val2)):
            return instr

        # Perform the calculation
        try:
            result = self._compute(instr.opcode, val1, val2)
            # Create new MOV instruction: MOV dest result
            return Instruction(OpCode.MOV, arg1=result, result=instr.result)
        except ZeroDivisionError:
            # If division by zero, we cannot fold safely at compile time (or we warn).
            # For now, leave it for runtime to crash.
            return instr

    def _is_constant(self, val: Union[str, int, float, None]) -> bool:
        return isinstance(val, (int, float))

    def _compute(self, opcode: OpCode, v1: Union[int, float], v2: Union[int, float]) -> Union[int, float]:
        if opcode == OpCode.ADD:
            return v1 + v2
        elif opcode == OpCode.SUB:
            return v1 - v2
        elif opcode == OpCode.MUL:
            return v1 * v2
        elif opcode == OpCode.DIV:
            # Use integer division if both are ints
            if isinstance(v1, int) and isinstance(v2, int):
                return v1 // v2
            return v1 / v2
        return 0 # Should not happen based on _fold check
