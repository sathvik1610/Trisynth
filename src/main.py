# This file serves as the main execution entry point for the compiler. This grabs the user arguments and run the whole pipeline from text to executable here.

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
from src.frontend.lexer import Lexer
from src.frontend.parser import Parser

def main():
               
    # This is the primary entrypoint where we tie everything together.
    parser = argparse.ArgumentParser(description="Trisynth Native Compiler")
    parser.add_argument('file', nargs='?', help="Source file to compile (.tri)")
    parser.add_argument('--demo', action='store_true', help="Run in interactive demo mode")
    parser.add_argument('--arch', choices=['x86', 'riscv', 'both'], default='x86',
                        help="Target architecture (default: x86)")
    parser.add_argument('--tokens', action='store_true', help='Print Lexer tokens and halt')
    parser.add_argument('--ast', action='store_true', help='Print Abstract Syntax Tree and halt')
    parser.add_argument('--ir', action='store_true', help='Print Intermediate Representation and halt')
    parser.add_argument('--asm', action='store_true', help='Print generated Assembly strings and halt')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print all compilation details')
    parser.add_argument('--compare-asm', action='store_true', help='Compile to both x86 and RISC-V and print side-by-side')
    parser.add_argument('--benchmark', action='store_true', help='Compile, natively execute, and compare speeds of x86 vs RISC-V')
    
    args = parser.parse_args()

    if args.demo or not args.file:
        run_demo(args)
    else:
        if not args.file.endswith('.tri'):
            print(f"Fatal Compiler Error: Unrecognized file extension in '{args.file}'.")
            print("Trisynth natively requires standard '.tri' source files for parsing.")
            sys.exit(1)
        compile_file(args.file, args)

def run_demo(args):
    # This launches the interactive demo mode directly in the console.
    print("Trisynth Compiler Interactive Mode")
    print("----------------------------------")
    print("Type your code below (press Ctrl+D on Linux/Mac or Ctrl+Z then Enter on Windows to finish):")
    try:
        source_code = sys.stdin.read()
        if source_code.strip():
            process_source(source_code, args)
    except (KeyboardInterrupt, EOFError):
        return

def compile_file(filepath, args):
                                          
    # This lakes a file path and pushes it through the compiler pipeline.
    try:
        with open(filepath, 'r') as f:
            source_code = f.read()
        process_source(source_code, args)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
    except Exception as e:
        print(f"Error: {e}")

class ASTPrinter:
                                
    def __init__(self):
        # This initializes the base properties.
        self.output = []

    def print_tree(self, node, prefix="", is_last=True):
        # This handles the primary logic for print tree operations.
        if not node:
            return

        marker = "└── " if is_last else "├── "
        
        if isinstance(node, list):
            self.output.append(f"{prefix}{marker}List[{len(node)}]")
            new_prefix = prefix + ("    " if is_last else "│   ")
            for i, child in enumerate(node):
                self.print_tree(child, new_prefix, i == len(node) - 1)
            return
            
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
        children = [c for c in children if c is not None]
        for i, child in enumerate(children):
            self.print_tree(child, new_prefix, i == len(children) - 1)

    def format(self, root_node):
        # This handles the primary logic for format operations.
        self.output = []
        self.print_tree(root_node, "", True)
        return "\n".join(self.output)

