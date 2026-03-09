import pytest
from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer

def analyze_code(source_code):
    """Helper to parse and semantically analyze NanoC code."""
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

class TestArrayAndRecursionErrors:

    def test_array_negative_size(self):
        """Parser rejects negative array sizes (MINUS token triggers Syntax Error before size check)."""
        code = "void main() { int arr[-5]; }"
        with pytest.raises(Exception):  # Parser hits MINUS before INTEGER → Syntax Error
            analyze_code(code)

    def test_array_zero_size(self):
        """Parser should reject zero array sizes."""
        code = "void main() { int arr[0]; }"
        with pytest.raises(Exception, match="Array size must be a positive integer"):
            analyze_code(code)

    def test_array_non_integer_size(self):
        """Parser requires INTEGER token for size; `true` causes a Syntax Error."""
        code = "void main() { int arr[true]; }"
        with pytest.raises(Exception):
            analyze_code(code)

    def test_array_access_non_integer_index(self):
        """Indexing an array with a bool should raise a type error."""
        code = """
        void main() { 
            int arr[5];
            arr[1] = 5;
            int x = arr[true];
        }
        """
        with pytest.raises(Exception, match="Array index must be int"):
            analyze_code(code)

    def test_array_assignment_non_integer_index(self):
        """Assigning through a bool index should raise a type error."""
        code = """
        void main() { 
            int arr[5];
            arr[false] = 10;
        }
        """
        with pytest.raises(Exception, match="Array index must be int"):
            analyze_code(code)

    def test_pass_int_to_array_param(self):
        """Passing a plain int where an int[] is expected should raise a type error."""
        code = """
        void foo(int arr[]) {}
        void main() {
            int x = 5;
            foo(x);
        }
        """
        with pytest.raises(Exception, match=r"expects 'int\[\]'"):
            analyze_code(code)

    def test_pass_array_to_int_param(self):
        """Passing an int[] where a plain int is expected should raise a type error."""
        code = """
        void foo(int x) {}
        void main() {
            int arr[5];
            foo(arr);
        }
        """
        with pytest.raises(Exception, match=r"expects 'int'"):
            analyze_code(code)

    def test_missing_return_in_recursive_func(self):
        """A non-void function missing a guaranteed return path should raise an error."""
        code = """
        int recursive_bad(int n) {
            if (n > 0) {
                return recursive_bad(n - 1);
            }
        }
        void main() {}
        """
        with pytest.raises(Exception, match="Missing return statement in non-void function 'recursive_bad'"):
            analyze_code(code)
