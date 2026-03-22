from typing import List, Dict
from src.ir.instructions import Instruction, OpCode

class CopyPropagation:
    """
    Optimization Pass: Copy Propagation
    
    Replaces occurrences of targets of direct assignments with their values.
    If `a = b` (MOV a b), then subsequent uses of `a` can be replaced with `b`.
    This heavily cleans up flat IR by allowing DCE to later remove the redundant MOVs.
    """
    
    def run(self, instructions: List[Instruction]) -> List[Instruction]:
        # Maps a variable to the variable it is a copy of
        # e.g., if MOV a_1 t0, copies map holds {"a_1": "t0"}
        copies: Dict[str, str] = {}
        
        optimized = []
        from copy import copy
        for instr in instructions:
            instr = copy(instr)
            
            # Control flow reset
            if instr.opcode in (OpCode.LABEL, OpCode.FUNC_START):
                copies.clear()
                
            # 1. Propagate copies into arguments
            arg1 = instr.arg1
            if isinstance(arg1, str) and arg1 in copies:
                instr.arg1 = copies[arg1]
                
            arg2 = instr.arg2
            if isinstance(arg2, str) and arg2 in copies:
                instr.arg2 = copies[arg2]
                
            # For ASTORE, the 'result' field is actually the value being stored
            if instr.opcode == OpCode.ASTORE and isinstance(instr.result, str) and instr.result in copies:
                instr.result = copies[instr.result]
                
            # 2. Record new copies, or invalidate redefined variables
            if instr.opcode == OpCode.MOV and isinstance(instr.arg1, str):
                # We have: MOV dest, src_var
                copies[instr.result] = instr.arg1
            elif instr.result and instr.opcode != OpCode.ASTORE:
                # Some other operation overwrites instr.result.
                # It is no longer a copy of anything.
                if instr.result in copies:
                    del copies[instr.result]
                    
                # Also, if any variable was a copy of THIS variable, invalidate it.
                # e.g., if b = a, and now we do a = 5, b is no longer tracking the current 'a'
                invalid_keys = [k for k, v in copies.items() if v == instr.result]
                for k in invalid_keys:
                    del copies[k]
                    
            optimized.append(instr)
            
        return optimized