class IRInterpreter:
                                              
    def __init__(self, ir):
        # This initializes the base properties.
        self.ir = ir
        self.locals: "dict" = {}
        self.arrays: "dict" = {}
        self.pc = 0
        self.call_stack = []
        self.param_stack = []
        self.functions = {}
        self.labels = {}
        self.return_value = None

        import src.ir.instructions as inst
        for i, instr in enumerate(self.ir):
            if instr.opcode == inst.OpCode.FUNC_START:
                self.functions[instr.arg1] = i
            elif instr.opcode == inst.OpCode.LABEL:
                self.labels[instr.arg1] = i
                
    def run(self, main_func="main"):
        # This kicks off the main execution loop for this component.
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
                    break
                state = self.call_stack.pop()
                self.pc = state['pc']
                self.locals = state['locals']
                if state.get('result') and self.return_value is not None:
                    self.locals[state['result']] = self.return_value
                    self.return_value = None
            elif op == inst.OpCode.PARAM:
                val = self.locals.get(instr.arg1, instr.arg1)
                self.param_stack.append(val)
            elif op == inst.OpCode.PARAM_REF:
                self.param_stack.append(instr.arg1)
            elif op == inst.OpCode.LOAD_PARAM:
                val = self.param_stack.pop(0)
                self.locals[instr.result] = val
            elif op == inst.OpCode.LOAD_PARAM_REF:
                val = self.param_stack.pop(0)
                self.locals[instr.result] = val
            elif op == inst.OpCode.CALL:
                self.call_stack.append({
                    'pc': self.pc,
                    'locals': self.locals.copy(),
                    'result': instr.result,
                })
                self.pc = self.functions[instr.arg1]
                self.locals = {}
                self.return_value = None
            elif op == inst.OpCode.RETURN:
                if instr.arg1 is not None:
                    self.return_value = self.locals.get(instr.arg1, instr.arg1)
                if not self.call_stack:
                    break
                state = self.call_stack.pop()
                self.pc = state['pc']
                self.locals = state['locals']
                if state.get('result') and self.return_value is not None:
                    self.locals[state['result']] = self.return_value
                    self.return_value = None
            elif op == inst.OpCode.PRINT:
                val = self.locals.get(instr.arg1, instr.arg1)
                print(val)
            elif op == inst.OpCode.PRINT_STR:
                val = self.locals.get(instr.arg1, instr.arg1)
                processed_val = str(val).encode('utf-8').decode('unicode_escape')
                print(processed_val, end='')
            elif op == inst.OpCode.LOAD_STR:
                self.locals[instr.result] = instr.arg1
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
                cond = self.locals.get(instr.arg1, instr.arg1)
                if not cond or cond == 0:
                    self.pc = self.labels[instr.arg2]
            elif op == inst.OpCode.JMP:
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

def _resolve_toolchain():
                                                           
    # This handles the primary logic for resolve toolchain operations.
    import platform
    import shutil
    import subprocess

    system = platform.system()

    if system != "Windows":
        return {
            "mode":     "linux",
            "prefix":   [],
            "obj_fmt":  "elf64",
            "obj_ext":  ".o",
            "exe":      "program",
            "run":      ["./program"],
            "tag":      "",
        }

    if shutil.which("wsl") is not None:
        try:
            subprocess.run(
                ["wsl", "nasm", "--version"],
                capture_output=True, timeout=5, check=True
            )
            return {
                "mode":     "wsl",
                "prefix":   ["wsl"],
                "obj_fmt":  "elf64",
                "obj_ext":  ".o",
                "exe":      "program",
                "run":      ["wsl", "./program"],
                "tag":      " over WSL",
            }
        except Exception:
            pass

    if shutil.which("nasm") is not None and shutil.which("gcc") is not None:
        return {
            "mode":     "windows_native",
            "prefix":   [],
            "obj_fmt":  "win64",
            "obj_ext":  ".obj",
            "exe":      "program.exe",
            "run":      ["program.exe"],
            "tag":      " (native Windows)",
        }

    return None


def _toolchain_install_hint():
    # This handles the primary logic for toolchain install hint operations.
    import platform
    system = platform.system()
    if system == "Windows":
        return (
            "  Run `setup.bat` (double-click or as Administrator) to auto-install everything.\n"
            "  Note: RISC-V is not supported on native Windows — use WSL for that."
        )
    else:
        return (
            "  Run: curl -sSL <repo-url>/setup.sh | bash\n"
            "  (Or run `bash setup.sh` in the project root) to auto-install everything."
        )


