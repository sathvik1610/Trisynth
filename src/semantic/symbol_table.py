from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class Symbol:
    """
    Represents a symbol (variable or function) in the program.
    """
    name: str
    type_name: str
    category: str # 'variable' or 'function'
    is_const: bool = False

class SymbolTable:
    """
    Manages nested scopes and symbol definitions.
    
    Implementation:
    - Stack-based scope management.
    - Each scope is a dictionary mapping names to Symbols.
    """
    def __init__(self):
        self.scopes: List[Dict[str, Symbol]] = [{}] # Global scope

    def enter_scope(self):
        """Push a new scope onto the stack."""
        self.scopes.append({})

    def exit_scope(self):
        """Pop the current scope from the stack."""
        if len(self.scopes) > 1:
            self.scopes.pop()
        else:
            raise Exception("Compiler Internal Error: Cannot pop global scope.")

    def define(self, name: str, type_name: str, category: str = 'variable', is_const: bool = False):
        """
        Define a new symbol in the CURRENT scope.
        
        Raises:
            Exception: If symbol is already defined in the current scope.
        """
        current_scope = self.scopes[-1]
        if name in current_scope:
            raise Exception(f"Semantic Error: Symbol '{name}' already declared in this scope.")
        
        symbol = Symbol(name, type_name, category, is_const)
        current_scope[name] = symbol

    def resolve(self, name: str) -> Optional[Symbol]:
        """
        Look up a symbol by name, starting from current scope and moving up.
        
        Returns:
            Symbol if found, None otherwise.
        """
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
