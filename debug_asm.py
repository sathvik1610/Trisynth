# debug_asm.py
import sys
import os

# Ensure src is in path
sys.path.append(os.path.dirname(__file__))

from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.ir_gen import IRGenerator
from src.optimization.optimizer import Optimizer
from src.optimization.constant_fold import ConstantFolding
from src.optimization.dead_code import DeadCodeElimination
from src.optimization.strength_reduction import StrengthReduction
from src.backend.x86_64.codegen import X86Generator

def compile_to_asm(filepath):
    print(f"Compiling {filepath}...")
    with open(filepath, 'r') as f:
        code = f.read()

    # 1. Frontend
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast)

    # 2. IR
    ir = IRGenerator().generate(ast)

    # 3. Optimize
    opt = Optimizer()
    opt.add_pass(ConstantFolding())
    opt.add_pass(StrengthReduction())
    opt.add_pass(DeadCodeElimination())
    ir = opt.optimize(ir)

    # 4. Backend
    gen = X86Generator()
    asm = gen.generate(ir)

    # 5. Output
    out_path = filepath.replace(".nc", ".asm")
    with open(out_path, 'w') as f:
        f.write(asm)
    
    print(f"✅ Generated: {out_path}")
    print(f"Size: {len(asm.splitlines())} lines")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_asm.py <file.nc>")
    else:
        compile_to_asm(sys.argv[1])
