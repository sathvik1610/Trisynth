import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
from src.frontend.lexer import Lexer
from src.frontend.parser import Parser

def main():
    parser = argparse.ArgumentParser(description="Trisynth Compiler")
    parser.add_argument('file', nargs='?', help="Source file to compile")
    parser.add_argument('--demo', action='store_true', help="Run in interactive demo mode")
    
    args = parser.parse_args()

    if args.demo or not args.file:
        run_demo()
    else:
        compile_file(args.file)

def run_demo():
    print("Trisynth Compiler Interactive Mode")
    print("----------------------------------")
    print("Type your code below (press Ctrl+Z then Enter to finish):")
    try:
        source_code = sys.stdin.read()
        process_source(source_code)
    except KeyboardInterrupt:
        return

def compile_file(filepath):
    try:
        with open(filepath, 'r') as f:
            source_code = f.read()
        process_source(source_code)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
    except Exception as e:
        print(f"Error: {e}")

class ASTPrinter:
    def __init__(self):
        self.output = []

    def print_tree(self, node, prefix="", is_last=True):
        if not node:
            return

        marker = "└── " if is_last else "├── "
        
        if isinstance(node, list):
            self.output.append(f"{prefix}{marker}List[{len(node)}]")
            new_prefix = prefix + ("    " if is_last else "│   ")
            for i, child in enumerate(node):
                self.print_tree(child, new_prefix, i == len(node) - 1)
            return
            
        # Get node name and attributes to print
        node_name = node.__class__.__name__
        attrs = []
        children = []
        
        import src.frontend.ast as ast
        if isinstance(node, ast.Program):
            children = node.declarations
        elif isinstance(node, (ast.Literal, ast.Variable)):
            attrs.append(str(node))
        elif isinstance(node, ast.BinaryExpr):
            attrs.append(f"op: {node.operator.name}")
            children = [node.left, node.right]
        elif isinstance(node, ast.UnaryExpr):
            attrs.append(f"op: {node.operator.name}")
            children = [node.operand]
        elif isinstance(node, ast.Assignment):
            attrs.append(f"target: {node.name}")
            children = [node.value]
        elif isinstance(node, ast.ArrayAssignment):
            attrs.append(f"target: {node.name}")
            children = [node.index, node.value]
        elif isinstance(node, ast.ArrayAccess):
            attrs.append(f"array: {node.name}")
            children = [node.index]
        elif isinstance(node, ast.CallExpr):
            attrs.append(f"callee: {node.callee}")
            children = node.args
        elif isinstance(node, ast.ExprStmt):
            children = [node.expression]
        elif isinstance(node, ast.PrintStmt):
            children = [node.expression]
        elif isinstance(node, ast.VarDecl):
            const_str = "const " if node.is_const else ""
            attrs.append(f"{const_str}{node.type_name} {node.name}")
            if node.initializer:
                children = [node.initializer]
        elif isinstance(node, ast.ArrayDecl):
            attrs.append(f"{node.type_name} {node.name}[{node.size}]")
        elif isinstance(node, ast.Block):
            children = node.statements
        elif isinstance(node, ast.IfStmt):
            children = [node.condition, node.then_branch]
            if node.else_branch:
                children.append(node.else_branch)
        elif isinstance(node, ast.WhileStmt):
            children = [node.condition, node.body]
        elif isinstance(node, ast.ForStmt):
            children = [node.init, node.condition, node.update, node.body]
        elif isinstance(node, ast.FunctionDecl):
            params_str = ", ".join([f"{t} {n}" for t, n in node.params])
            attrs.append(f"{node.return_type} {node.name}({params_str})")
            children = [node.body]
        elif isinstance(node, ast.ReturnStmt):
            if node.value:
                children = [node.value]
        else:
            attrs.append(str(node))

        attr_str = f" ({', '.join(attrs)})" if attrs else ""
        self.output.append(f"{prefix}{marker}{node_name}{attr_str}")

        new_prefix = prefix + ("    " if is_last else "│   ")
        # Filter None children
        children = [c for c in children if c is not None]
        for i, child in enumerate(children):
            self.print_tree(child, new_prefix, i == len(children) - 1)

    def format(self, root_node):
        self.output = []
        self.print_tree(root_node, "", True)
    def format(self, root_node):
        self.output = []
        self.print_tree(root_node, "", True)
        return "\n".join(self.output)

