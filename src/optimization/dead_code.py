from typing import List, Set
from src.ir.instructions import Instruction, OpCode

class DeadCodeElimination:
    """
    Optimization Pass: Dead Code Elimination (DCE).
    
    Removes instructions that define variables which are never used later.
    Constraint: Only operates on local linear IR (Basic Block level conceptually).
    Safety: variable 'x' (user var) vs 't0' (temp). 
    For this implementation, we treat all variables typically. 
    However, we must be careful not to remove side-effects.
    """
    
    def run(self, instructions: List[Instruction]) -> List[Instruction]:
        """
        Iteratively remove dead code until convergence.
        """
        while True:
            changed, new_instructions = self._dce_pass(instructions)
            if not changed:
                break
            instructions = new_instructions
        return instructions

    def _dce_pass(self, instructions: List[Instruction]) -> (bool, List[Instruction]):
        # 1. Identify all used variables
        # We scan the entire list. If a variable appears as an ARGUMENT, it is 'used'.
        used_vars: Set[str] = set()
        
        for instr in instructions:
            if isinstance(instr.arg1, str):
                used_vars.add(instr.arg1)
            if isinstance(instr.arg2, str):
                used_vars.add(instr.arg2)
                
            # Special case: JMP_IF_FALSE arg1 is used
            # PRINT arg1 is used
            # CALL arg1 (dest) is set, but args... (not modeled in single instruction well yet, 
            # assuming args passed via param registers or stack prior to call, or implementation details).
            # For our logic: arg1 and arg2 cover most usages.
            
            # CRITICAL FIX: ASTORE uses 'result' field as the Value to store.
            # Instruction(ASTORE, arr, index, value)
            if instr.opcode == OpCode.ASTORE:
                if isinstance(instr.result, str):
                    used_vars.add(instr.result)
            
        # 2. Filter instructions
        new_instructions = []
        changed = False
        
        for instr in instructions:
            # Check if instruction has side effects or affects control flow
            if self._has_side_effects(instr):
                new_instructions.append(instr)
                continue
                
            # It's a pure instruction (defining a result).
            # Check if result is used.
            if instr.result and instr.result not in used_vars:
                # Dead code! Drop it.
                changed = True
                continue
                
            new_instructions.append(instr)
            
        return changed, new_instructions

    def _has_side_effects(self, instr: Instruction) -> bool:
        """
        Returns True if instruction must be kept regardless of result usage.
        """
        # Control Flow instructions
        if instr.opcode in (OpCode.LABEL, OpCode.JMP, OpCode.JMP_IF_FALSE, 
                           OpCode.FUNC_START, OpCode.FUNC_END, OpCode.RETURN):
            return True
            
        # I/O and Function Calls
        if instr.opcode in (OpCode.PRINT, OpCode.CALL, OpCode.PARAM):
            return True
            
        # Memory writes (Side effects)
        if instr.opcode == OpCode.ASTORE:
            return True
            
        return False
