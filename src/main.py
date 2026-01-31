import sys
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

def process_source(source_code):
    print("\n[1] Tokens:")
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    for token in tokens:
        print(f"  {token}")

    print("\n[2] Abstract Syntax Tree (AST):")
    parser = Parser(tokens)
    ast = parser.parse()
    for decl in ast.declarations:
        print(f"  {decl}")

    print("\n[3] Semantic Analysis:")
    from src.semantic.analyzer import SemanticAnalyzer
    try:
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        print("  ✅ Passed (No semantic errors)")
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

    print("\n[5] Optimization (Constant Folding & Dead Code Elimination):")
    from src.optimization.optimizer import Optimizer
    from src.optimization.constant_fold import ConstantFolding
    from src.optimization.dead_code import DeadCodeElimination
    try:
        optimizer = Optimizer()
        optimizer.add_pass(ConstantFolding())
        optimizer.add_pass(DeadCodeElimination())
        optimized_ir = optimizer.optimize(ir)
        for instr in optimized_ir:
            print(f"  {instr}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

if __name__ == "__main__":
    main()
