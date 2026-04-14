# This simplifies operations by pre-calculating constant math at compile time.

from typing import List, Union
from src.ir.instructions import Instruction, OpCode

class ConstantFolding:
\
\
\
\
\
       
    def run(self, instructions: List[Instruction]) -> List[Instruction]:
                                                                                                 
                                                                                  
        # This kicks off the main execution loop for this component.
        func_assign_counts = {}                                  
        func_entry_vars = {}                                 
        
        current_func = None
        in_entry_block = False
        
        for instr in instructions:
            if instr.opcode == OpCode.FUNC_START:
                current_func = instr.arg1
                func_assign_counts[current_func] = {}
                func_entry_vars[current_func] = set()
                in_entry_block = True
                continue
                
            if current_func is None:
                continue
                
            if instr.opcode in (OpCode.LABEL, OpCode.JMP, OpCode.JMP_IF_FALSE):
                in_entry_block = False
                
            if instr.result and instr.opcode != OpCode.ASTORE:
                func_assign_counts[current_func][instr.result] = func_assign_counts[current_func].get(instr.result, 0) + 1
                if in_entry_block:
                    func_entry_vars[current_func].add(instr.result)

        current_func = None
        global_constants = {}
        constants = {}
        
        optimized = []
        from copy import copy
        for instr in instructions:
            instr = copy(instr)
            
                                                   
            if instr.opcode == OpCode.FUNC_START:
                current_func = instr.arg1
                constants.clear()
                global_constants.clear()
            elif instr.opcode == OpCode.LABEL:
                constants.clear()
                                                         
                constants.update(global_constants)

                                                                
            if isinstance(instr.arg1, str) and instr.arg1 in constants:
                instr.arg1 = constants[instr.arg1]
            if isinstance(instr.arg2, str) and instr.arg2 in constants:
                instr.arg2 = constants[instr.arg2]
                
                                
            folded_instr = self._fold(instr)
            
                                                                            
            if folded_instr.result:
                if folded_instr.opcode == OpCode.MOV and self._is_constant(folded_instr.arg1):
                    constants[folded_instr.result] = folded_instr.arg1
                                                       
                    if current_func and func_assign_counts[current_func].get(folded_instr.result, 0) == 1:
                        if folded_instr.result in func_entry_vars[current_func]:
                            global_constants[folded_instr.result] = folded_instr.arg1
            
            optimized.append(folded_instr)
            
                                         
                                                                        
        no_dead_branches = []
        for instr in optimized:
            if instr.opcode == OpCode.JMP_IF_FALSE and self._is_constant(instr.arg1):
                if instr.arg1 != 0:
                    continue                                                                   
                else:
                                                                                                   
                    instr.opcode = OpCode.JMP
                    instr.arg1 = instr.arg2
                    instr.arg2 = None
            no_dead_branches.append(instr)
            
                                                                                 
        final_optimized = []
        for i, instr in enumerate(no_dead_branches):
            if instr.opcode == OpCode.JMP:
                                                                                         
                                              
                is_redundant = False
                for j in range(i + 1, len(no_dead_branches)):
                    next_instr = no_dead_branches[j]
                    if next_instr.opcode == OpCode.LABEL:
                        if next_instr.arg1 == instr.arg1:
                            is_redundant = True
                            break
                    else:
                        break                            
                if is_redundant:
                    continue
                    
            final_optimized.append(instr)

        return final_optimized

    def _fold(self, instr: Instruction) -> Instruction:
                                                                  
                                                                 
        # This handles the primary logic for fold operations.
        if instr.opcode not in (OpCode.ADD, OpCode.SUB, OpCode.MUL, OpCode.DIV, OpCode.MOD,
                                OpCode.LSHIFT, OpCode.RSHIFT,
                                OpCode.LT, OpCode.GT, OpCode.LTE, OpCode.GTE, OpCode.EQ, OpCode.NEQ):
            return instr

        val1 = instr.arg1
        val2 = instr.arg2
        
        if not (self._is_constant(val1) and self._is_constant(val2)):
            return instr

                                 
        try:
            result = self._compute(instr.opcode, val1, val2)
                                                         
            return Instruction(OpCode.MOV, arg1=result, result=instr.result)
        except ZeroDivisionError:
            return instr

    def _is_constant(self, val: Union[str, int, float, None]) -> bool:
        # This handles the primary logic for is constant operations.
        return isinstance(val, (int, float))

    def _compute(self, opcode: OpCode, v1: Union[int, float], v2: Union[int, float]) -> Union[int, float]:
        # This handles the primary logic for compute operations.
        if opcode == OpCode.ADD: return v1 + v2
        elif opcode == OpCode.SUB: return v1 - v2
        elif opcode == OpCode.MUL: return v1 * v2
        elif opcode == OpCode.DIV:
            if isinstance(v1, int) and isinstance(v2, int): return v1 // v2
            return v1 / v2
        elif opcode == OpCode.MOD: return v1 % v2
        elif opcode == OpCode.LSHIFT: return int(v1) << int(v2)
        elif opcode == OpCode.RSHIFT: return int(v1) >> int(v2)
                                      
        elif opcode == OpCode.LT: return 1 if v1 < v2 else 0
        elif opcode == OpCode.GT: return 1 if v1 > v2 else 0
        elif opcode == OpCode.LTE: return 1 if v1 <= v2 else 0
        elif opcode == OpCode.GTE: return 1 if v1 >= v2 else 0
        elif opcode == OpCode.EQ: return 1 if v1 == v2 else 0
        elif opcode == OpCode.NEQ: return 1 if v1 != v2 else 0
        
        return 0
