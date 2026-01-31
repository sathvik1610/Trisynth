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
        for opt_pass in self.passes:
            optimized_ir = opt_pass.run(optimized_ir)
        return optimized_ir
