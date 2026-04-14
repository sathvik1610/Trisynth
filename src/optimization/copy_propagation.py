# This cleans up unnecessary variable copies by redirecting to original values.

from typing import List, Dict
from src.ir.instructions import Instruction, OpCode

class CopyPropagation:
\
\
\
\
\
\
       
    
    def run(self, instructions: List[Instruction]) -> List[Instruction]:
                                                         
                                                             
        # This kicks off the main execution loop for this component.
        copies: Dict[str, str] = {}
        
        optimized = []
        from copy import copy
        for instr in instructions:
            instr = copy(instr)
            
                                                                       
                                                                    
            if instr.opcode in (OpCode.LABEL, OpCode.FUNC_START):
                copies.clear()
                
                                                         
            arg1 = instr.arg1
            if isinstance(arg1, str) and arg1 in copies:
                instr.arg1 = copies[arg1]
                
            arg2 = instr.arg2
            if isinstance(arg2, str) and arg2 in copies:
                instr.arg2 = copies[arg2]

                                                                                
                                                                                  
                                                                               
                                                                               
            if instr.opcode == OpCode.ASTORE and isinstance(instr.result, str) and instr.result in copies:
                instr.result = copies[instr.result]

                                                                             
                                                                          
                                                                          
            if instr.result and instr.opcode != OpCode.ASTORE:
                if instr.result in copies:
                    del copies[instr.result]

                                                                         
                                                                         
                                                                         
                stale = [k for k, v in copies.items() if v == instr.result]
                for k in stale:
                    del copies[k]

                                                                          
            if instr.opcode == OpCode.MOV and isinstance(instr.arg1, str):
                                                                  
                copies[instr.result] = instr.arg1
            elif instr.result and instr.opcode != OpCode.ASTORE:
                                                                          
                                                                        
                if instr.result in copies:
                    del copies[instr.result]
                    
                                                                        
                                                     
                invalid_keys = [k for k, v in copies.items() if v == instr.result]
                for k in invalid_keys:
                    del copies[k]
                    
            optimized.append(instr)
            
        return optimized