def process_source(source_code, args):
                             
    # This handles the primary logic for process source operations.
    import time
    start_time = time.time()
    
    verbose = args.verbose
    if verbose or args.tokens or args.ast or args.ir or args.asm or args.compare_asm:
        print(r"""
  _____     _                  _   _     
 |_   _| __(_)___ _   _ _ __ | |_| |__  
   | || '__| / __| | | | '_ \| __| '_ \ 
   | || |  | \__ \ |_| | | | | |_| | | |
   |_||_|  |_|___/\__, |_| |_|\__|_| |_|
                  |___/                 
""")
    if verbose:
        print("==================================")
        print("         COMPILATION DETAILS        ")
        print("==================================")
    
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    
    if verbose or args.tokens:
        print("\n[1] Tokens:")
        print("  Line:Col | Type             | Value")
        print("  ---------+------------------+-----------------")
        for t in tokens:
            print(f"  {t.line:02d}:{t.column:02d}    | {t.type.name:<16} | '{t.value}'")
        if args.tokens: return

    parser = Parser(tokens)
    ast = parser.parse()
    
    if verbose or args.ast:
        print("\n[2] Abstract Syntax Tree (AST):")
        ast_printer = ASTPrinter()
        print(ast_printer.format(ast))
        if args.ast: return

    from src.semantic.analyzer import SemanticAnalyzer
    try:
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        if verbose:
            print("\n[3] Semantic Analysis:")
            print("   Passed (No semantic errors)")
            print("\n  --- Global Symbol Table ---")
            print("  Name             | Type             | Category   ")
            print("  -----------------+------------------+------------")
            global_scope = analyzer.symbol_table.scopes[0]
            for name, sym in global_scope.items():
                 print(f"  {name:<16} | {sym.type_name:<16} | {sym.category}")
    except Exception as e:
        print(f"   Failed: {e}")
        return

    from src.ir.ir_gen import IRGenerator
    try:
        ir_gen = IRGenerator()
        ir = ir_gen.generate(ast)
        if verbose or args.ir:
            print("\n[4] Intermediate Representation (IR):")
            for instr in ir:
                print(f"  {instr}")
    except Exception as e:
        print(f"   Failed: {e}")
        return

    from src.optimization.constant_fold import ConstantFolding
    from src.optimization.dead_code import DeadCodeElimination
    from src.optimization.strength_reduction import StrengthReduction
    from src.optimization.cse import CommonSubexpressionElimination
    from src.optimization.copy_propagation import CopyPropagation
    try:
        passes = [
            ("Strength Reduction", StrengthReduction()),
            ("Common Subexp Elimination", CommonSubexpressionElimination()),
            ("Copy Propagation", CopyPropagation()),
            ("Constant Folding", ConstantFolding()),
            ("Post-Folding Cleanup", CommonSubexpressionElimination()),
            ("Dead Code Elimination", DeadCodeElimination())
        ]
        
        current_ir = ir
        if verbose or args.ir:
            print("\n[5] Optimization:")
            print("  --- Initial IR ---")
            for instr in ir:
                 print(f"    {instr}")
                 
        for name, opt_pass in passes:
            current_ir = opt_pass.run(current_ir)
            if verbose or args.ir:
                print(f"\n  --- After {name} ---")
                if not current_ir:
                    print("    (Empty IR)")
                else:
                    for instr in current_ir:
                        print(f"    {instr}")
        if verbose or args.ir:
            print("\n   Optimization Complete")
            if args.ir: return
    except Exception as e:
        print(f"   Failed: {e}")
        return

    from src.backend.codegen_x86 import X86Generator
    from src.backend.riscv.codegen_riscv import RISCVGenerator
    
    x86_gen = X86Generator()
    asm_code = x86_gen.generate(current_ir)
    with open("output.asm", "w") as f:
        f.write(asm_code)
        
    riscv_gen = RISCVGenerator()
    riscv_code = riscv_gen.generate(current_ir)
    with open("output_riscv.s", "w") as f:
        f.write(riscv_code)

    if verbose or args.asm or args.compare_asm:
        if args.compare_asm or args.arch in ('x86', 'both'):
            print("\n[7] X86-64 Code Generation (NASM):")
            for line in asm_code.splitlines():
                print(f"  {line}")
        if args.compare_asm or args.arch in ('riscv', 'both'):
            print("\n[8] RISC-V 64-bit Code Generation (GNU AS):")
            for line in riscv_code.splitlines():
                print(f"  {line}")
        if args.asm or args.compare_asm: return

    if verbose:
        print("\n==================================")
        print("           PROGRAM OUTPUT           ")
        print("==================================\n")

    try:
        import subprocess

        tc = _resolve_toolchain()

        if tc is None:
            print("   No assembler toolchain found.")
            print(_toolchain_install_hint())
            return

        if verbose:
            print(f"  [Toolchain: {tc['mode']}]")

        if tc['mode'] == 'linux':
            meipass = getattr(sys, '_MEIPASS', None)
            if meipass:
                exe_dir = os.path.dirname(os.path.abspath(sys.executable))
                external_nasm = os.path.join(exe_dir, 'bin', 'linux', 'nasm')
                internal_nasm = os.path.join(meipass, 'bin', 'linux', 'nasm')
                if os.path.exists(external_nasm):
                    bundled_nasm = external_nasm
                else:
                    bundled_nasm = internal_nasm
            else:
                bundled_nasm = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin', 'linux', 'nasm'))
            nasm_exe = bundled_nasm if os.path.exists(bundled_nasm) else "nasm"
            # Auto-fix execute permission if the bundled nasm isn't executable
            # (happens when zip is extracted on Windows and Unix bits are stripped)
            if nasm_exe != "nasm" and os.path.exists(nasm_exe):
                import stat as _stat
                current_mode = os.stat(nasm_exe).st_mode
                if not (current_mode & _stat.S_IXUSR):
                    os.chmod(nasm_exe, current_mode | _stat.S_IXUSR | _stat.S_IXGRP | _stat.S_IXOTH)
        else:
            nasm_exe = "nasm"

        obj_fmt  = str(tc['obj_fmt'])
        obj_ext  = str(tc['obj_ext'])
        exe_name = str(tc['exe'])
        prefix   = list(tc['prefix'])
        run_cmd  = list(tc['run'])
        tag      = str(tc['tag'])

        if args.benchmark:
            print(f"  [Benchmarking Mode -> Building X86-64 Native & RISC-V QEMU]")

            if tc['mode'] == 'windows_native':
                print("  ⚠️  Benchmark mode requires WSL or Linux for RISC-V/QEMU support.")

            x86_start = time.time()
            subprocess.run(prefix + [nasm_exe, "-f", obj_fmt, "output.asm", "-o", f"output{obj_ext}"], check=True)
            link_flags = ["-no-pie"] if tc['mode'] != 'windows_native' else []
            subprocess.run(prefix + ["gcc", f"output{obj_ext}", "-o", exe_name] + link_flags, check=True)
            res_x86 = subprocess.run(run_cmd, text=True, capture_output=True)
            x86_elapsed = (time.time() - x86_start) * 1000

            if tc['mode'] != 'windows_native':
                rv_start = time.time()
                subprocess.run(prefix + ["riscv64-linux-gnu-gcc", "output_riscv.s", "-o", "program_riscv", "-static"], check=True)
                res_rv = subprocess.run(prefix + ["qemu-riscv64", "./program_riscv"], text=True, capture_output=True)
                rv_elapsed = (time.time() - rv_start) * 1000
                print(f"\n[X86-64 NATIVE EXECUTION]\n{res_x86.stdout}")
                print(f"[RISC-V QEMU EXECUTION]\n{res_rv.stdout}")
                print(f"\n   Benchmarking Complete")
                print(f"  x86-64{tag}: {x86_elapsed:.2f} ms")
                print(f"   RISC-V QEMU Emulation: {rv_elapsed:.2f} ms")
            else:
                print(f"\n[X86-64 NATIVE EXECUTION]\n{res_x86.stdout}")
                print(f"\n   X86-64 Benchmark Complete")
                print(f"  x86-64{tag}: {x86_elapsed:.2f} ms")

        else:
            if verbose: print("  [Invoking Native Assembler & Linker...]")

            link_flags = ["-no-pie"] if tc['mode'] != 'windows_native' else []

            if args.arch in ('x86', 'both'):
                subprocess.run(prefix + [nasm_exe, "-f", obj_fmt, "output.asm", "-o", f"output{obj_ext}"], check=True)
                subprocess.run(prefix + ["gcc", f"output{obj_ext}", "-o", exe_name] + link_flags, check=True)
                result = subprocess.run(run_cmd, text=True, capture_output=True)
                print(result.stdout, end="")

            if args.arch in ('riscv', 'both'):
                if tc['mode'] == 'windows_native':
                    print("  ⚠️  RISC-V target requires WSL or Linux. Skipping.")
                else:
                    subprocess.run(prefix + ["riscv64-linux-gnu-gcc", "output_riscv.s", "-o", "program_riscv", "-static"], check=True)
                    result = subprocess.run(prefix + ["qemu-riscv64", "./program_riscv"], text=True, capture_output=True)
                    print(result.stdout, end="")

            end_time = time.time()
            elapsed = (end_time - start_time) * 1000
            if verbose:
                print(f"\n   Native Hardware Execution Complete")
                print(f"  Trisynth natively assembled & executed{tc['tag']} in {elapsed:.2f} ms")

    except Exception as e:
        print(f"  Failed: {e}")

if __name__ == "__main__":
    main()
