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

    def _reduce_div(self, instr: Instruction) -> Instruction:
                              
        
                                        
        # This helps optimize slow div operations into faster equivalents.
        if instr.arg2 == 1:
            return Instruction(OpCode.MOV, arg1=instr.arg1, result=instr.result)
            
                                                                              
        if self._is_power_of_two(instr.arg2):
            power = self._get_power(instr.arg2)
                                     
            return Instruction(OpCode.RSHIFT, arg1=instr.arg1, arg2=power, result=instr.result)
            
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
