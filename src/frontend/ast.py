from abc import ABC, abstractmethod
from typing import List, Optional, Union
from src.frontend.token_type import TokenType

class ASTNode(ABC):
    """
    Abstract base class for all Abstract Syntax Tree (AST) nodes.
    
    Each node represents a construct in the source language.
    """
    @abstractmethod
    def __repr__(self) -> str:
        """
        Returns a string representation of the node for debugging.
        """
        pass

# --- Expressions ---

class Expr(ASTNode):
    """Base class for all expression nodes (constructs that evaluate to a value)."""
    pass

class Literal(Expr):
    """
    Represents a literal value (integer, float, boolean, etc.).
    Example: 10, 3.14, true
    """
    def __init__(self, value, type_name: str):
        self.value = value
        self.type_name = type_name # 'int', 'float', 'bool'

    def __repr__(self):
        return f"Literal({self.value}:{self.type_name})"

class Variable(Expr):
    """
    Represents a variable access.
    Example: x, myVar
    """
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"Var({self.name})"

class BinaryExpr(Expr):
    """
    Represents a binary operation.
    Example: a + b, x > 10
    """
    def __init__(self, left: Expr, operator: TokenType, right: Expr):
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self):
        return f"Binary({self.left} {self.operator.name} {self.right})"

class UnaryExpr(Expr):
    """
    Represents a unary operation.
    Example: -x, !flag
    """
    def __init__(self, operator: TokenType, operand: Expr):
        self.operator = operator
        self.operand = operand

    def __repr__(self):
        return f"Unary({self.operator.name} {self.operand})"

class Assignment(Expr):
    """
    Represents a variable assignment. 
    Note: In C-like languages, assignment is often an expression.
    Example: x = 10
    """
    def __init__(self, name: str, value: Expr):
        self.name = name
        self.value = value

    def __repr__(self):
        return f"Assign({self.name} = {self.value})"

class CallExpr(Expr):
    """
    Represents a function call.
    Example: print(x), foo(1, 2)
    """
    def __init__(self, callee: str, args: List[Expr]):
        self.callee = callee
        self.args = args

    def __repr__(self):
        return f"Call({self.callee}, args={self.args})"

# --- Statements ---

class Stmt(ASTNode):
    """Base class for all statement nodes (constructs that perform an action)."""
    pass

class ExprStmt(Stmt):
    """
    Represents an expression used as a statement.
    Example: print(x);, x = 10;
    """
    def __init__(self, expression: Expr):
        self.expression = expression

    def __repr__(self):
        return f"ExprStmt({self.expression})"

class VarDecl(Stmt):
    """
    Represents a variable declaration.
    Example: int x = 10;
    """
    def __init__(self, type_name: str, name: str, initializer: Optional[Expr]):
        self.type_name = type_name
        self.name = name
        self.initializer = initializer

    def __repr__(self):
        init_str = f" = {self.initializer}" if self.initializer else ""
        return f"VarDecl({self.type_name} {self.name}{init_str})"

class Block(Stmt):
    """
    Represents a block of statements (scope).
    Example: { int x = 1; x = x + 1; }
    """
    def __init__(self, statements: List[Stmt]):
        self.statements = statements

    def __repr__(self):
        return f"Block(count={len(self.statements)})"

class IfStmt(Stmt):
    """
    Represents an if-else conditional statement.
    Example: if (x > 0) { ... } else { ... }
    """
    def __init__(self, condition: Expr, then_branch: Stmt, else_branch: Optional[Stmt] = None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def __repr__(self):
        else_str = " else ..." if self.else_branch else ""
        return f"If({self.condition} then ...{else_str})"

class WhileStmt(Stmt):
    """
    Represents a while loop.
    Example: while (x > 0) { ... }
    """
    def __init__(self, condition: Expr, body: Stmt):
        self.condition = condition
        self.body = body

    def __repr__(self):
        return f"While({self.condition} ...)"

class ReturnStmt(Stmt):
    """
    Represents a return statement.
    Example: return 0;
    """
    def __init__(self, value: Optional[Expr]):
        self.value = value

    def __repr__(self):
        return f"Return({self.value})"

class FunctionDecl(Stmt):
    """
    Represents a function declaration.
    Example: int add(int a, int b) { return a + b; }
    """
    def __init__(self, return_type: str, name: str, params: List[tuple[str, str]], body: Block):
        """
        params is a list of (type_name, param_name) tuples.
        """
        self.return_type = return_type
        self.name = name
        self.params = params
        self.body = body

    def __repr__(self):
        params_str = ", ".join([f"{t} {n}" for t, n in self.params])
        return f"Func({self.return_type} {self.name}({params_str}))"

class Program(ASTNode):
    """
    Represents the entire program (root node).
    Contains a list of global declarations (functions, variables).
    """
    def __init__(self, declarations: List[Stmt]):
        self.declarations = declarations

    def __repr__(self):
        return f"Program(decls={len(self.declarations)})"
