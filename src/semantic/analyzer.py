# This crawls through the syntax tree to check variable types and rules.

from typing import Any
import src.frontend.ast as ast
from src.semantic.symbol_table import SymbolTable

class SemanticAnalyzer:

       
    def __init__(self):
        # This initializes the base properties.
        self.symbol_table = SymbolTable()
        self.loop_depth = 0
        self.current_function = None                                                 
        self.symbol_table.define('readInt', 'int', category='function')

    def visit(self, node: ast.ASTNode):
                                         
        # This handles the primary logic for visit operations.
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.ASTNode):
                                                            
        # This acts as our fallback for any nodes that don't have a specific handler.
        raise Exception(f"No visit_{type(node).__name__} method defined.")

    def analyze(self, program: ast.Program):
                                                
        # This runs through all the nodes to catch errors early.
        self.visit_Program(program)

                             

    def visit_Program(self, node: ast.Program):
                                                             
        # This specifically parses and processes Program structures.
        for decl in node.declarations:
            if isinstance(decl, ast.FunctionDecl):
                try:
                    self.symbol_table.define(decl.name, decl.return_type, category='function')
                                                                                                           
                    func_sym = self.symbol_table.resolve(decl.name)
                    func_sym.param_types = [t for t, n in decl.params]
                except:
                     pass                                                                        
                                                                    
                                                                                                    
                                                                        
                                                                             
                                                                                           
                     raise

                                              
        for decl in node.declarations:
            if isinstance(decl, ast.FunctionDecl):
                                                                     
                                                           
                                                                                                 
                                                                                    
                                                                                   
                
                                                                                       
                self.symbol_table.enter_scope()
                param_types = []
                for type_name, param_name in decl.params:
                    self.symbol_table.define(param_name, type_name, category='variable')
                    param_types.append(type_name)

                                                             
                func_sym = self.symbol_table.resolve(decl.name)
                func_sym.param_types = param_types

                                                                              
                prev_func = self.current_function
                self.current_function = (decl.name, decl.return_type)
                has_return = self._body_has_return(decl.body)
                self.visit(decl.body)
                if decl.return_type != 'void' and not has_return:
                    raise Exception(f"Missing return statement in non-void function '{decl.name}'")
                self.current_function = prev_func
                self.symbol_table.exit_scope()
            else:
                self.visit(decl)

                                           
        if not self.symbol_table.resolve('main'):
            raise Exception("E004 Semantic Error: Program is missing required entry point 'main' function.")

    def visit_VarDecl(self, node: ast.VarDecl):
                                                                          
        # This specifically parses and processes VarDecl structures.
        if node.type_name in ('float', 'char'):
            raise Exception(f"E002 Semantic Error: Unsupported intrinsic type '{node.type_name}' for variable '{node.name}'.")

                                               
        if node.initializer:
            init_type = self.visit(node.initializer)
            if init_type != node.type_name:
                raise Exception(f"Type Error: Cannot assign '{init_type}' to '{node.type_name}' for variable '{node.name}'.")
        
                                   
        self.symbol_table.define(node.name, node.type_name, category='variable', is_const=node.is_const)

    def visit_FunctionDecl(self, node: ast.FunctionDecl):
                                                                     
        # This specifically parses and processes FunctionDecl structures.
        self.symbol_table.define(node.name, node.return_type, category='function')
        
                                                    
        self.symbol_table.enter_scope()
        
                              
        param_types = []
        for type_name, param_name in node.params:
            self.symbol_table.define(param_name, type_name, category='variable')
            param_types.append(type_name)
            
                                
        func_sym = self.symbol_table.resolve(node.name)
        func_sym.param_types = param_types
            
                       
        self.visit(node.body)                                                                
                                                     
                                                                                          
                                                            
                                         
                                                                                                           
                                                                                                 
                                                    
             
                         
                                     
                               
                                 
                          
        
        self.symbol_table.exit_scope()

    def visit_Block(self, node: ast.Block):
        # This specifically parses and processes Block structures.
        self.symbol_table.enter_scope()
        for stmt in node.statements:
            self.visit(stmt)
        self.symbol_table.exit_scope()

    def visit_IfStmt(self, node: ast.IfStmt):
        # This specifically parses and processes IfStmt structures.
        cond_type = self.visit(node.condition)
        if cond_type not in ('bool', 'int'):
            raise Exception(f"E002 Type Error: If condition must evaluate to bool or int, got '{cond_type}'.")

        self.visit(node.then_branch)
        if node.else_branch:
            self.visit(node.else_branch)

    def visit_WhileStmt(self, node: ast.WhileStmt):
        # This specifically parses and processes WhileStmt structures.
        self.loop_depth += 1
        cond_type = self.visit(node.condition)
        if cond_type not in ('bool', 'int'):
            raise Exception(f"Type Error: While condition must be bool or int, got '{cond_type}'.")
        self.visit(node.body)
        self.loop_depth -= 1

    def visit_ReturnStmt(self, node: ast.ReturnStmt):
        # This specifically parses and processes ReturnStmt structures.
        if not self.current_function:
            raise Exception("E003 Semantic Error: 'return' statement outside of function.")
        
        expected_ret_type = self.current_function[1]
        
        if node.value:
            actual_ret_type = self.visit(node.value)
            if expected_ret_type == 'void':
                 raise Exception(f"E002 Semantic Error: Function '{self.current_function[0]}' is void and cannot return a value.")
            if actual_ret_type != expected_ret_type:
                 raise Exception(f"E002 Type Error: Function '{self.current_function[0]}' expects return type '{expected_ret_type}', but returned '{actual_ret_type}'.")
        else:
            if expected_ret_type != 'void':
                 raise Exception(f"E002 Type Error: Function '{self.current_function[0]}' expects return type '{expected_ret_type}', but returned nothing.")

    def visit_PrintStmt(self, node: ast.PrintStmt):
        # This specifically parses and processes PrintStmt structures.
        expr_type = self.visit(node.expression)
        node.expression._semantic_type = expr_type

    def visit_ExprStmt(self, node: ast.ExprStmt):
        # This specifically parses and processes ExprStmt structures.
        self.visit(node.expression)

                                              

    def visit_Literal(self, node: ast.Literal) -> str:
        # This specifically parses and processes Literal structures.
        if node.type_name in ('float', 'char'):
             raise Exception(f"E002 Semantic Error: Literal type '{node.type_name}' is not structurally supported by the backend emission.")
        return node.type_name

    def visit_StringLiteral(self, node: ast.StringLiteral) -> str:
        # This specifically parses and processes StringLiteral structures.
        return node.type_name

    def visit_Variable(self, node: ast.Variable) -> str:
        # This specifically parses and processes Variable structures.
        symbol = self.symbol_table.resolve(node.name)
        if not symbol:
            raise Exception(f"Semantic Error: Undeclared variable '{node.name}'.")
        return symbol.type_name

    def visit_BinaryExpr(self, node: ast.BinaryExpr) -> str:
        # This specifically parses and processes BinaryExpr structures.
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        
                                     
        if left_type != right_type:
            raise Exception(f"Type Error: Type mismatch in binary operation '{node.operator.name}'. Got '{left_type}' and '{right_type}'.")
        
                                            
        if left_type == 'string' and node.operator.name not in ('EQ', 'NEQ'):
            raise Exception(f"E002 Semantic Error: Operator '{node.operator.name}' is not structurally supported on string pointers.")
        
                           
                            
        if node.operator.name in ('EQ', 'NEQ', 'LT', 'GT', 'LTE', 'GTE'):
            return 'bool'
        
                                        
        return left_type

    def visit_UnaryExpr(self, node: ast.UnaryExpr) -> str:
        # This specifically parses and processes UnaryExpr structures.
        operand_type = self.visit(node.operand)
        return operand_type

    def visit_Assignment(self, node: ast.Assignment) -> str:
                                  
        # This specifically parses and processes Assignment structures.
        symbol = self.symbol_table.resolve(node.name)
        if not symbol:
            raise Exception(f"Semantic Error: Undeclared variable '{node.name}'.")
        
        if symbol.is_const:
             raise Exception(f"Semantic Error: Cannot assign to const variable '{node.name}'.")

        value_type = self.visit(node.value)
        
        if symbol.type_name != value_type:
            raise Exception(f"Type Error: Cannot assign '{value_type}' to '{symbol.type_name}' for variable '{node.name}'.")
            
        return value_type                                    

    def visit_UnaryExpr(self, node: ast.UnaryExpr) -> str:
        # This specifically parses and processes UnaryExpr structures.
        operand_type = self.visit(node.operand)
        
                                           
        if node.operator.name in ('INCREMENT', 'DECREMENT'):
             if operand_type != 'int':
                  raise Exception(f"Type Error: Increment/Decrement requires 'int', got '{operand_type}'.")
                               
             if isinstance(node.operand, ast.Variable):
                  sym = self.symbol_table.resolve(node.operand.name)
                  if sym and sym.is_const:
                       raise Exception(f"Semantic Error: Cannot increment/decrement const variable '{node.operand.name}'.")
        
        return operand_type

    def visit_CallExpr(self, node: ast.CallExpr) -> str:
        # This specifically parses and processes CallExpr structures.
        symbol = self.symbol_table.resolve(node.callee)
        if not symbol:
            raise Exception(f"Semantic Error: User-defined function '{node.callee}' not found (Recursion/Forward decls might need 2 passes).")
        
        if symbol.category != 'function':
             raise Exception(f"Semantic Error: '{node.callee}' is not a function.")
             
                                                        
        if hasattr(symbol, 'param_types'):
            if len(node.args) != len(symbol.param_types):
                raise Exception(f"Type Error: Function '{node.callee}' expects {len(symbol.param_types)} arguments, got {len(node.args)}.")

            for i, arg in enumerate(node.args):
                arg_type = self.visit(arg)
                expected_type = symbol.param_types[i]
                param_name = None
                                                                         
                func_sym = self.symbol_table.resolve(node.callee)
                if func_sym and hasattr(func_sym, 'param_names') and i < len(func_sym.param_names):
                    param_name = func_sym.param_names[i]

                if arg_type != expected_type:
                    raise Exception(
                        f"Type Error: Argument {i+1} of '{node.callee}' expects '{expected_type}', got '{arg_type}'."
                    )

        return symbol.type_name
    def visit_ArrayDecl(self, node: ast.ArrayDecl):
                                                
                                                            
        # This specifically parses and processes ArrayDecl structures.
        array_type = node.type_name + "[]"
        self.symbol_table.define(node.name, array_type, category='variable')

    def visit_ArrayAccess(self, node: ast.ArrayAccess) -> str:
        # This specifically parses and processes ArrayAccess structures.
        symbol = self.symbol_table.resolve(node.name)
        if not symbol:
            raise Exception(f"Semantic Error: Undeclared array '{node.name}'.")

        if not symbol.type_name.endswith("[]"):
            raise Exception(f"Type Error: '{node.name}' is not an array.")

        index_type = self.visit(node.index)
        if index_type != 'int':
            raise Exception(f"Type Error: Array index must be int, got '{index_type}'.")

        return symbol.type_name[:-2]                         

    def visit_ArrayAssignment(self, node: ast.ArrayAssignment) -> str:
        # This specifically parses and processes ArrayAssignment structures.
        symbol = self.symbol_table.resolve(node.name)
        if not symbol:
            raise Exception(f"Semantic Error: Undeclared array '{node.name}'.")
            
        if not symbol.type_name.endswith("[]"):
            raise Exception(f"Type Error: '{node.name}' is not an array.")
            
        if getattr(symbol, 'is_const', False):
             raise Exception(f"E002 Semantic Error: Cannot mutate elements of const array '{node.name}'.")
            
        index_type = self.visit(node.index)
        if index_type != 'int':
            raise Exception(f"Type Error: Array index must be int, got '{index_type}'.")
             
        value_type = self.visit(node.value)
        base_type = symbol.type_name[:-2]
        
        if value_type != base_type:
            raise Exception(f"Type Error: Cannot assign '{value_type}' to '{base_type}' array element.")
            
        return value_type

    def visit_ForStmt(self, node: ast.ForStmt):
        # This specifically parses and processes ForStmt structures.
        self.symbol_table.enter_scope()
        self.loop_depth += 1
        
        if node.init:
            self.visit(node.init)
        
        if node.condition:
            cond_type = self.visit(node.condition)
            if cond_type != 'bool':
                 raise Exception(f"Type Error: For condition must be bool, got '{cond_type}'.")
        
        if node.update:
            self.visit(node.update)
            
        self.visit(node.body)
        
        self.loop_depth -= 1
        self.symbol_table.exit_scope()

    def visit_BreakStmt(self, node: ast.BreakStmt):
        # This specifically parses and processes BreakStmt structures.
        if self.loop_depth == 0:
            raise Exception("Semantic Error: 'break' outside of loop.")

    def visit_ContinueStmt(self, node: ast.ContinueStmt):
        # This specifically parses and processes ContinueStmt structures.
        if self.loop_depth == 0:
            raise Exception("Semantic Error: 'continue' outside of loop.")

    def _body_has_return(self, node) -> bool:
                                                                                  
        # This handles the primary logic for body has return operations.
        import src.frontend.ast as ast_mod
        if isinstance(node, ast_mod.Block):
            for stmt in node.statements:
                if self._body_has_return(stmt):
                    return True
            return False
        elif isinstance(node, ast_mod.ReturnStmt):
            return True
        elif isinstance(node, ast_mod.IfStmt):
                                                     
            then_returns = self._body_has_return(node.then_branch)
            else_returns = node.else_branch is not None and self._body_has_return(node.else_branch)
            return then_returns and else_returns
        elif isinstance(node, ast_mod.WhileStmt):
            return False                                      
        elif isinstance(node, ast_mod.ForStmt):
            return False
        return False

    def visit_LogicalExpr(self, node: ast.LogicalExpr) -> str:
        # This specifically parses and processes LogicalExpr structures.
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        if left_type not in ('bool', 'int') or right_type not in ('bool', 'int'):
            raise Exception(f"Type Error: Logical operators require bool operands, got '{left_type}' and '{right_type}'.")
        return 'bool'
