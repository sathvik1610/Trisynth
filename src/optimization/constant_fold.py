from typing import List, Union
from src.ir.instructions import Instruction, OpCode

class ConstantFolding:
    """
    Optimization Pass: Constant Folding
    
    Evaluates arithmetic operations with constant operands at compile time.
    IR Format handled: OP dest src1 src2
    """
    def run(self, instructions: List[Instruction]) -> List[Instruction]:
        # Dictionary to store known constant values for variables: {var_name: value}
        # Note: This simple propagation assumes linear execution and no reassignment issues 
        # within the block (SSA-like behavior or relying on unique temp names helps).
        # Since our IR uses unique names for temps, this is mostly safe for temps.
        # User variables might be reassigned (MOV x 10 ... MOV x 20), so we must be careful.
        # Current valid strategy: Update map on definition.
        constants = {}
        
        optimized = []
        for instr in instructions:
            # SAFETY GUARD: Control Flow Boundaries
            # If we hit a label or function start, we enter a new basic block (or merge point).
            # We must assume all previously known variable values are invalid because we 
            # could have arrived here from a path where they have different values.
            if instr.opcode in (OpCode.LABEL, OpCode.FUNC_START):
                constants.clear()

            # 1. Substitute operands if they are known constants
            if isinstance(instr.arg1, str) and instr.arg1 in constants:
                instr.arg1 = constants[instr.arg1]
            if isinstance(instr.arg2, str) and instr.arg2 in constants:
                instr.arg2 = constants[instr.arg2]
                
            # 2. Attempt to fold
            folded_instr = self._fold(instr)
            
            # 3. Update constants map if this instruction defines a constant
            if folded_instr.result:
                # Case A: MOV dest, constant
                if folded_instr.opcode == OpCode.MOV and self._is_constant(folded_instr.arg1):
                    constants[folded_instr.result] = folded_instr.arg1
            
            optimized.append(folded_instr)
            
        return optimized

    def _fold(self, instr: Instruction) -> Instruction:
        # We only look for arithmetic ops: ADD, SUB, MUL, DIV, MOD
        # Relational ops could also be folded (True/False or 1/0)
        if instr.opcode not in (OpCode.ADD, OpCode.SUB, OpCode.MUL, OpCode.DIV, OpCode.MOD,
                                OpCode.LSHIFT, OpCode.RSHIFT,
                                OpCode.LT, OpCode.GT, OpCode.LTE, OpCode.GTE, OpCode.EQ, OpCode.NEQ):
            return instr

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
            return instr

    def _is_constant(self, val: Union[str, int, float, None]) -> bool:
        return isinstance(val, (int, float))

    def _compute(self, opcode: OpCode, v1: Union[int, float], v2: Union[int, float]) -> Union[int, float]:
        if opcode == OpCode.ADD: return v1 + v2
        elif opcode == OpCode.SUB: return v1 - v2
        elif opcode == OpCode.MUL: return v1 * v2
        elif opcode == OpCode.DIV:
            if isinstance(v1, int) and isinstance(v2, int): return v1 // v2
            return v1 / v2
        elif opcode == OpCode.MOD: return v1 % v2
        elif opcode == OpCode.LSHIFT: return int(v1) << int(v2)
        elif opcode == OpCode.RSHIFT: return int(v1) >> int(v2)
        # Relational (Bool as Int 1/0)
        elif opcode == OpCode.LT: return 1 if v1 < v2 else 0
        elif opcode == OpCode.GT: return 1 if v1 > v2 else 0
        elif opcode == OpCode.LTE: return 1 if v1 <= v2 else 0
        elif opcode == OpCode.GTE: return 1 if v1 >= v2 else 0
        elif opcode == OpCode.EQ: return 1 if v1 == v2 else 0
        elif opcode == OpCode.NEQ: return 1 if v1 != v2 else 0
        
        return 0
