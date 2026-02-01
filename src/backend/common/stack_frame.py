from typing import Dict, List

class StackFrame:
    """
    Manages stack allocation for a single function.
    Architecture-agnostic.
    
    Layout:
    Base Pointer -> [Previous FP]
    + Offset     -> [Return Address/Params]
    - Offset     -> [Locals/Temporaries]
    
    Slot size is configurable (default 8 bytes).
    Total size is aligned to 16 bytes by default (common ABI requirement).
    """
    def __init__(self):
        self.offsets: Dict[str, int] = {}
        self.current_offset = 0 # Grows downwards
        self.total_size = 0

    def allocate(self, var_name: str, size: int = 8):
        """
        Allocate a slot for a variable.
        Size is in bytes (default 8 bytes).
        """
        if var_name in self.offsets:
            return # Already allocated
            
        self.current_offset += size
        self.offsets[var_name] = self.current_offset

    def get_offset(self, var_name: str) -> int:
        """Returns the offset from any Base Pointer (e.g. 8 means [FP - 8])."""
        if var_name not in self.offsets:
            # Auto-allocate if not found (Lazy allocation for temp vars)
            self.allocate(var_name)
        return self.offsets[var_name]

    def finalize(self):
        """Align frame size to 16 bytes."""
        self.total_size = self._align_16(self.current_offset)

    def _align_16(self, size: int) -> int:
        if size % 16 == 0:
            return size
        return size + (16 - (size % 16))
