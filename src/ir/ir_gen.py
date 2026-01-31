from typing import List, Union
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

        # Loop Control Stack for break/continue
        # Stack of tuples: (continue_label, break_label)
        self.loop_stack = []

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

    def visit(self, node: ast.ASTNode) -> Union[str, int, float]:
        """
        Generic visitor. Returns the name of the variable/temp holding the result (if any) OR a literal value.
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
        unique_name = self._get_unique_name(node.name)
        self.scopes[-1][node.name] = unique_name
        
        if node.initializer:
            value_src = self.visit(node.initializer)
            self._emit(OpCode.MOV, arg1=value_src, result=unique_name)

    def visit_ArrayDecl(self, node: ast.ArrayDecl):
        # int x[10]; -> Just register unique name or emit alloc?
        # Since we don't have malloc, and stack is implicit, 
        # we treat 'x' as base pointer/name.
        unique_name = self._get_unique_name(node.name)
        self.scopes[-1][node.name] = unique_name
        # Optional: Emit ARR_DECL x_N size (for backend stack alloc info)
        # self._emit(OpCode.ARR_DECL, arg1=node.size, result=unique_name)
        # For our simple IR, ALOAD/ASTORE will just use unique_name.
        pass

    def visit_FunctionDecl(self, node: ast.FunctionDecl):
        self._emit(OpCode.FUNC_START, arg1=node.name)
        self._enter_scope()
        
        for i, (_, param_name) in enumerate(node.params):
            unique_name = self._get_unique_name(param_name)
            self.scopes[-1][param_name] = unique_name
            # Emit LOAD_PARAM index, result=unique_name
            self._emit(OpCode.LOAD_PARAM, arg1=i, result=unique_name)

        self.visit(node.body) 
        self._exit_scope()
        
        if self.instructions[-1].opcode != OpCode.RETURN:
             self._emit(OpCode.FUNC_END, arg1=node.name)

    def visit_Block(self, node: ast.Block):
        self._enter_scope()
        for stmt in node.statements:
            self.visit(stmt)
        self._exit_scope()

    def visit_IfStmt(self, node: ast.IfStmt):
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

        # Push to loop stack: (continue_target, break_target)
        self.loop_stack.append((label_start, label_end))

        self._emit(OpCode.LABEL, arg1=label_start)
        cond_temp = self.visit(node.condition)
        self._emit(OpCode.JMP_IF_FALSE, arg1=cond_temp, arg2=label_end)

        self.visit(node.body)
        self._emit(OpCode.JMP, arg1=label_start)

        self._emit(OpCode.LABEL, arg1=label_end)
        self.loop_stack.pop()

    def visit_ForStmt(self, node: ast.ForStmt):
        # for (init; cond; update) body
        # Scope for init variable? 
        # C99 allows int i=0 inside for. So we should enter scope.
        self._enter_scope()
        
        if node.init:
            self.visit(node.init) # Decl or ExprStmt

        label_start = self._new_label() # Check condition
        label_update = self._new_label() # Increment
        label_end = self._new_label()   # Exit

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
        if not self.loop_stack:
            raise Exception("IR Gen Error: Break outside loop.")
        _, label_break = self.loop_stack[-1]
        self._emit(OpCode.JMP, arg1=label_break)

    def visit_ContinueStmt(self, node: ast.ContinueStmt):
        if not self.loop_stack:
            raise Exception("IR Gen Error: Continue outside loop.")
        label_continue, _ = self.loop_stack[-1]
        self._emit(OpCode.JMP, arg1=label_continue)

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

    def visit_Literal(self, node: ast.Literal) -> Union[str, int, float]:
        if isinstance(node.value, bool):
            return 1 if node.value else 0
        return node.value

    def visit_Variable(self, node: ast.Variable) -> str:
        return self._resolve(node.name)
        
    def visit_ArrayAccess(self, node: ast.ArrayAccess) -> str:
        array_name = self._resolve(node.name)
        index_val = self.visit(node.index)
        result = self._new_temp()
        self._emit(OpCode.ALOAD, arg1=array_name, arg2=index_val, result=result)
        return result

    def visit_ArrayAssignment(self, node: ast.ArrayAssignment) -> str:
        array_name = self._resolve(node.name)
        index_val = self.visit(node.index)
        value_val = self.visit(node.value)
        self._emit(OpCode.ASTORE, arg1=array_name, arg2=index_val, result=value_val) # ASTORE arr, idx, val (result field reused for val)
        return value_val

    def visit_CallExpr(self, node: ast.CallExpr) -> str:
        # Evaluate arguments
        arg_temp_names = []
        for arg in node.args:
            arg_temp_names.append(self.visit(arg))
            
        # Push arguments (PARAM)
        for temp_name in arg_temp_names:
            self._emit(OpCode.PARAM, arg1=temp_name)
            
        result = self._new_temp()
        # CALL func_name, num_args -> result
        self._emit(OpCode.CALL, arg1=node.callee, arg2=len(node.args), result=result)
        return result

    def visit_LogicalExpr(self, node: ast.LogicalExpr) -> str:
        # Short-circuit logic: a && b
        # t = 0 (false)
        # if !a jmp end
        # if !b jmp end
        # t = 1 (true)
        # label end
        
        # Actually, simpler:
        # result = new_temp()
        # MOV result, 0
        
        label_true = self._new_label()
        label_false = self._new_label()
        label_end = self._new_label()
        
        left = self.visit(node.left)
        
        if node.operator.name == 'AND':
             # if !left jmp false (actually false/end same here)
             # simpler: 
             # MOV result 0
             # JMP_IF_FALSE left, end
             # right = visit(right)
             # JMP_IF_FALSE right, end
             # MOV result 1
             # LABEL end
             
             result = self._new_temp()
             self._emit(OpCode.MOV, arg1=0, result=result)
             self._emit(OpCode.JMP_IF_FALSE, arg1=left, arg2=label_end)
             
             right = self.visit(node.right)
             self._emit(OpCode.JMP_IF_FALSE, arg1=right, arg2=label_end)
             
             self._emit(OpCode.MOV, arg1=1, result=result)
             self._emit(OpCode.LABEL, arg1=label_end)
             return result
             
        elif node.operator.name == 'OR':
             # MOV result 1
             # JMP_IF_FALSE left, check_right
             # JMP end (it was true)
             # LABEL check_right
             # JMP_IF_FALSE right, set_false
             # JMP end (it was true)
             # LABEL set_false
             # MOV result 0
             # LABEL end
             
             result = self._new_temp()
             self._emit(OpCode.MOV, arg1=1, result=result)
             
             label_check_right = self._new_label()
             label_set_false = self._new_label()
             
             # If left is FALSE, we must check right.
             self._emit(OpCode.JMP_IF_FALSE, arg1=left, arg2=label_check_right)
             # Left was true -> result is 1, jump to end
             self._emit(OpCode.JMP, arg1=label_end)
             
             self._emit(OpCode.LABEL, arg1=label_check_right)
             right = self.visit(node.right)
             self._emit(OpCode.JMP_IF_FALSE, arg1=right, arg2=label_set_false)
             # Right was true -> result is 1, jump to end
             self._emit(OpCode.JMP, arg1=label_end)
             
             self._emit(OpCode.LABEL, arg1=label_set_false)
             self._emit(OpCode.MOV, arg1=0, result=result)
             
             self._emit(OpCode.LABEL, arg1=label_end)
             return result
             
        raise Exception(f"IR Gen Error: Unknown logical op {node.operator.name}")

    def visit_BinaryExpr(self, node: ast.BinaryExpr) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        temp = self._new_temp()
        
        op_map = {
            'PLUS': OpCode.ADD, 'MINUS': OpCode.SUB, 
            'STAR': OpCode.MUL, 'SLASH': OpCode.DIV, 'MODULO': OpCode.MOD,
            'LT': OpCode.LT, 'GT': OpCode.GT, 'LTE': OpCode.LTE, 'GTE': OpCode.GTE,
            'EQ': OpCode.EQ, 'NEQ': OpCode.NEQ
        }
        
        opcode = op_map.get(node.operator.name)
        if not opcode:
            raise Exception(f"IR Gen Error: Unsupported binary operator {node.operator.name}")
            
        self._emit(opcode, arg1=left, arg2=right, result=temp)

        return temp

    def visit_UnaryExpr(self, node: ast.UnaryExpr) -> str:
        if node.operator.name == 'MINUS':
            operand = self.visit(node.operand)
            result = self._new_temp()
            # 0 - operand
            self._emit(OpCode.SUB, arg1=0, arg2=operand, result=result)
            return result
        elif node.operator.name == 'NOT':
             # !operand -> (operand == 0)
             operand = self.visit(node.operand)
             result = self._new_temp()
             self._emit(OpCode.EQ, arg1=operand, arg2=0, result=result)
             return result
        elif node.operator.name == 'INCREMENT':
             # Only for ArrayAccess here (Variables expanded)
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
        value = self.visit(node.value)
        target_name = self._resolve(node.name) # Must exist
        self._emit(OpCode.MOV, arg1=value, result=target_name)
        return target_name
