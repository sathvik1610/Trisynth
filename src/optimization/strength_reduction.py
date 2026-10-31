# This pass looks for slow operations like multiplication and replaces them with faster equivalents like binary shifting.

from typing import List, Union
import math
from src.ir.instructions import Instruction, OpCode

class StrengthReduction:
\
\
\
\
\
\
\
\
       
    def run(self, instructions: List[Instruction]) -> List[Instruction]:
        # This kicks off the main execution loop for this component.
        optimized = []
        for instr in instructions:
            reduced = self._reduce(instr)
            if isinstance(reduced, list):
                optimized.extend(reduced)
                continue

            if reduced.opcode == OpCode.MOV and reduced.arg1 == reduced.result:
                continue
            optimized.append(reduced)
        return optimized

    def _reduce(self, instr: Instruction) -> Instruction:
        # This handles the primary logic for reduce operations.
        if instr.opcode == OpCode.MUL:
            return self._reduce_mul(instr)
        elif instr.opcode == OpCode.DIV:
            return self._reduce_div(instr)
        elif instr.opcode == OpCode.ADD:
            return self._reduce_add(instr)
        elif instr.opcode == OpCode.SUB:
            return self._reduce_sub(instr)
        return instr

    def _reduce_mul(self, instr: Instruction) -> Instruction:
                              
                      
        # This helps optimize slow mul operations into faster equivalents.
        if instr.arg1 == 0 or instr.arg2 == 0:
            return Instruction(OpCode.MOV, arg1=0, result=instr.result)
            
                                
        if instr.arg1 == 1:
            return Instruction(OpCode.MOV, arg1=instr.arg2, result=instr.result)
        if instr.arg2 == 1:
            return Instruction(OpCode.MOV, arg1=instr.arg1, result=instr.result)

                                               
        
                                  
        if self._is_power_of_two(instr.arg2):
            power = self._get_power(instr.arg2)
                                     
            return Instruction(OpCode.LSHIFT, arg1=instr.arg1, arg2=power, result=instr.result)
        
                                                
        if self._is_power_of_two(instr.arg1):
            power = self._get_power(instr.arg1)
                                     
            return Instruction(OpCode.LSHIFT, arg1=instr.arg2, arg2=power, result=instr.result)
            
        return instr

    def _reduce_div(self, instr: Instruction) -> Union[Instruction, List[Instruction]]:



        # This helps optimize slow div operations into faster equivalents.
        if instr.arg2 == 1:
            return Instruction(OpCode.MOV, arg1=instr.arg1, result=instr.result)

        # A bare right shift rounds toward negative infinity, but division truncates toward zero.
        # So add (2^k - 1) to negative dividends first: x / 2^k == (x + (x < 0 ? 2^k - 1 : 0)) >> k.
        # Constant dividends are left for constant folding.
        if (self._is_power_of_two(instr.arg2) and instr.arg2 < (1 << 63)
                and not isinstance(instr.arg1, int)):
            power = self._get_power(instr.arg2)
            r = instr.result
            is_neg, bias, biased = f"{r}_sr_neg", f"{r}_sr_bias", f"{r}_sr_sum"
            seq = [Instruction(OpCode.LT, arg1=instr.arg1, arg2=0, result=is_neg)]
            if power == 1:
                bias = is_neg                       # 2^1 - 1 == 1, so the 0/1 flag is already the bias
            else:
                bias_hi = f"{r}_sr_hi"              # bias = (flag << k) - flag
                seq.append(Instruction(OpCode.LSHIFT, arg1=is_neg, arg2=power, result=bias_hi))
                seq.append(Instruction(OpCode.SUB, arg1=bias_hi, arg2=is_neg, result=bias))
            seq.append(Instruction(OpCode.ADD, arg1=instr.arg1, arg2=bias, result=biased))
            seq.append(Instruction(OpCode.RSHIFT, arg1=biased, arg2=power, result=instr.result))
            return seq

        return instr
        
    def _reduce_add(self, instr: Instruction) -> Instruction:
                              
                                        
        # This helps optimize slow add operations into faster equivalents.
        if instr.arg1 == 0:
            return Instruction(OpCode.MOV, arg1=instr.arg2, result=instr.result)
        if instr.arg2 == 0:
            return Instruction(OpCode.MOV, arg1=instr.arg1, result=instr.result)
        return instr

    def _reduce_sub(self, instr: Instruction) -> Instruction:
                              
                                        
        # This helps optimize slow sub operations into faster equivalents.
        if instr.arg2 == 0:
            return Instruction(OpCode.MOV, arg1=instr.arg1, result=instr.result)
                                        
        if instr.arg1 == instr.arg2 and isinstance(instr.arg1, str):
            return Instruction(OpCode.MOV, arg1=0, result=instr.result)
        return instr
        
    def _is_power_of_two(self, val: Union[str, int, float, None]) -> bool:
        # This handles the primary logic for is power of two operations.
        if not isinstance(val, int) or val <= 0:
            return False
        return (val & (val - 1) == 0) and val != 0

    def _get_power(self, val: int) -> int:
        # This handles the primary logic for get power operations.
        return int(math.log2(val))
