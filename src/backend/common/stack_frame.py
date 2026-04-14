# This file manages the memory stack frame during execution, making sure all the variables and temporary values are stored at the right offsets.

from typing import Dict, List

class StackFrame:

       
    def __init__(self):
        # This initializes the base properties.
        self.offsets: Dict[str, int] = {}
        self.is_ref: Dict[str, bool] = {}                                                          
        self.current_offset = 0                  
        self.total_size = 0

    def allocate(self, var_name: str, size: int = 8, is_ref: bool = False):

           
        # This handles the primary logic for allocate operations.
        if var_name in self.offsets:
            return                    
            
        self.current_offset += size
        self.offsets[var_name] = self.current_offset
        self.is_ref[var_name] = is_ref

    def get_offset(self, var_name: str) -> int:
                                                                               
        # This handles the primary logic for get offset operations.
        if var_name not in self.offsets:
                                                                        
            self.allocate(var_name)
        return self.offsets[var_name]

    def is_reference(self, var_name: str) -> bool:
                                                                  
        # This handles the primary logic for is reference operations.
        return self.is_ref.get(var_name, False)

    def finalize(self):
                                           
        # This handles the primary logic for finalize operations.
        self.total_size = self._align_16(self.current_offset)

    def _align_16(self, size: int) -> int:
        # This handles the primary logic for align 16 operations.
        if size % 16 == 0:
            return size
        return size + (16 - (size % 16))
