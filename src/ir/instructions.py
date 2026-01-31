from enum import Enum, auto
from dataclasses import dataclass
from typing import Union, Optional

class OpCode(Enum):
    # Data Movement
    MOV = auto()   # MOV dest, src
    
    # Arithmetic
    ADD = auto()   # ADD dest, src1, src2
    SUB = auto()   # SUB dest, src1, src2
    MUL = auto()   # MUL dest, src1, src2

    DIV = auto()   # DIV dest, src1, src2
    MOD = auto()   # MOD dest, src1, src2
    LSHIFT = auto() # LSHIFT dest, src, count
    RSHIFT = auto() # RSHIFT dest, src, count
    
    # Relational
    LT = auto()    # LT dest, src1, src2
    GT = auto()    # GT dest, src1, src2
    LTE = auto()   # LTE dest, src1, src2
    GTE = auto()   # GTE dest, src1, src2
    EQ = auto()    # EQ dest, src1, src2
    NEQ = auto()   # NEQ dest, src1, src2
    
    # Control Flow
    LABEL = auto()       # LABEL name
    JMP = auto()         # JMP label
    JMP_IF_FALSE = auto() # JMP_IF_FALSE src, label
    
    # Functions
    FUNC_START = auto()  # FUNC_START name
    FUNC_END = auto()    # FUNC_END name
    RETURN = auto()      # RETURN [val]
    # CALL dest, func_name, NumArgs. Args must be passed via PARAM before.
    CALL = auto()        
    PARAM = auto()       # PARAM val (push argument)
    LOAD_PARAM = auto()  # LOAD_PARAM index (load argument to local)
    
    # Memory / Arrays
    ALOAD = auto()     # ALOAD dest, array_name, index
    ASTORE = auto()    # ASTORE array_name, index, src_val

    # I/O
    PRINT = auto()       # PRINT src

@dataclass
class Instruction:
    """
    Represents a single IR instruction (Three-Address Code).
    """
    opcode: OpCode
    arg1: Optional[Union[str, int, float]] = None
    arg2: Optional[Union[str, int, float]] = None
    result: Optional[str] = None

    def __repr__(self):
        parts = [self.opcode.name]
        if self.result:
            parts.append(f"{self.result}")
        if self.arg1 is not None:
            parts.append(f"{self.arg1}")
        if self.arg2 is not None:
            parts.append(f"{self.arg2}")
        return " ".join(parts)
