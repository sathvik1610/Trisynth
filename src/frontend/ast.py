# This defines all structural building blocks for the abstract syntax tree.

from abc import ABC, abstractmethod
from typing import List, Optional, Union
from src.frontend.token_type import TokenType

class ASTNode(ABC):
\
\
\
\
       
    @abstractmethod
    def __repr__(self) -> str:
\
\
           
        # This handles the primary logic for repr operations.
        pass

                     

class Expr(ASTNode):
                                                                                    
    pass

class Literal(Expr):
\
\
\
       
    def __init__(self, value, type_name: str):
        # This initializes the base properties.
        self.value = value
        self.type_name = type_name                         

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"Literal({self.value}:{self.type_name})"

class StringLiteral(Expr):
\
\
\
       
    def __init__(self, value: str):
        # This initializes the base properties.
        self.value = value
        self.type_name = "string"

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"StringLiteral(\"{self.value}\")"

class Variable(Expr):
\
\
\
       
    def __init__(self, name: str):
        # This initializes the base properties.
        self.name = name

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"Var({self.name})"

class ArrayAccess(Expr):
\
\
\
       
    def __init__(self, name: str, index: Expr):
        # This initializes the base properties.
        self.name = name
        self.index = index

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"ArrayAccess({self.name}[{self.index}])"

class BinaryExpr(Expr):
\
\
\
       
    def __init__(self, left: Expr, operator: TokenType, right: Expr):
        # This initializes the base properties.
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"Binary({self.left} {self.operator.name} {self.right})"

class UnaryExpr(Expr):
\
\
\
       
    def __init__(self, operator: TokenType, operand: Expr):
        # This initializes the base properties.
        self.operator = operator
        self.operand = operand

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"Unary({self.operator.name} {self.operand})"

class LogicalExpr(Expr):
\
\
\
       
    def __init__(self, left: Expr, operator: TokenType, right: Expr):
        # This initializes the base properties.
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"Logic({self.left} {self.operator.name} {self.right})"

class Assignment(Expr):
\
\
\
\
       
    def __init__(self, name: str, value: Expr):
        # This initializes the base properties.
        self.name = name
        self.value = value

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"Assign({self.name} = {self.value})"

class ArrayAssignment(Expr):
\
\
\
       
    def __init__(self, name: str, index: Expr, value: Expr):
        # This initializes the base properties.
        self.name = name
        self.index = index
        self.value = value

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"ArrayAssign({self.name}[{self.index}] = {self.value})"

class CallExpr(Expr):
\
\
\
       
    def __init__(self, callee: str, args: List[Expr]):
        # This initializes the base properties.
        self.callee = callee
        self.args = args

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"Call({self.callee}, args={self.args})"

                    

class Stmt(ASTNode):
                                                                                 
    pass

class ExprStmt(Stmt):
\
\
\
       
    def __init__(self, expression: Expr):
        # This initializes the base properties.
        self.expression = expression

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"ExprStmt({self.expression})"

class PrintStmt(Stmt):
\
\
\
       
    def __init__(self, expression: Expr):
        # This initializes the base properties.
        self.expression = expression

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"Print({self.expression})"

class VarDecl(Stmt):
\
\
\
       
    def __init__(self, type_name: str, name: str, initializer: Optional[Expr], is_const: bool = False):
        # This initializes the base properties.
        self.type_name = type_name
        self.name = name
        self.initializer = initializer
        self.is_const = is_const

    def __repr__(self):
        # This handles the primary logic for repr operations.
        init_str = f" = {self.initializer}" if self.initializer else ""
        const_str = "const " if self.is_const else ""
        return f"VarDecl({const_str}{self.type_name} {self.name}{init_str})"

class Block(Stmt):
\
\
\
       
    def __init__(self, statements: List[Stmt]):
        # This initializes the base properties.
        self.statements = statements

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"Block(count={len(self.statements)})"

class IfStmt(Stmt):
\
\
\
       
    def __init__(self, condition: Expr, then_branch: Stmt, else_branch: Optional[Stmt] = None):
        # This initializes the base properties.
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def __repr__(self):
        # This handles the primary logic for repr operations.
        else_str = " else ..." if self.else_branch else ""
        return f"If({self.condition} then ...{else_str})"

class WhileStmt(Stmt):
\
\
\
       
    def __init__(self, condition: Expr, body: Stmt):
        # This initializes the base properties.
        self.condition = condition
        self.body = body

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"While({self.condition} ...)"

class WhileStmt(Stmt):
\
\
\
       
    def __init__(self, condition: Expr, body: Stmt):
        # This initializes the base properties.
        self.condition = condition
        self.body = body

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"While({self.condition} ...)"

class ForStmt(Stmt):
\
\
\
       
    def __init__(self, init: Optional[Stmt], condition: Optional[Expr], update: Optional[Expr], body: Stmt):
        # This initializes the base properties.
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"For(init={self.init}, cond={self.condition}, upd={self.update} ...)"

class BreakStmt(Stmt):
                        # This handles the primary logic for repr operations.
    def __repr__(self): return "Break"

class ContinueStmt(Stmt):
                        # This handles the primary logic for repr operations.
    def __repr__(self): return "Continue"

class ReturnStmt(Stmt):
\
\
\
       
    def __init__(self, value: Optional[Expr]):
        # This initializes the base properties.
        self.value = value

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"Return({self.value})"

class ArrayDecl(Stmt):
\
\
\
       
    def __init__(self, type_name: str, name: str, size: int):
        # This initializes the base properties.
        self.type_name = type_name
        self.name = name
        self.size = size

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"ArrayDecl({self.type_name} {self.name}[{self.size}])"

class FunctionDecl(Stmt):
\
\
\
       
    def __init__(self, return_type: str, name: str, params: List[tuple[str, str]], body: Block):
\
\
           
        # This initializes the base properties.
        self.return_type = return_type
        self.name = name
        self.params = params
        self.body = body

    def __repr__(self):
        # This handles the primary logic for repr operations.
        params_str = ", ".join([f"{t} {n}" for t, n in self.params])
        return f"Func({self.return_type} {self.name}({params_str}))"

class Program(ASTNode):
\
\
\
       
    def __init__(self, declarations: List[Stmt]):
        # This initializes the base properties.
        self.declarations = declarations

    def __repr__(self):
        # This handles the primary logic for repr operations.
        return f"Program(decls={len(self.declarations)})"
