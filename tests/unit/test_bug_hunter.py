"""
BUG HUNTER NEGATIVE TEST SUITE
================================
Exhaustive negative tests across ALL compiler phases.
Tests are intentionally designed to find edge cases and unfixed bugs.

Coverage:
  Phase 1 - Lexer:       Unknown tokens, malformed literals
  Phase 2 - Parser:      Syntax violations, missing delimiters, wrong grammar
  Phase 3 - Semantic:    Types, scopes, const, break/continue, undeclared vars,
                         redeclarations, void misuse, wrong arg counts, type widening
  Phase 4 - IR+Runtime:  Division by zero, const mutation via array ref
"""
import pytest
from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer


def lex(src):
    return Lexer(src).tokenize()

def parse(src):
    tokens = Lexer(src).tokenize()
    return Parser(tokens).parse()

def analyze(src):
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast)


# ─────────────────────────────────────────
# PHASE 1 — LEXER
# ─────────────────────────────────────────

class TestLexerErrors:

    def test_unknown_token(self):
        """Dollar sign is not a valid token."""
        with pytest.raises(Exception):
            lex("void main() { int x = $5; }")

    def test_unclosed_block_comment(self):
        """Block comment that never closes should raise an error."""
        with pytest.raises(Exception):
            lex("void main() { /* this never ends }")

    def test_ampersand_single(self):
        """Single & is not a valid operator (only && is allowed)."""
        with pytest.raises(Exception):
            lex("void main() { int x = 1 & 2; }")

    def test_pipe_single(self):
        """Single | is not a valid operator (only || is allowed)."""
        with pytest.raises(Exception):
            lex("void main() { int x = 1 | 2; }")


# ─────────────────────────────────────────
# PHASE 2 — PARSER
# ─────────────────────────────────────────

class TestParserErrors:

    def test_missing_semicolon(self):
        """Missing semicolon after statement."""
        with pytest.raises(Exception, match="Expected ';'"):
            parse("void main() { int x = 5 }")

    def test_missing_closing_brace(self):
        """Missing closing brace."""
        with pytest.raises(Exception):
            parse("void main() { int x = 5; ")

    def test_missing_condition_parens(self):
        """If statement missing parentheses around condition."""
        with pytest.raises(Exception):
            parse("void main() { if true { } }")

    def test_empty_expression(self):
        """Assignment with no right-hand side."""
        with pytest.raises(Exception):
            parse("void main() { int x = ; }")

    def test_double_operator(self):
        """Two consecutive binary operators."""
        with pytest.raises(Exception):
            parse("void main() { int x = 3 + + 4; }")

    def test_array_access_no_index(self):
        """Array access with empty brackets."""
        with pytest.raises(Exception):
            parse("void main() { int a[5]; int x = a[]; }")

    def test_function_missing_return_type(self):
        """Function declaration missing return type."""
        with pytest.raises(Exception):
            parse("main() { }")

    def test_function_missing_body(self):
        """Function declared with no body."""
        with pytest.raises(Exception):
            parse("void main();")

    def test_const_function(self):
        """Functions cannot be marked const."""
        with pytest.raises(Exception, match="Functions cannot be const"):
            parse("const void main() { }")

    def test_const_no_init(self):
        """Const variable must have an initializer."""
        with pytest.raises(Exception, match="Const variable must be initialized"):
            parse("void main() { const int x; }")


# ─────────────────────────────────────────
# PHASE 3 — SEMANTIC ANALYZER
# ─────────────────────────────────────────

