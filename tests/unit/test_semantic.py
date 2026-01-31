import pytest
from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer

def analyze_source(source):
    tokens = Lexer(source).tokenize()
    ast_root = Parser(tokens).parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast_root)

def test_valid_declarations():
    source = """
    int x = 10;
    void main() {
        int y = x + 5;
    }
    """
    analyze_source(source)

def test_undeclared_variable():
    source = """
    void main() {
        int x = y; 
    }
    """
    with pytest.raises(Exception) as excinfo:
        analyze_source(source)
    assert "Undeclared variable 'y'" in str(excinfo.value)

def test_type_mismatch_assignment():
    source = """
    void main() {
        int x = 10;
        x = 3.14; 
    }
    """ # float assigned to int
    with pytest.raises(Exception) as excinfo:
        analyze_source(source)
    print(f"\nCaught Exception: {excinfo.value}")
    assert "Cannot assign 'float' to 'int' for variable 'x'" in str(excinfo.value)

def test_scope_shadowing():
    source = """
    int x = 10;
    void main() {
        int x = 20; // Shadowing
        x = x + 1;
    }
    """
    analyze_source(source)

def test_scope_isolation():
    source = """
    void func() {
        int local = 5;
    }
    void main() {
        local = 10; // Error: local not in main
    }
    """
    with pytest.raises(Exception) as excinfo:
        analyze_source(source)
    assert "Undeclared variable 'local'" in str(excinfo.value)

def test_binary_op_mismatch():
    source = """
    void main() {
        int x = 10 + 3.5;
    }
    """
    # Our simple strict checker expects compatible types
    with pytest.raises(Exception) as excinfo:
        analyze_source(source)
    assert "Type mismatch" in str(excinfo.value)
