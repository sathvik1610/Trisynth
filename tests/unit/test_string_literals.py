import pytest
import io
import sys
from unittest.mock import patch
from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.ir_gen import IRGenerator
from src.main import IRInterpreter

def execute_code(code: str) -> str:
    """Helper to compile and interpret Trisynth code, capturing and explicitly returning stdout."""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    
    parser = Parser(tokens)
    ast = parser.parse()
    
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    
    ir_gen = IRGenerator()
    ir = ir_gen.generate(ast)
    
    interpreter = IRInterpreter(ir)
    
    # Capture standard output correctly
    captured_output = io.StringIO()
    with patch('sys.stdout', new=captured_output):
        interpreter.run()
        
    return captured_output.getvalue()

def test_string_literal_basic():
    code = """
    void main() {
        print("Hello World!");
    }
    """
    output = execute_code(code)
    assert output == "Hello World!"

def test_string_literal_with_escapes():
    code = """
    void main() {
        print("Line1\\nLine2\\tTabbed");
    }
    """
    output = execute_code(code)
    assert "Line1\nLine2\tTabbed" == output

def test_string_literal_multiple_outputs():
    code = """
    void main() {
        print("Value is: ");
        print(42);
    }
    """
    output = execute_code(code)
    # Integer print includes an implicit newline natively in our language right now, string print does not!
    assert output == "Value is: 42\n"
