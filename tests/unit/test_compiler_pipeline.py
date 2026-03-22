import pytest
from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.ir_gen import IRGenerator
from src.optimization.optimizer import Optimizer
from src.optimization.strength_reduction import StrengthReduction
from src.optimization.cse import CommonSubexpressionElimination
from src.optimization.copy_propagation import CopyPropagation
from src.optimization.constant_fold import ConstantFolding
from src.optimization.dead_code import DeadCodeElimination

def compile_to_ir(source):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast)
    ir = IRGenerator().generate(ast)
    
    optimizer = Optimizer()
    optimizer.add_pass(StrengthReduction())
    optimizer.add_pass(CommonSubexpressionElimination())
    optimizer.add_pass(CopyPropagation())
    optimizer.add_pass(ConstantFolding())
    optimizer.add_pass(CommonSubexpressionElimination())
    optimizer.add_pass(DeadCodeElimination())
    
    return optimizer.optimize(ir)

def test_full_pipeline_compiles_without_errors():
    source = """
    int helper(int a, int b) {
        if (a > b) { return a; } else { return b; }
    }
    void main() {
        int x = 16;
        int y = 8;
        int expr = (x * 2) + helper(x, y);
        print(expr);
    }
    """
    optimized_ir = compile_to_ir(source)
    assert len(optimized_ir) > 0