class IRInterpreter:
    """
    A simple stack-based interpreter to execute Trisynth Intermediate Representation (IR) directly.
    """
    def __init__(self, ir):
        self.ir = ir
        self.locals = {}       # Variable storage
        self.arrays = {}       # Array storage
        self.pc = 0            # Program counter
        self.call_stack = []   # Return addresses and saved locals
        self.param_stack = []  # Passing parameters between functions
        self.functions = {}    # Maps function name to starting PC
        self.labels = {}       # Maps label name to PC index (pre-built)
        self.return_value = None  # Stores most recent function return value

        # Build function and label lookup tables in one pass
        import src.ir.instructions as inst
        for i, instr in enumerate(self.ir):
            if instr.opcode == inst.OpCode.FUNC_START:
                self.functions[instr.arg1] = i   # arg1 = function name
            elif instr.opcode == inst.OpCode.LABEL:
                self.labels[instr.arg1] = i       # arg1 = label name
                
    def run(self, main_func="main"):
        if main_func not in self.functions:
            print(f"Error: Function '{main_func}' not found.")
            return
            
        self.pc = self.functions[main_func]
        import src.ir.instructions as inst
        
        while self.pc < len(self.ir):
            instr = self.ir[self.pc]
            op = instr.opcode
            
            if op == inst.OpCode.FUNC_START:
                pass
            elif op == inst.OpCode.FUNC_END:
                if not self.call_stack:
                    break # End of main
                state = self.call_stack.pop()
                self.pc = state['pc']
                self.locals = state['locals']
                # Store return value into caller's result register (for void funcs, result may be None)
                if state.get('result') and self.return_value is not None:
                    self.locals[state['result']] = self.return_value
                    self.return_value = None
            elif op == inst.OpCode.PARAM:
                val = self.locals.get(instr.arg1, instr.arg1)
                self.param_stack.append(val)
            elif op == inst.OpCode.PARAM_REF:
                self.param_stack.append(instr.arg1) # Pass array name as reference
            elif op == inst.OpCode.LOAD_PARAM:
                val = self.param_stack.pop(0) # FIFO
                self.locals[instr.result] = val
            elif op == inst.OpCode.LOAD_PARAM_REF:
                val = self.param_stack.pop(0)
                self.locals[instr.result] = val # Store reference name
            elif op == inst.OpCode.CALL:
                # Save state, including where to store the return value
                self.call_stack.append({
                    'pc': self.pc,
                    'locals': self.locals.copy(),
                    'result': instr.result,  # register to store return val in caller
                })
                # Jump to function
                self.pc = self.functions[instr.arg1]
                self.locals = {} # Clean locals for new frame
                self.return_value = None
            elif op == inst.OpCode.RETURN:
                if instr.arg1 is not None:
                    self.return_value = self.locals.get(instr.arg1, instr.arg1)

                if not self.call_stack:
                    break
                state = self.call_stack.pop()
                self.pc = state['pc']
                self.locals = state['locals']
                # Store return value into caller's result register
                if state.get('result') and self.return_value is not None:
                    self.locals[state['result']] = self.return_value
                    self.return_value = None
            elif op == inst.OpCode.PRINT:
                val = self.locals.get(instr.arg1, instr.arg1)
                print(val)
            elif op == inst.OpCode.ADD:
                left = self.locals.get(instr.arg1, instr.arg1)
                right = self.locals.get(instr.arg2, instr.arg2)
                self.locals[instr.result] = int(left) + int(right)
            elif op == inst.OpCode.SUB:
                left = self.locals.get(instr.arg1, instr.arg1)
                right = self.locals.get(instr.arg2, instr.arg2)
                self.locals[instr.result] = int(left) - int(right)
            elif op == inst.OpCode.MUL:
                left = self.locals.get(instr.arg1, instr.arg1)
                right = self.locals.get(instr.arg2, instr.arg2)
                self.locals[instr.result] = int(left) * int(right)
            elif op == inst.OpCode.DIV:
                left = self.locals.get(instr.arg1, instr.arg1)
                right = self.locals.get(instr.arg2, instr.arg2)
                self.locals[instr.result] = int(left) // int(right)
            elif op == inst.OpCode.LT:
                left = self.locals.get(instr.arg1, instr.arg1)
                right = self.locals.get(instr.arg2, instr.arg2)
                self.locals[instr.result] = 1 if int(left) < int(right) else 0
            elif op == inst.OpCode.GT:
                left = self.locals.get(instr.arg1, instr.arg1)
                right = self.locals.get(instr.arg2, instr.arg2)
                self.locals[instr.result] = 1 if int(left) > int(right) else 0
            elif op == inst.OpCode.JMP_IF_FALSE:
                # arg1 = condition var; arg2 = target label
                cond = self.locals.get(instr.arg1, instr.arg1)
                if not cond or cond == 0:
                    self.pc = self.labels[instr.arg2]
            elif op == inst.OpCode.JMP:
                # arg1 = target label
                self.pc = self.labels[instr.arg1]
            elif op == inst.OpCode.LTE:
                left = self.locals.get(instr.arg1, instr.arg1)
                right = self.locals.get(instr.arg2, instr.arg2)
                self.locals[instr.result] = 1 if int(left) <= int(right) else 0
            elif op == inst.OpCode.GTE:
                left = self.locals.get(instr.arg1, instr.arg1)
                right = self.locals.get(instr.arg2, instr.arg2)
                self.locals[instr.result] = 1 if int(left) >= int(right) else 0
            elif op == inst.OpCode.EQ:
                left = self.locals.get(instr.arg1, instr.arg1)
                right = self.locals.get(instr.arg2, instr.arg2)
                self.locals[instr.result] = 1 if int(left) == int(right) else 0
            elif op == inst.OpCode.NEQ:
                left = self.locals.get(instr.arg1, instr.arg1)
                right = self.locals.get(instr.arg2, instr.arg2)
                self.locals[instr.result] = 1 if int(left) != int(right) else 0
            elif op == inst.OpCode.MOD:
                left = self.locals.get(instr.arg1, instr.arg1)
                right = self.locals.get(instr.arg2, instr.arg2)
                self.locals[instr.result] = int(left) % int(right)
            elif op == inst.OpCode.LSHIFT:
                left = self.locals.get(instr.arg1, instr.arg1)
                right = self.locals.get(instr.arg2, instr.arg2)
                self.locals[instr.result] = int(left) << int(right)
            elif op == inst.OpCode.RSHIFT:
                left = self.locals.get(instr.arg1, instr.arg1)
                right = self.locals.get(instr.arg2, instr.arg2)
                self.locals[instr.result] = int(left) >> int(right)
            elif op == inst.OpCode.MOV:
                val = self.locals.get(instr.arg1, instr.arg1)
                self.locals[instr.result] = val
            elif op == inst.OpCode.ARR_DECL:
                self.arrays[instr.result] = [0] * int(instr.arg1)
            elif op == inst.OpCode.ASTORE:
                val = self.locals.get(instr.result, instr.result)
                arr_name = self.locals.get(instr.arg1, instr.arg1)
                idx = self.locals.get(instr.arg2, instr.arg2)
                self.arrays[arr_name][int(idx)] = int(val)
            elif op == inst.OpCode.ALOAD:
                arr_name = self.locals.get(instr.arg1, instr.arg1)
                idx = self.locals.get(instr.arg2, instr.arg2)
                self.locals[instr.result] = self.arrays[arr_name][int(idx)]
                
            self.pc += 1

