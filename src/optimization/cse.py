from typing import List, Dict, Tuple, Any
from src.ir.instructions import Instruction, OpCode

class CommonSubexpressionElimination:
    """
    Optimization Pass: Common Subexpression Elimination (CSE)
    
    Identifies if an expression has already been computed in the current
    basic block and replaces subsequent redundant computations with a MOV 
    from the previously computed result.
    """
    
    def run(self, instructions: List[Instruction]) -> List[Instruction]:
        # Maps a tuple of (opcode, arg1, arg2) to the variable name that holds the result
        available_exprs: Dict[Tuple[OpCode, Any, Any], str] = {}
        
        optimized = []
        for instr in instructions:
            # Control flow boundaries reset available expressions
            if instr.opcode in (OpCode.LABEL, OpCode.FUNC_START):
                available_exprs.clear()
                
            is_math = instr.opcode in (OpCode.ADD, OpCode.SUB, OpCode.MUL, OpCode.DIV, OpCode.MOD,
                                       OpCode.LSHIFT, OpCode.RSHIFT,
                                       OpCode.LT, OpCode.GT, OpCode.LTE, OpCode.GTE, OpCode.EQ, OpCode.NEQ)
            
            matched = False
            expr_key = None
            
            # Step 1: Try to match
            if is_math:
                arg1, arg2 = instr.arg1, instr.arg2
                if instr.opcode in (OpCode.ADD, OpCode.MUL, OpCode.EQ, OpCode.NEQ):
                    if str(arg1) > str(arg2):
                        arg1, arg2 = arg2, arg1
                        
                expr_key = (instr.opcode, arg1, arg2)
                
                if expr_key in available_exprs:
                    prev_result = available_exprs[expr_key]
                    optimized.append(Instruction(OpCode.MOV, arg1=prev_result, result=instr.result))
                    matched = True
                    
            if not matched:
                optimized.append(instr)

            # Step 2: Invalidate stale expressions. 
            # ANY instruction that writes to a result variable invalidates prior expressions
            # that either used that variable or claimed to compute that variable.
            if instr.result and instr.opcode != OpCode.ASTORE:
                invalid_keys = [k for k, v in available_exprs.items() 
                                if k[1] == instr.result or k[2] == instr.result or v == instr.result]
                for k in invalid_keys:
                    del available_exprs[k]

            # Step 3: Record new expressions for the future
            if is_math and not matched and instr.result:
                available_exprs[expr_key] = instr.result
                
        return optimized
