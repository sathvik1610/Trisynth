# This tracks variables and function names in memory for scoping and shadowing rules.

from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class Symbol:

    name: str
    type_name: str
    category: str                           
    is_const: bool = False

class SymbolTable:

       
    def __init__(self):
        # This initializes the base properties.
        self.scopes: List[Dict[str, Symbol]] = [{}]               

    def enter_scope(self):
                                              
        # This handles the primary logic for enter scope operations.
        self.scopes.append({})

    def exit_scope(self):
                                                   
        # This handles the primary logic for exit scope operations.
        if len(self.scopes) > 1:
            self.scopes.pop()
        else:
            raise Exception("Compiler Internal Error: Cannot pop global scope.")

    def define(self, name: str, type_name: str, category: str = 'variable', is_const: bool = False):

        # This registers a new identifier securely into our system.
        current_scope = self.scopes[-1]
        if name in current_scope:
            raise Exception(f"Semantic Error: Symbol '{name}' already declared in this scope.")
        
        symbol = Symbol(name, type_name, category, is_const)
        current_scope[name] = symbol

    def resolve(self, name: str) -> Optional[Symbol]:

           
        # This looks up existing definitions reliably.
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
