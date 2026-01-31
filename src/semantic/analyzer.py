from typing import Any
import src.frontend.ast as ast
from src.semantic.symbol_table import SymbolTable

class SemanticAnalyzer:
    """
    Performs semantic analysis on the AST.
    
    Responsibilities:
    1. Scope Resolution: Ensure variables are declared before use.
    2. Type Checking: Ensure operations are performed on compatible types.
    3. Redeclaration Check: Prevent declaring same variable twice in same scope.
    """
    def __init__(self):
        self.symbol_table = SymbolTable()

    def visit(self, node: ast.ASTNode):
        """Generic visitor dispatcher."""
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.ASTNode):
        """Fallback for nodes without a specific visitor."""
        raise Exception(f"No visit_{type(node).__name__} method defined.")

    def analyze(self, program: ast.Program):
        """Entry point for semantic analysis."""
        self.visit_Program(program)

    # --- Visitor Methods ---

    def visit_Program(self, node: ast.Program):
        for decl in node.declarations:
            self.visit(decl)

    def visit_VarDecl(self, node: ast.VarDecl):
        # 1. Check initializer type (if exists)
        if node.initializer:
            init_type = self.visit(node.initializer)
            if init_type != node.type_name:
                raise Exception(f"Type Error: Cannot assign '{init_type}' to '{node.type_name}' for variable '{node.name}'.")
        
        # 2. Define in symbol table
        self.symbol_table.define(node.name, node.type_name, category='variable')

    def visit_FunctionDecl(self, node: ast.FunctionDecl):
        # 1. Define function in CURRENT scope (for recursion/calling)
        self.symbol_table.define(node.name, node.return_type, category='function')
        
        # 2. Enter new scope for parameters and body
        self.symbol_table.enter_scope()
        
        # 3. Define parameters
        for type_name, param_name in node.params:
            self.symbol_table.define(param_name, type_name, category='variable')
            
        # 4. Visit body
        self.visit(node.body) # Block will handle scope too? No, specialized handling needed.
        # Actually, Block visitor enters a new scope.
        # But for functions, parameters and body usually share the same scope (or nested).
        # Let's say FunctionDecl parameters are in scope S1.
        # The body Block starts scope S2?
        # Standard C: Params are in the function scope. The body block technically opens a NEW inner scope?
        # Let's simplify: Params are in the function scope. The body IS the function scope logic.
        # BUT our AST `Block` defines its own scope.
        # So:
        # Scope 0: Global
        #   -> Func Decl (in Scope 0)
        #   -> Scope 1 (Params)
        #      -> Block (Scope 2)
        # This works fine.
        
        self.symbol_table.exit_scope()

    def visit_Block(self, node: ast.Block):
        self.symbol_table.enter_scope()
        for stmt in node.statements:
            self.visit(stmt)
        self.symbol_table.exit_scope()

    def visit_IfStmt(self, node: ast.IfStmt):
        cond_type = self.visit(node.condition)
        if cond_type != 'bool':
             # Allow int as condition? For now, strict bool.
             # Actually, C allows int. Let's start strict.
             # Wait, our relational ops return bool.
             pass 
             # If we want to allow int, we check compatibility. 
             # For strict design:
             if cond_type not in ('bool', 'int'):
                 raise Exception(f"Type Error: If condition must be bool or int, got '{cond_type}'.")

        self.visit(node.then_branch)
        if node.else_branch:
            self.visit(node.else_branch)

    def visit_WhileStmt(self, node: ast.WhileStmt):
        cond_type = self.visit(node.condition)
        if cond_type not in ('bool', 'int'):
            raise Exception(f"Type Error: While condition must be bool or int, got '{cond_type}'.")
        self.visit(node.body)

    def visit_ReturnStmt(self, node: ast.ReturnStmt):
        # TODO: Check against enclosing function return type.
        # Without reference to parent function, hard to check return type here.
        # We can store 'current_function_return_type' in analyzer state.
        if node.value:
            self.visit(node.value)

    def visit_PrintStmt(self, node: ast.PrintStmt):
        self.visit(node.expression)

    def visit_ExprStmt(self, node: ast.ExprStmt):
        self.visit(node.expression)

    # --- Expressions (Return Type String) ---

    def visit_Literal(self, node: ast.Literal) -> str:
        return node.type_name

    def visit_Variable(self, node: ast.Variable) -> str:
        symbol = self.symbol_table.resolve(node.name)
        if not symbol:
            raise Exception(f"Semantic Error: Undeclared variable '{node.name}'.")
        return symbol.type_name

    def visit_BinaryExpr(self, node: ast.BinaryExpr) -> str:
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        
        # Simple strict type matching
        if left_type != right_type:
            raise Exception(f"Type Error: Type mismatch in binary operation '{node.operator.name}'. Got '{left_type}' and '{right_type}'.")
        
        # Result type logic
        # Relational -> bool
        if node.operator.name in ('EQ', 'NEQ', 'LT', 'GT', 'LTE', 'GTE'):
            return 'bool'
        
        # Arithmetic -> same as operands
        return left_type

    def visit_UnaryExpr(self, node: ast.UnaryExpr) -> str:
        operand_type = self.visit(node.operand)
        return operand_type

    def visit_Assignment(self, node: ast.Assignment) -> str:
        # Check if variable exists
        symbol = self.symbol_table.resolve(node.name)
        if not symbol:
            raise Exception(f"Semantic Error: Undeclared variable '{node.name}'.")
            
        value_type = self.visit(node.value)
        
        if symbol.type_name != value_type:
            raise Exception(f"Type Error: Cannot assign '{value_type}' to '{symbol.type_name}' for variable '{node.name}'.")
            
        return value_type # Assignment evaluates to the value

    def visit_CallExpr(self, node: ast.CallExpr) -> str:
        symbol = self.symbol_table.resolve(node.callee)
        if not symbol:
            raise Exception(f"Semantic Error: User-defined function '{node.callee}' not found (Recursion/Forward decls might need 2 passes).")
        
        if symbol.category != 'function':
             raise Exception(f"Semantic Error: '{node.callee}' is not a function.")
             
        # TODO: Check argument count and types against symbol.
        # Current Symbol class only stores type_name (return type). 
        # Need to extend Symbol to store param types for full checking.
        
        return symbol.type_name
