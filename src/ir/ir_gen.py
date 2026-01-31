from typing import List
import src.frontend.ast as ast
from src.ir.instructions import Instruction, OpCode

class IRGenerator:
    """
    converts AST to Intermediate Representation (Three-Address Code).
    """
    def __init__(self):
        self.instructions: List[Instruction] = []
        self._temp_counter = 0
        self._label_counter = 0
        
        # Scope Management for Unique Renaming
        # Stack of dicts: {source_name: unique_ir_name}
        self.scopes = [{}] 
        self._var_counter = 0

    def generate(self, program: ast.Program) -> List[Instruction]:
        self.visit(program)
        return self.instructions

    def _new_temp(self) -> str:
        name = f"t{self._temp_counter}"
        self._temp_counter += 1
        return name

    def _new_label(self) -> str:
        name = f"L{self._label_counter}"
        self._label_counter += 1
        return name

    def _get_unique_name(self, name: str) -> str:
        """Generates a unique name for a new variable declaration."""
        unique = f"{name}_{self._var_counter}"
        self._var_counter += 1
        return unique

    def _resolve(self, name: str) -> str:
        """Resolves a source name to its current unique IR name."""
        # Search from inner-most scope to outer-most
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise Exception(f"IR Gen Error: Variable '{name}' not found in scope.")

    def _enter_scope(self):
        self.scopes.append({})

    def _exit_scope(self):
        self.scopes.pop()

    def _emit(self, opcode: OpCode, arg1=None, arg2=None, result=None):
        instr = Instruction(opcode, arg1, arg2, result)
        self.instructions.append(instr)

    def visit(self, node: ast.ASTNode) -> str:
        """
        Generic visitor. Returns the name of the variable/temp holding the result (if any).
        """
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.ASTNode):
        raise Exception(f"No visit_{type(node).__name__} method defined in IRGenerator.")

    # --- Visitor Methods ---

    def visit_Program(self, node: ast.Program):
        for decl in node.declarations:
            self.visit(decl)

    def visit_VarDecl(self, node: ast.VarDecl):
        # int x = 10; -> MOV x_N, 10
        
        # 1. Generate unique name for this declaration
        unique_name = self._get_unique_name(node.name)
        
        # 2. Register in current scope
        self.scopes[-1][node.name] = unique_name
        
        if node.initializer:
            value_src = self.visit(node.initializer)
            self._emit(OpCode.MOV, arg1=value_src, result=unique_name)
        else:
            # Optional: Emit a zero-init or just leave it. 
            # For safety/debug in IR, maybe good to know it exists? 
            # But strictly MOV is enough when assigned.
            pass

    def visit_FunctionDecl(self, node: ast.FunctionDecl):
        self._emit(OpCode.FUNC_START, arg1=node.name)
        
        self._enter_scope()
        
        # Handle parameters (register them in scope)
        for _, param_name in node.params:
            unique_name = self._get_unique_name(param_name)
            self.scopes[-1][param_name] = unique_name
            # Note: In a real compiler, we'd emit instructions to move args from registers/stack 
            # to these locals. For this IR, we assume they are set.

        # We visit the body block manually to avoid double scope entry if visit_Block does it
        # But visit_Block handles scope...
        # Let's inspect visit_Block node structure. 
        # AST FunctionDecl has 'body' which is a Block.
        # If we visit(node.body), visit_Block will enter another scope. 
        # That's fine (function scope + block scope), or we can just delegate.
        self.visit(node.body) 
        
        self._exit_scope()
        
        # Implicit return for void functions if missing
        if self.instructions[-1].opcode != OpCode.RETURN:
             self._emit(OpCode.FUNC_END, arg1=node.name)

    def visit_Block(self, node: ast.Block):
        self._enter_scope()
        for stmt in node.statements:
            self.visit(stmt)
        self._exit_scope()

    def visit_IfStmt(self, node: ast.IfStmt):
        # ... (same logic, just using visit which uses resolve) ...
        cond_temp = self.visit(node.condition)
        
        label_else = self._new_label() if node.else_branch else None
        label_end = self._new_label()

        target_false = label_else if label_else else label_end
        self._emit(OpCode.JMP_IF_FALSE, arg1=cond_temp, arg2=target_false)

        self.visit(node.then_branch)
        self._emit(OpCode.JMP, arg1=label_end)

        if node.else_branch:
            self._emit(OpCode.LABEL, arg1=label_else)
            self.visit(node.else_branch)

        self._emit(OpCode.LABEL, arg1=label_end)

    def visit_WhileStmt(self, node: ast.WhileStmt):
        label_start = self._new_label()
        label_end = self._new_label()

        self._emit(OpCode.LABEL, arg1=label_start)
        
        cond_temp = self.visit(node.condition)
        self._emit(OpCode.JMP_IF_FALSE, arg1=cond_temp, arg2=label_end)

        self.visit(node.body)
        self._emit(OpCode.JMP, arg1=label_start)

        self._emit(OpCode.LABEL, arg1=label_end)

    def visit_ReturnStmt(self, node: ast.ReturnStmt):
        val = None
        if node.value:
            val = self.visit(node.value)
        self._emit(OpCode.RETURN, arg1=val)

    def visit_PrintStmt(self, node: ast.PrintStmt):
        val = self.visit(node.expression)
        self._emit(OpCode.PRINT, arg1=val)

    def visit_ExprStmt(self, node: ast.ExprStmt):
        self.visit(node.expression)

    # --- Expressions ---

    def visit_Literal(self, node: ast.Literal) -> str:
        return node.value

    def visit_Variable(self, node: ast.Variable) -> str:
        # Resolve source name to unique IR name
        return self._resolve(node.name)

    def visit_BinaryExpr(self, node: ast.BinaryExpr) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        temp = self._new_temp()
        
        op_map = {
            'PLUS': OpCode.ADD, 'MINUS': OpCode.SUB, 
            'STAR': OpCode.MUL, 'SLASH': OpCode.DIV,
            'LT': OpCode.LT, 'GT': OpCode.GT, 'EQ': OpCode.EQ, 'NEQ': OpCode.NEQ
        }
        
        opcode = op_map.get(node.operator.name)
        if not opcode:
            raise Exception(f"IR Gen Error: Unsupported binary operator {node.operator.name}")
            
        self._emit(opcode, arg1=left, arg2=right, result=temp)
        return temp

    def visit_Assignment(self, node: ast.Assignment) -> str:
        value = self.visit(node.value)
        target_name = self._resolve(node.name) # Must exist
        self._emit(OpCode.MOV, arg1=value, result=target_name)
        return target_name
