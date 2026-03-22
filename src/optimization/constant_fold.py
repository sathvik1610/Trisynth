from typing import List, Union
from src.ir.instructions import Instruction, OpCode

class ConstantFolding:
    """
    Optimization Pass: Constant Folding
    
    Evaluates arithmetic operations with constant operands at compile time.
    IR Format handled: OP dest src1 src2
    """
    def run(self, instructions: List[Instruction]) -> List[Instruction]:
        # Pre-scan: identify variables assigned exactly once IN THE ENTRY BLOCK of each function.
        # These are safe to propagate globally across labels within that function.
        func_assign_counts = {}  # func_name -> {var_name: count}
        func_entry_vars = {}     # func_name -> set(var_name)
        
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
            
            # SAFETY GUARD: Control Flow Boundaries
            if instr.opcode == OpCode.FUNC_START:
                current_func = instr.arg1
                constants.clear()
                global_constants.clear()
            elif instr.opcode == OpCode.LABEL:
                constants.clear()
                # Restore function-level global constants
                constants.update(global_constants)

            # 1. Substitute operands if they are known constants
            if isinstance(instr.arg1, str) and instr.arg1 in constants:
                instr.arg1 = constants[instr.arg1]
            if isinstance(instr.arg2, str) and instr.arg2 in constants:
                instr.arg2 = constants[instr.arg2]
                
            # 2. Attempt to fold
            folded_instr = self._fold(instr)
            
            # 3. Update constants map if this instruction defines a constant
            if folded_instr.result:
                if folded_instr.opcode == OpCode.MOV and self._is_constant(folded_instr.arg1):
                    constants[folded_instr.result] = folded_instr.arg1
                    # Global constant promotion if safe
                    if current_func and func_assign_counts[current_func].get(folded_instr.result, 0) == 1:
                        if folded_instr.result in func_entry_vars[current_func]:
                            global_constants[folded_instr.result] = folded_instr.arg1
            
            optimized.append(folded_instr)
            
        # 4. Peephole Branch Optimization
        # Pass 1: Remove never-taken branch, convert always-taken branch
        no_dead_branches = []
        for instr in optimized:
            if instr.opcode == OpCode.JMP_IF_FALSE and self._is_constant(instr.arg1):
                if instr.arg1 != 0:
                    continue  # Condition always True -> branch never taken -> Drop instruction
                else:
                    # Condition always False -> branch ALWAYS taken -> Convert to Unconditional JMP
                    instr.opcode = OpCode.JMP
                    instr.arg1 = instr.arg2
                    instr.arg2 = None
            no_dead_branches.append(instr)
            
        # Pass 2: Remove redundant unconditional JMP to the very next instruction
        final_optimized = []
        for i, instr in enumerate(no_dead_branches):
            if instr.opcode == OpCode.JMP:
                # Look ahead to see if the immediate next instruction is the target label
                # (skipping over other labels)
                is_redundant = False
                for j in range(i + 1, len(no_dead_branches)):
                    next_instr = no_dead_branches[j]
                    if next_instr.opcode == OpCode.LABEL:
                        if next_instr.arg1 == instr.arg1:
                            is_redundant = True
                            break
                    else:
                        break # Not a label, stop looking
                if is_redundant:
                    continue
                    
            final_optimized.append(instr)

        return final_optimized

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
