from typing import List
from src.ir.instructions import Instruction

class Optimizer:
    """
    Driver for running optimization passes on the IR.
    """
    def __init__(self):
        self.passes = []

    def add_pass(self, optimization_pass):
        """Add an optimization pass to the pipeline."""
        self.passes.append(optimization_pass)

    def optimize(self, instructions: List[Instruction]) -> List[Instruction]:
        """
        Run all registered passes on the IR instructions.
        
        Args:
            instructions: The initial list of IR instructions.
            
        Returns:
            The optimized list of IR instructions.
        """
        optimized_ir = instructions
        
        # We loop all passes until reaching a fixed point (IR no longer changes)
        # This solves "post-folding cleanup" and cascaded CSE
        for _ in range(10):  # Hard limit to prevent infinite loops
            # To compare IR changes, we need a string representation since object IDs change
            before_str = "\n".join(str(i) for i in optimized_ir)
            
            for opt_pass in self.passes:
                optimized_ir = opt_pass.run(optimized_ir)
                
            after_str = "\n".join(str(i) for i in optimized_ir)
            if before_str == after_str:
                break
                
        return optimized_ir
