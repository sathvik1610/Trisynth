# This defines all internal instructions representing operations before hardware translation.

from enum import Enum, auto
from dataclasses import dataclass
from typing import Union, Optional

class OpCode(Enum):
                   
    MOV = auto()                  
    
                
    ADD = auto()                         
    SUB = auto()                         
    MUL = auto()                         

    DIV = auto()                         
    MOD = auto()                         
    LSHIFT = auto()                          
    RSHIFT = auto()                          
    
                
    LT = auto()                         
    GT = auto()                         
    LTE = auto()                         
    GTE = auto()                         
    EQ = auto()                         
    NEQ = auto()                         
    
                  
    LABEL = auto()                   
    JMP = auto()                    
    JMP_IF_FALSE = auto()                          
    
               
    FUNC_START = auto()                   
    FUNC_END = auto()                   
    RETURN = auto()                    
                                                                          
    CALL = auto()        
    PARAM = auto()                                  
    LOAD_PARAM = auto()                                             
                     
    ARR_DECL = auto()                             
    ALOAD = auto()                                    
    ASTORE = auto()                                       
    PARAM_REF = auto()                                               
    LOAD_PARAM_REF = auto()                                                                  

         
    PRINT = auto()                  
    PRINT_STR = auto()                  
    LOAD_STR = auto()                                

@dataclass
class Instruction:
       
    opcode: OpCode
    arg1: Optional[Union[str, int, float]] = None
    arg2: Optional[Union[str, int, float]] = None
    result: Optional[str] = None

    def __repr__(self):
        # This handles the primary logic for repr operations.
        parts = [self.opcode.name]
        if self.result:
            parts.append(f"{self.result}")
        if self.arg1 is not None:
            parts.append(f"{self.arg1}")
        if self.arg2 is not None:
            parts.append(f"{self.arg2}")
        return " ".join(parts)
