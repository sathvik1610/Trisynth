# This scans through instructions to delete pieces of code that will never execute.

from typing import List, Set, Tuple
from src.ir.instructions import Instruction, OpCode

class DeadCodeElimination:
\
\
\
\
\
\
\
\
       
    
    def run(self, instructions: List[Instruction]) -> List[Instruction]:
\
\
           
        # This kicks off the main execution loop for this component.
        while True:
            changed, new_instructions = self._dce_pass(instructions)
            if not changed:
                break
            instructions = new_instructions
        return instructions

    def _dce_pass(self, instructions: List[Instruction]) -> Tuple[bool, List[Instruction]]:
                                                                                         
                                                                                          
                                                                             
        # This handles the primary logic for dce pass operations.
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
                                                                       
                        targeted_labels.add(instr.arg1)
                    elif instr.opcode == OpCode.JMP_IF_FALSE:
                        cond = instr.arg1
                                                                                            
                        if isinstance(cond, (int, float)) and cond != 0:
                            pass                                           
                        else:
                                                                             
                            targeted_labels.add(instr.arg2)
                            
                if instr.opcode in (OpCode.RETURN, OpCode.JMP):
                    is_reachable = False
                elif instr.opcode == OpCode.JMP_IF_FALSE:
                    cond = instr.arg1
                    if isinstance(cond, (int, float)) and cond != 0:
                        pass                                                            
                        
            if len(targeted_labels) == old_size:
                break

                                                                          
                                                                             
        reachable: List[bool] = []
        is_reachable = True
        for instr in instructions:
            if instr.opcode == OpCode.FUNC_START:
                is_reachable = True                                          
            elif instr.opcode == OpCode.LABEL:
                                                                              
                if instr.arg1 in targeted_labels:
                    is_reachable = True
                                                                                  
            reachable.append(is_reachable)
            if instr.opcode in (OpCode.RETURN, OpCode.JMP):
                is_reachable = False                                                          
        
                                                           
        for i, instr in enumerate(instructions):
            if instr.opcode in (OpCode.FUNC_START, OpCode.FUNC_END, OpCode.LABEL):
                reachable[i] = True                                                    


                                                                                 
        used_vars: Set[str] = set()
        for i, instr in enumerate(instructions):
            if not reachable[i]:
                continue
            if isinstance(instr.arg1, str):
                used_vars.add(instr.arg1)
            if isinstance(instr.arg2, str):
                used_vars.add(instr.arg2)

                                                                             
                                                    
            if instr.opcode == OpCode.ASTORE:
                if isinstance(instr.result, str):
                    used_vars.add(instr.result)

                                      
        new_instructions = []
        changed = False

        for i, instr in enumerate(instructions):
                                                                   
            if not reachable[i]:
                changed = True
                continue
            
                                                                      
            if instr.opcode in (OpCode.FUNC_START, OpCode.FUNC_END, OpCode.LABEL):
                new_instructions.append(instr)                 
                continue


                                                                           
            if self._has_side_effects(instr):
                new_instructions.append(instr)
                continue

                                                          
                                      
            if instr.result and instr.result not in used_vars:
                                     
                changed = True
                continue

            new_instructions.append(instr)

                                                           
                                                                                               
                                    
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
                    continue                     
            final_instructions.append(instr)

                                         
                                                                            
        used_labels = set()
        for instr in final_instructions:
            if instr.opcode in (OpCode.JMP, OpCode.JMP_IF_FALSE):
                label_target = instr.arg1 if instr.opcode == OpCode.JMP else instr.arg2
                used_labels.add(label_target)
                
        cleaned_instructions = []
        for instr in final_instructions:
            if instr.opcode == OpCode.LABEL and instr.arg1 not in used_labels:
                changed = True
                continue                   
            cleaned_instructions.append(instr)

        return changed, cleaned_instructions

    def _has_side_effects(self, instr: Instruction) -> bool:
\
\
           
                                   
        # This handles the primary logic for has side effects operations.
        if instr.opcode in (OpCode.LABEL, OpCode.JMP, OpCode.JMP_IF_FALSE, 
                           OpCode.FUNC_START, OpCode.FUNC_END, OpCode.RETURN):
            return True
            
                                
        if instr.opcode in (OpCode.PRINT, OpCode.CALL, OpCode.PARAM, OpCode.PARAM_REF, OpCode.LOAD_PARAM_REF, OpCode.LOAD_PARAM):
            return True
            
                                                                       
        if instr.opcode in (OpCode.ASTORE, OpCode.ARR_DECL, OpCode.ALOAD):
            return True
            
        return False
