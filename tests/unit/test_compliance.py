import pytest
from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.ir_gen import IRGenerator
# Note: TokenType is needed for some checks but not imported directly in tests usually?
# We just check IR output or semantic errors.

def analyze(code):
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    return analyzer

def generate_ir(code):
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    ir_gen = IRGenerator()
    return ir_gen.generate(ast)

def test_const_declaration_and_error():
    # Valid const
    code_valid = """
    void main() {
        const int x = 10;
        int y = x;
    }
    """
    analyze(code_valid)

    # Invalid Assignment to const
    code_invalid = """
    void main() {
        const int x = 10;
        x = 20; 
    }
    """
    with pytest.raises(Exception, match="Cannot assign to const variable"):
        analyze(code_invalid)

def test_increment_decrement():
    # Variable increment (Expanded to Assignment)
    code_var = """
    void main() {
        int i = 0;
        ++i;
        --i;
    }
    """
    ir = generate_ir(code_var)
    # Should see ADD and SUB opcodes
    opcodes = [i.opcode.name for i in ir]
    assert 'ADD' in opcodes
    assert 'SUB' in opcodes

    # Array increment (UnaryExpr in AST/IR)
    code_arr = """
    void main() {
        int arr[5];
        ++arr[0];
    }
    """
    ir = generate_ir(code_arr)
    # Should see ALOAD, ADD, ASTORE sequence
    opcodes = [i.opcode.name for i in ir]
    assert 'ALOAD' in opcodes
    assert 'ADD' in opcodes
    assert 'ASTORE' in opcodes

def test_const_increment_error():
    code = """
    void main() {
        const int x = 5;
        ++x;
    }
    """
    with pytest.raises(Exception, match="Cannot assign to const variable"):
        analyze(code)

def test_function_hoisting():
    # Calling a function declared LATER
    code = """
    void main() {
        foo();
    }
    
    void foo() {
        print(1);
    }
    """
    analyze(code) # Should pass with Two-Pass analyzer
