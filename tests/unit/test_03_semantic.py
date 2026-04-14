import pytest
from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer

def _analyze(code):
    ast = Parser(Lexer(code).tokenize()).parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

def test_valid_program():
    code = "int x = 10; int get_x() { return x; } void main() {}"
    _analyze(code)  # Should not raise

def test_undeclared_variable():
    with pytest.raises(Exception, match="Undeclared variable"):
        _analyze("void main() { x = 5; }")

def test_type_mismatch():
    with pytest.raises(Exception, match="Type Error"):
        _analyze("void main() { int x = 5; int arr[10]; x = arr; }")

def test_missing_return():
    with pytest.raises(Exception, match="Missing return statement"):
        _analyze("int foo() { int x = 5; } void main() {}")

def test_invalid_argument_count():
    code = "int add(int a, int b) { return a+b; } void main() { int x = add(5); }"
    with pytest.raises(Exception, match="expects 2 arguments"):
        _analyze(code)

def test_const_reassignment():
    with pytest.raises(Exception, match="Cannot assign to const variable"):
        _analyze("void main() { const int X = 10; X = 20; }")
