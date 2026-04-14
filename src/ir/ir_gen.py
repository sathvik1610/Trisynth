# This is where the magic of turning the raw syntax tree into a flat sequence of intermediate instructions happens. We walk the tree and generate the lower-level operations.

from typing import List, Union
import src.frontend.ast as ast
from src.ir.instructions import Instruction, OpCode

class IRGenerator:

    def __init__(self):
        # This initializes the base properties.
        self.instructions: List[Instruction] = []
        self._temp_counter = 0
        self._label_counter = 0

        self.scopes = [{}]
        self._var_counter = 0

                                                                                   
        self._array_names: set = set()

                                               
        self.loop_stack = []

    def generate(self, program: ast.Program) -> List[Instruction]:
        # This takes the parsed data and spits out the actual generated implementation.
        self.visit(program)
        return self.instructions

    def _new_temp(self) -> str:
        # This handles the primary logic for new temp operations.
        name = f"t{self._temp_counter}"
        self._temp_counter += 1
        return name

    def _new_label(self) -> str:
        # This handles the primary logic for new label operations.
        name = f"L{self._label_counter}"
        self._label_counter += 1
        return name

    def _get_unique_name(self, name: str) -> str:
                                                                     
        # This handles the primary logic for get unique name operations.
        unique = f"{name}_{self._var_counter}"
        self._var_counter += 1
        return unique

    def _resolve(self, name: str) -> str:
                                                                   
                                                    
        # This handles the primary logic for resolve operations.
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise Exception(f"IR Gen Error: Variable '{name}' not found in scope.")

    def _enter_scope(self):
        # This handles the primary logic for enter scope operations.
        self.scopes.append({})

    def _exit_scope(self):
        # This handles the primary logic for exit scope operations.
        self.scopes.pop()

    def _emit(self, opcode: OpCode, arg1=None, arg2=None, result=None):
        # This handles the primary logic for emit operations.
        instr = Instruction(opcode, arg1, arg2, result)
        self.instructions.append(instr)

    def visit(self, node: ast.ASTNode) -> Union[str, int, float]:

        # This handles the primary logic for visit operations.
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.ASTNode):
        # This acts as our fallback for any nodes that don't have a specific handler.
        raise Exception(f"No visit_{type(node).__name__} method defined in IRGenerator.")


    def visit_Program(self, node: ast.Program):
        # This specifically parses and processes Program structures.
        for decl in node.declarations:
            self.visit(decl)

    def visit_VarDecl(self, node: ast.VarDecl):
                                    
        # This specifically parses and processes VarDecl structures.
        unique_name = self._get_unique_name(node.name)
        self.scopes[-1][node.name] = unique_name
        
        if node.initializer:
            value_src = self.visit(node.initializer)
            self._emit(OpCode.MOV, arg1=value_src, result=unique_name)

    def visit_ArrayDecl(self, node: ast.ArrayDecl):
                                          
        # This specifically parses and processes ArrayDecl structures.
        unique_name = self._get_unique_name(node.name)
        self.scopes[-1][node.name] = unique_name
        self._array_names.add(unique_name)                                               
        self._emit(OpCode.ARR_DECL, arg1=node.size, result=unique_name)

    def visit_FunctionDecl(self, node: ast.FunctionDecl):
        # This specifically parses and processes FunctionDecl structures.
        self._emit(OpCode.FUNC_START, arg1=node.name)
        self._enter_scope()
        
        for i, (type_name, param_name) in enumerate(node.params):
            unique_name = self._get_unique_name(param_name)
            self.scopes[-1][param_name] = unique_name
            if type_name.endswith("[]"):
                self._emit(OpCode.LOAD_PARAM_REF, arg1=i, result=unique_name)
            else:
                self._emit(OpCode.LOAD_PARAM, arg1=i, result=unique_name)

        self.visit(node.body)
        self._exit_scope()
        
        self._emit(OpCode.FUNC_END, arg1=node.name)                               

    def visit_Block(self, node: ast.Block):
        # This specifically parses and processes Block structures.
        self._enter_scope()
        for stmt in node.statements:
            self.visit(stmt)
        self._exit_scope()

    def visit_IfStmt(self, node: ast.IfStmt):
        # This specifically parses and processes IfStmt structures.
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
        # This specifically parses and processes WhileStmt structures.
        label_start = self._new_label()
        label_end = self._new_label()

        self.loop_stack.append((label_start, label_end))

        self._emit(OpCode.LABEL, arg1=label_start)
        cond_temp = self.visit(node.condition)
        self._emit(OpCode.JMP_IF_FALSE, arg1=cond_temp, arg2=label_end)

        self.visit(node.body)
        self._emit(OpCode.JMP, arg1=label_start)

        self._emit(OpCode.LABEL, arg1=label_end)
        self.loop_stack.pop()


    def visit_ForStmt(self, node: ast.ForStmt):

        # This specifically parses and processes ForStmt structures.
        self._enter_scope()
        
        if node.init:
            self.visit(node.init)                   

        label_start = self._new_label()                  
        label_update = self._new_label()            
        label_end = self._new_label()         

        self.loop_stack.append((label_update, label_end))

        self._emit(OpCode.LABEL, arg1=label_start)
        
        if node.condition:
            cond_temp = self.visit(node.condition)
            self._emit(OpCode.JMP_IF_FALSE, arg1=cond_temp, arg2=label_end)
        
        self.visit(node.body)

        self._emit(OpCode.LABEL, arg1=label_update)
        if node.update:
            self.visit(node.update)
        
        self._emit(OpCode.JMP, arg1=label_start)
        
        self._emit(OpCode.LABEL, arg1=label_end)
        
        self.loop_stack.pop()
        self._exit_scope()

    def visit_BreakStmt(self, node: ast.BreakStmt):
        # This specifically parses and processes BreakStmt structures.
        if not self.loop_stack:
            raise Exception("IR Gen Error: Break outside loop.")
        _, label_break = self.loop_stack[-1]
        self._emit(OpCode.JMP, arg1=label_break)

    def visit_ContinueStmt(self, node: ast.ContinueStmt):
        # This specifically parses and processes ContinueStmt structures.
        if not self.loop_stack:
            raise Exception("IR Gen Error: Continue outside loop.")
        label_continue, _ = self.loop_stack[-1]
        self._emit(OpCode.JMP, arg1=label_continue)

    def visit_ReturnStmt(self, node: ast.ReturnStmt):
        # This specifically parses and processes ReturnStmt structures.
        val = None
        if node.value:
            val = self.visit(node.value)
        self._emit(OpCode.RETURN, arg1=val)

    def visit_PrintStmt(self, node: ast.PrintStmt):
        # This specifically parses and processes PrintStmt structures.
        val = self.visit(node.expression)
        expr_type = getattr(node.expression, '_semantic_type', None)
        if expr_type == 'string' or isinstance(node.expression, ast.StringLiteral):
            self._emit(OpCode.PRINT_STR, arg1=val)
        else:
            self._emit(OpCode.PRINT, arg1=val)

    def visit_ExprStmt(self, node: ast.ExprStmt):
        # This specifically parses and processes ExprStmt structures.
        self.visit(node.expression)

                         

    def visit_Literal(self, node: ast.Literal) -> Union[str, int, float]:
        # This specifically parses and processes Literal structures.
        if isinstance(node.value, bool):
            return 1 if node.value else 0
        return node.value

    def visit_StringLiteral(self, node: ast.StringLiteral) -> str:
        # This specifically parses and processes StringLiteral structures.
        temp = self._new_temp()
        self._emit(OpCode.LOAD_STR, arg1=node.value, result=temp)
        return temp

    def visit_Variable(self, node: ast.Variable) -> str:
        # This specifically parses and processes Variable structures.
        return self._resolve(node.name)
        
    def visit_ArrayAccess(self, node: ast.ArrayAccess) -> str:
        # This specifically parses and processes ArrayAccess structures.
        array_name = self._resolve(node.name)
        index_val = self.visit(node.index)
        result = self._new_temp()
        self._emit(OpCode.ALOAD, arg1=array_name, arg2=index_val, result=result)
        return result

    def visit_ArrayAssignment(self, node: ast.ArrayAssignment) -> str:
        # This specifically parses and processes ArrayAssignment structures.
        array_name = self._resolve(node.name)
        index_val = self.visit(node.index)
        value_val = self.visit(node.value)
        self._emit(OpCode.ASTORE, arg1=array_name, arg2=index_val, result=value_val)                                                     
        return value_val

    def visit_CallExpr(self, node: ast.CallExpr) -> str:
                            
        # This specifically parses and processes CallExpr structures.
        arg_info = []                         
        for arg in node.args:
                                                                                      
            if isinstance(arg, ast.Variable):
                resolved = self._resolve(arg.name)
                if resolved in self._array_names:
                    arg_info.append((resolved, True))
                else:
                    arg_info.append((resolved, False))
            else:
                arg_info.append((self.visit(arg), False))
            
                                             
        for temp_name, is_array in arg_info:
            if is_array:
                self._emit(OpCode.PARAM_REF, arg1=temp_name)
            else:
                self._emit(OpCode.PARAM, arg1=temp_name)
            
        result = self._new_temp()
                                            
        self._emit(OpCode.CALL, arg1=node.callee, arg2=len(node.args), result=result)
        return result

    def visit_LogicalExpr(self, node: ast.LogicalExpr) -> str:

        # This specifically parses and processes LogicalExpr structures.
        label_true = self._new_label()
        label_false = self._new_label()
        label_end = self._new_label()
        
        left = self.visit(node.left)
        
        if node.operator.name == 'AND':

             result = self._new_temp()
             self._emit(OpCode.MOV, arg1=0, result=result)
             self._emit(OpCode.JMP_IF_FALSE, arg1=left, arg2=label_end)
             
             right = self.visit(node.right)
             self._emit(OpCode.JMP_IF_FALSE, arg1=right, arg2=label_end)
             
             self._emit(OpCode.MOV, arg1=1, result=result)
             self._emit(OpCode.LABEL, arg1=label_end)
             return result
             
        elif node.operator.name == 'OR':

             result = self._new_temp()
             self._emit(OpCode.MOV, arg1=1, result=result)
             
             label_check_right = self._new_label()
             label_set_false = self._new_label()
             
                                                     
             self._emit(OpCode.JMP_IF_FALSE, arg1=left, arg2=label_check_right)
                                                        
             self._emit(OpCode.JMP, arg1=label_end)
             
             self._emit(OpCode.LABEL, arg1=label_check_right)
             right = self.visit(node.right)
             self._emit(OpCode.JMP_IF_FALSE, arg1=right, arg2=label_set_false)
                                                         
             self._emit(OpCode.JMP, arg1=label_end)
             
             self._emit(OpCode.LABEL, arg1=label_set_false)
             self._emit(OpCode.MOV, arg1=0, result=result)
             
             self._emit(OpCode.LABEL, arg1=label_end)
             return result
             
        raise Exception(f"IR Gen Error: Unknown logical op {node.operator.name}")

    def visit_BinaryExpr(self, node: ast.BinaryExpr) -> str:
        # This specifically parses and processes BinaryExpr structures.
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        temp = self._new_temp()
        
        op_map = {
            'PLUS': OpCode.ADD, 'MINUS': OpCode.SUB, 
            'STAR': OpCode.MUL, 'SLASH': OpCode.DIV, 'MODULO': OpCode.MOD,
            'LT': OpCode.LT, 'GT': OpCode.GT, 'LTE': OpCode.LTE, 'GTE': OpCode.GTE,
            'EQ': OpCode.EQ, 'NEQ': OpCode.NEQ,
            'LSHIFT': OpCode.LSHIFT, 'RSHIFT': OpCode.RSHIFT
        }
        
        opcode = op_map.get(node.operator.name)
        if not opcode:
            raise Exception(f"IR Gen Error: Unsupported binary operator {node.operator.name}")
            
        self._emit(opcode, arg1=left, arg2=right, result=temp)

        return temp

    def visit_UnaryExpr(self, node: ast.UnaryExpr) -> str:
        # This specifically parses and processes UnaryExpr structures.
        if node.operator.name == 'MINUS':
            operand = self.visit(node.operand)
            result = self._new_temp()
                         
            self._emit(OpCode.SUB, arg1=0, arg2=operand, result=result)
            return result
        elif node.operator.name == 'NOT':
                                         
             operand = self.visit(node.operand)
             result = self._new_temp()
             self._emit(OpCode.EQ, arg1=operand, arg2=0, result=result)
             return result
        elif node.operator.name == 'INCREMENT':
                                                             
             if isinstance(node.operand, ast.ArrayAccess):
                 arr_name = self._resolve(node.operand.name)
                 idx_val = self.visit(node.operand.index)
                 val = self._new_temp()
                 self._emit(OpCode.ALOAD, arg1=arr_name, arg2=idx_val, result=val)
                 
                 new_val = self._new_temp()
                 self._emit(OpCode.ADD, arg1=val, arg2=1, result=new_val)
                 
                 self._emit(OpCode.ASTORE, arg1=arr_name, arg2=idx_val, result=new_val)
                 return new_val
             raise Exception("IR Gen: ++/-- only supported on vars or arrays.")
        elif node.operator.name == 'DECREMENT':
             if isinstance(node.operand, ast.ArrayAccess):
                 arr_name = self._resolve(node.operand.name)
                 idx_val = self.visit(node.operand.index)
                 val = self._new_temp()
                 self._emit(OpCode.ALOAD, arg1=arr_name, arg2=idx_val, result=val)
                 
                 new_val = self._new_temp()
                 self._emit(OpCode.SUB, arg1=val, arg2=1, result=new_val)
                 
                 self._emit(OpCode.ASTORE, arg1=arr_name, arg2=idx_val, result=new_val)
                 return new_val
             raise Exception("IR Gen: ++/-- only supported on vars or arrays.")
        
        raise Exception(f"IR Gen Error: Unsupported unary operator {node.operator.name}")

    def visit_Assignment(self, node: ast.Assignment) -> str:
        # This specifically parses and processes Assignment structures.
        value = self.visit(node.value)
        target_name = self._resolve(node.name)             
        self._emit(OpCode.MOV, arg1=value, result=target_name)
        return target_name

    def _is_array(self, name: str) -> bool:

        # This handles the primary logic for is array operations.
        return f"{name}[]" in [k + "[]" for s in self.scopes for k in s]                                                 
