# This acts as the coordinator that chains all of our performance optimizations together and runs them in the right sequence.

from typing import List
from src.ir.instructions import Instruction

class Optimizer:
\
\
       
    def __init__(self):
        # This initializes the base properties.
        self.passes = []

    def add_pass(self, optimization_pass):
                                                       
        # This handles the primary logic for add pass operations.
        self.passes.append(optimization_pass)

    def optimize(self, instructions: List[Instruction]) -> List[Instruction]:
\
\
\
\
\
\
\
\
           
        # This handles the primary logic for optimize operations.
        optimized_ir = instructions
        
                                                                                
                                                             
        for _ in range(10):                                        
                                                                                            
            before_str = "\n".join(str(i) for i in optimized_ir)
            
            for opt_pass in self.passes:
                optimized_ir = opt_pass.run(optimized_ir)
                
            after_str = "\n".join(str(i) for i in optimized_ir)
            if before_str == after_str:
                break
                
        return optimized_ir
