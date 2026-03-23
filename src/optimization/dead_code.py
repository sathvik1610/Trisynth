from typing import List, Set, Tuple
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

    def _dce_pass(self, instructions: List[Instruction]) -> Tuple[bool, List[Instruction]]:
        # Phase 0a: Collect labels that are actually jumped to by reachable instructions.
        # Key rule: JMP_IF_FALSE <non-zero-constant> label → the condition is ALWAYS true,
        # so the branch is NEVER taken → do NOT count that label as a target.
        targeted_labels: Set[str] = set()
        
        while True:
            old_size = len(targeted_labels)
            is_reachable = True
            
            for instr in instructions:
                if instr.opcode == OpCode.FUNC_START:
                    is_reachable = True
                elif instr.opcode == OpCode.LABEL:
                    if instr.arg1 in targeted_labels:
                        is_reachable = True
                        
                if is_reachable:
                    if instr.opcode == OpCode.JMP:
                        # Unconditional jump — target is always reached
                        targeted_labels.add(instr.arg1)
                    elif instr.opcode == OpCode.JMP_IF_FALSE:
                        cond = instr.arg1
                        # If condition is a constant non-zero → branch is NEVER taken → skip
                        if isinstance(cond, (int, float)) and cond != 0:
                            pass  # never jumps: don't add label to targets
                        else:
                            # Variable or zero constant → branch may be taken
                            targeted_labels.add(instr.arg2)
                            
                if instr.opcode in (OpCode.RETURN, OpCode.JMP):
                    is_reachable = False
                elif instr.opcode == OpCode.JMP_IF_FALSE:
                    cond = instr.arg1
                    if isinstance(cond, (int, float)) and cond != 0:
                        pass  # never-taken branch: execution continues, stays reachable
                        
            if len(targeted_labels) == old_size:
                break

        # Phase 0b: Linear reachability scan using the targeted-label set.
        # A LABEL only resets reachability if something actually jumps to it.
        reachable: List[bool] = []
        is_reachable = True
        for instr in instructions:
            if instr.opcode == OpCode.FUNC_START:
                is_reachable = True   # New function is always an entry point
            elif instr.opcode == OpCode.LABEL:
                # Only reset reachability if this label is genuinely jumped to
                if instr.arg1 in targeted_labels:
                    is_reachable = True
                # else: nobody jumps here → leave is_reachable as-is (stays False)
            reachable.append(is_reachable)
            if instr.opcode in (OpCode.RETURN, OpCode.JMP):
                is_reachable = False  # Everything after is unreachable until a targeted label
        
        # Phase 1: wherever you build the reachable[] array
        for i, instr in enumerate(instructions):
            if instr.opcode in (OpCode.FUNC_START, OpCode.FUNC_END, OpCode.LABEL):
                reachable[i] = True  # always mark structural instructions as reachable


        # Phase 1: Identify all used variables (only from reachable instructions)
        used_vars: Set[str] = set()
        for i, instr in enumerate(instructions):
            if not reachable[i]:
                continue
            if isinstance(instr.arg1, str):
                used_vars.add(instr.arg1)
            if isinstance(instr.arg2, str):
                used_vars.add(instr.arg2)

            # CRITICAL FIX: ASTORE uses 'result' field as the Value to store.
            # Instruction(ASTORE, arr, index, value)
            if instr.opcode == OpCode.ASTORE:
                if isinstance(instr.result, str):
                    used_vars.add(instr.result)

        # Phase 2: Filter instructions
        new_instructions = []
        changed = False

        for i, instr in enumerate(instructions):
            # Drop unreachable instructions (e.g. JMP after RETURN)
            if not reachable[i]:
                changed = True
                continue
            
            # Wherever you filter/remove instructions, add this check:
            if instr.opcode in (OpCode.FUNC_START, OpCode.FUNC_END, OpCode.LABEL):
                new_instructions.append(instr)  # ← must append
                continue


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

        # Phase 3: Peephole Cleanup (Redundant JMP Removal)
        # Often after DCE, an unconditional JMP will lead directly to the very next instruction
        # which is its target LABEL.
        final_instructions = []
        for i, instr in enumerate(new_instructions):
            if instr.opcode == OpCode.JMP:
                is_redundant = False
                for j in range(i + 1, len(new_instructions)):
                    next_instr = new_instructions[j]
                    if next_instr.opcode == OpCode.LABEL:
                        if next_instr.arg1 == instr.arg1:
                            is_redundant = True
                            break
                    else:
                        break
                if is_redundant:
                    changed = True
                    continue # Skip redundant JMP
            final_instructions.append(instr)

        # Phase 4: Dead Label Elimination
        # If no instruction jumps to a label, the label itself is dead code.
        used_labels = set()
        for instr in final_instructions:
            if instr.opcode in (OpCode.JMP, OpCode.JMP_IF_FALSE):
                label_target = instr.arg1 if instr.opcode == OpCode.JMP else instr.arg2
                used_labels.add(label_target)
                
        cleaned_instructions = []
        for instr in final_instructions:
            if instr.opcode == OpCode.LABEL and instr.arg1 not in used_labels:
                changed = True
                continue  # Drop dead label
            cleaned_instructions.append(instr)

        return changed, cleaned_instructions

    def _has_side_effects(self, instr: Instruction) -> bool:
        """
        Returns True if instruction must be kept regardless of result usage.
        """
        # Control Flow instructions
        if instr.opcode in (OpCode.LABEL, OpCode.JMP, OpCode.JMP_IF_FALSE, 
                           OpCode.FUNC_START, OpCode.FUNC_END, OpCode.RETURN):
            return True
            
        # I/O and Function Calls
        if instr.opcode in (OpCode.PRINT, OpCode.CALL, OpCode.PARAM, OpCode.PARAM_REF, OpCode.LOAD_PARAM_REF, OpCode.LOAD_PARAM):
            return True
            
        # Memory/Array operations are side effects or must be preserved
        if instr.opcode in (OpCode.ASTORE, OpCode.ARR_DECL, OpCode.ALOAD):
            return True
            
        return False