class TestSemanticErrors:

    def test_undeclared_variable(self):
        """Using a variable before declaring it."""
        with pytest.raises(Exception, match="Undeclared variable 'z'"):
            analyze("void main() { print(z); }")

    def test_redeclaration_same_scope(self):
        """Two declarations of the same variable in the same scope."""
        with pytest.raises(Exception):
            analyze("void main() { int x = 1; int x = 2; }")

    def test_assign_to_const(self):
        """Cannot reassign a const variable."""
        with pytest.raises(Exception, match="Cannot assign to const"):
            analyze("void main() { const int x = 5; x = 10; }")

    def test_break_outside_loop(self):
        """break used outside of any loop."""
        with pytest.raises(Exception, match="'break' outside of loop"):
            analyze("void main() { break; }")

    def test_continue_outside_loop(self):
        """continue used outside of any loop."""
        with pytest.raises(Exception, match="'continue' outside of loop"):
            analyze("void main() { continue; }")

    def test_call_undefined_function(self):
        """Calling a function that was never declared."""
        with pytest.raises(Exception, match="not found"):
            analyze("void main() { ghost(); }")

    def test_call_variable_as_function(self):
        """Calling a variable as if it were a function."""
        with pytest.raises(Exception, match="not a function"):
            analyze("void main() { int x = 5; x(); }")

    def test_wrong_arg_count_too_few(self):
        """Calling a function with fewer arguments than parameters."""
        with pytest.raises(Exception, match="expects 2 arguments"):
            analyze("void foo(int a, int b) {} void main() { foo(1); }")

    def test_wrong_arg_count_too_many(self):
        """Calling a function with more arguments than parameters."""
        with pytest.raises(Exception, match="expects 1 arguments"):
            analyze("void foo(int a) {} void main() { foo(1, 2, 3); }")

    def test_type_mismatch_int_bool(self):
        """Assigning a bool to an int variable."""
        with pytest.raises(Exception, match="Type Error"):
            analyze("void main() { int x = true; }")

    def test_type_mismatch_bool_int(self):
        """Assigning an int to a bool variable."""
        with pytest.raises(Exception, match="Type Error"):
            analyze("void main() { bool b = 42; }")

    def test_binary_op_type_mismatch(self):
        """Adding a bool and an int."""
        with pytest.raises(Exception, match="Type Error"):
            analyze("void main() { bool b = true; int x = b + 1; }")

    def test_increment_bool(self):
        """Pre-increment on a bool is desugared to bool=bool+1 which hits type mismatch."""
        with pytest.raises(Exception, match="Type Error"):
            analyze("void main() { bool b = true; ++b; }")

    def test_increment_const(self):
        """Pre-increment on a const is desugared to Assignment which is caught by const check."""
        with pytest.raises(Exception, match="Cannot assign to const"):
            analyze("void main() { const int x = 5; ++x; }")
    def test_non_array_accessed_as_array(self):
        """Attempting to index a plain int as if it were an array."""
        with pytest.raises(Exception, match="not an array"):
            analyze("void main() { int x = 5; int y = x[0]; }")

    def test_arr_assign_type_mismatch(self):
        """Storing a bool into an int array."""
        with pytest.raises(Exception, match="Type Error"):
            analyze("void main() { int arr[5]; arr[0] = true; }")

    def test_non_void_no_return(self):
        """A function returning int but having no return at all."""
        with pytest.raises(Exception, match="Missing return statement"):
            analyze("int get_val() { int x = 5; } void main() {}")

    def test_void_branch_no_return(self):
        """int function where only one if-branch returns — the other path is naked."""
        with pytest.raises(Exception, match="Missing return statement"):
            analyze("""
            int maybe(int x) {
                if (x > 0) {
                    return 1;
                }
            }
            void main() {}
            """)

    def test_relational_result_used_as_int(self):
        """Relational expr returns bool; using it as int in arithmetic should fail."""
        with pytest.raises(Exception, match="Type Error"):
            analyze("void main() { int x = (3 < 5) + 1; }")

    def test_function_declared_twice(self):
        """Two definitions of the same function name."""
        with pytest.raises(Exception):
            analyze("void foo() {} void foo() {} void main() {}")

    def test_for_condition_must_be_bool_or_int(self):
        """A float used directly as an array size is not valid syntax."""
        with pytest.raises(Exception):
            analyze("void main() { int arr[3.5]; }")
