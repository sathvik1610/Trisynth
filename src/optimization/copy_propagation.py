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
            
            # Control flow reset — copies across function boundaries or
            # loop back-edges (labels) are not safe to carry forward
            if instr.opcode in (OpCode.LABEL, OpCode.FUNC_START):
                copies.clear()
                
            # Step 1. Propagate copies into arg1 and arg2
            arg1 = instr.arg1
            if isinstance(arg1, str) and arg1 in copies:
                instr.arg1 = copies[arg1]
                
            arg2 = instr.arg2
            if isinstance(arg2, str) and arg2 in copies:
                instr.arg2 = copies[arg2]

            # Step 2. For ASTORE, propagate into result (the VALUE field) BEFORE
            # invalidation. ASTORE reuses the result field to hold the value being
            # stored — it is NOT a write destination. Must happen before Step 3
            # or the mapping will already be deleted when we try to substitute.
            if instr.opcode == OpCode.ASTORE and isinstance(instr.result, str) and instr.result in copies:
                instr.result = copies[instr.result]

            # Step 3. Invalidate stale copies now that all args are resolved.
            # If this instruction writes to a variable that was previously
            # tracked as a copy, that mapping is now outdated — remove it.
            if instr.result and instr.opcode != OpCode.ASTORE:
                if instr.result in copies:
                    del copies[instr.result]

                # Also remove any copy whose SOURCE is the variable being
                # overwritten. e.g. if copies has {b: a} and we now write
                # to a, then b no longer reflects the current value of a.
                stale = [k for k, v in copies.items() if v == instr.result]
                for k in stale:
                    del copies[k]

            # Step 4. Record new copy relationships or invalidate further.
            if instr.opcode == OpCode.MOV and isinstance(instr.arg1, str):
                # MOV dest src_var — dest is now a copy of src_var
                copies[instr.result] = instr.arg1
            elif instr.result and instr.opcode != OpCode.ASTORE:
                # Any other op that writes to result — result is no longer
                # a copy of anything (it holds a freshly computed value)
                if instr.result in copies:
                    del copies[instr.result]
                    
                # If any variable was recorded as a copy of this result,
                # that relationship is now broken too
                invalid_keys = [k for k, v in copies.items() if v == instr.result]
                for k in invalid_keys:
                    del copies[k]
                    
            optimized.append(instr)
            
        return optimized