def process_source(source_code):
    print("\n==================================")
    print("           PROGRAM OUTPUT           ")
    print("==================================\n")
    
    # Generate AST and IR instantly to execute first
    from src.ir.ir_gen import IRGenerator
    from src.semantic.analyzer import SemanticAnalyzer
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    
    try:
        ast = parser.parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        ir_gen = IRGenerator()
        ir = ir_gen.generate(ast)
        
        # Interpret the IR
        from src.optimization.optimizer import Optimizer
        from src.optimization.constant_fold import ConstantFolding
        from src.optimization.dead_code import DeadCodeElimination
        from src.optimization.strength_reduction import StrengthReduction
        
        optimizer = Optimizer()
        optimizer.add_pass(ConstantFolding())
        optimizer.add_pass(StrengthReduction())
        optimizer.add_pass(DeadCodeElimination())
        optimized_ir = optimizer.optimize(ir)
        
        interpreter = IRInterpreter(optimized_ir)
        interpreter.run()
    except Exception as e:
        print(f"Execution Error: {e}")

    print("\n==================================")
    print("         COMPILATION DETAILS        ")
    print("==================================")
    
    print("\n[1] Tokens:")
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    
    # Print Tokens in columns: [Line:Col] TYPE     "value"
    print("  Line:Col | Type             | Value")
    print("  ---------+------------------+-----------------")
    for t in tokens:
        print(f"  {t.line:02d}:{t.column:02d}    | {t.type.name:<16} | '{t.value}'")

    print("\n[2] Abstract Syntax Tree (AST):")
    parser = Parser(tokens)
    ast = parser.parse()
    ast_printer = ASTPrinter()
    print(ast_printer.format(ast))

    print("\n[3] Semantic Analysis:")
    from src.semantic.analyzer import SemanticAnalyzer
    try:
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        print("  ✅ Passed (No semantic errors)")
        
        # Extract symbols from the global scope (and potentially functions if we tracked them)
        # For a clean output, we can print the global scope functions at least
        print("\n  --- Global Symbol Table ---")
        print("  Name             | Type             | Category   ")
        print("  -----------------+------------------+------------")
        global_scope = analyzer.symbol_table.scopes[0]
        for name, sym in global_scope.items():
             print(f"  {name:<16} | {sym.type_name:<16} | {sym.category}")
            
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return # Stop if semantic error

    print("\n[4] Intermediate Representation (IR):")
    from src.ir.ir_gen import IRGenerator
    try:
        ir_gen = IRGenerator()
        ir = ir_gen.generate(ast)
        for instr in ir:
            print(f"  {instr}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return

    print("\n[5] Optimization:")
    from src.optimization.optimizer import Optimizer
    from src.optimization.constant_fold import ConstantFolding
    from src.optimization.dead_code import DeadCodeElimination
    from src.optimization.strength_reduction import StrengthReduction
    try:
        # Instead of generic optimizer, let's run passes manually to show steps
        print("  --- Initial IR ---")
        for instr in ir:
             print(f"    {instr}")
             
        passes = [
            ("Constant Folding", ConstantFolding()),
            ("Strength Reduction", StrengthReduction()),
            ("Dead Code Elimination", DeadCodeElimination())
        ]
        
        current_ir = ir
        for name, opt_pass in passes:
            print(f"\n  --- After {name} ---")
            current_ir = opt_pass.run(current_ir)
            if not current_ir:
                print("    (Empty IR)")
            else:
                for instr in current_ir:
                    print(f"    {instr}")
        print("\n  ✅ Optimization Complete")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

if __name__ == "__main__":
    main()
