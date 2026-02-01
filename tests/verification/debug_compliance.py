from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer

def debug_analyze(code):
    try:
        print(f"--- Analyzing Code ---\n{code}")
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        print("✅ Analysis Successful")
    except Exception as e:
        print(f"❌ Exception: {e}")

code_const_inc = """
void main() {
    const int x = 5;
    ++x;
}
"""
debug_analyze(code_const_inc)

code_hoisting = """
void main() {
    foo();
}
void foo() {
    print(1);
}
"""
debug_analyze(code_hoisting)
