# This file simply defines all the different types of tokens we encounter while reading the source code, basically our dictionary of symbols.

from enum import Enum, auto

class TokenType(Enum):
\
\
       
                      
    INTEGER = auto()             
    FLOAT = auto()                 
    IDENTIFIER = auto()                    
    STRING = auto()                           
    CHAR = auto()                

                              
    KW_INT = auto()              
    KW_UINT32 = auto()              
    KW_FLOAT = auto()              
    KW_BOOL = auto()              
    KW_CHAR = auto()              
    KW_VOID = auto()              
    KW_CONST = auto()              
    KW_STRING = auto()              

                                     
    KW_IF = auto()              
    KW_ELSE = auto()              
    KW_WHILE = auto()              
    KW_FOR = auto()              
    KW_BREAK = auto()              
    KW_CONTINUE = auto()              
    KW_RETURN = auto()              

                                        
    KW_PRINT = auto()              
    KW_READ_INT = auto()             
    KW_TRUE = auto()              
    KW_FALSE = auto()              

                                    
    PLUS = auto()              
    MINUS = auto()             
    STAR = auto()              
    SLASH = auto()             
    MODULO = auto()            
    LSHIFT = auto()             
    RSHIFT = auto()             
    INCREMENT = auto()          
    DECREMENT = auto()          

                                    
    EQ = auto()                 
    NEQ = auto()                
    LT = auto()                
    GT = auto()                
    LTE = auto()                
    GTE = auto()                

                                 
    AND = auto()                
    OR = auto()                 
    NOT = auto()               

                        
    ASSIGN = auto()            

                        
    LPAREN = auto()            
    RPAREN = auto()            
    LBRACE = auto()            
    RBRACE = auto()            
    LBRACKET = auto()          
    RBRACKET = auto()          
    SEMICOLON = auto()         
    COMMA = auto()             

                     
    EOF = auto()                         
    ERROR = auto()                                             


class Token:
\
\
       
    def __init__(self, type: TokenType, value: str, line: int, column: int):
\
\
\
\
\
\
\
\
           
        # This initializes the base properties.
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
\
\
\
           
        # This handles the primary logic for repr operations.
        return f"Token({self.type.name}, {repr(self.value)}, {self.line}:{self.column})"

    def __eq__(self, other):
\
\
           
        # This handles the primary logic for eq operations.
        if not isinstance(other, Token):
            return False
        return (self.type == other.type and
                self.value == other.value and
                self.line == other.line and
                self.column == other.column)
