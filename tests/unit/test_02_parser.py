import pytest
from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
import src.frontend.ast as ast

def _parse(code):
    return Parser(Lexer(code).tokenize()).parse()

def test_basic_assignment():
    prog = _parse("int x = 5;")
    assert isinstance(prog, ast.Program)
    assert len(prog.declarations) == 1
    decl = prog.declarations[0]
    assert isinstance(decl, ast.VarDecl)
    assert decl.name == "x"
    assert decl.type_name == "int"
    assert isinstance(decl.initializer, ast.Literal)
    assert decl.initializer.value == 5

def test_operator_precedence():
    prog = _parse("int x = 1 + 2 * 3;")
    expr = prog.declarations[0].initializer
    assert isinstance(expr, ast.BinaryExpr)
    assert expr.operator.name == "PLUS"
    assert isinstance(expr.right, ast.BinaryExpr)
    assert expr.right.operator.name == "STAR"

def test_control_structures():
    prog = _parse("void main() { if (x > 0) { x = x - 1; } else { x = 0; } }")
    func_decl = prog.declarations[0]
    if_stmt = func_decl.body.statements[0]
    assert isinstance(if_stmt, ast.IfStmt)
    assert isinstance(if_stmt.condition, ast.BinaryExpr)
    assert isinstance(if_stmt.then_branch, ast.Block)
    assert isinstance(if_stmt.else_branch, ast.Block)

def test_array_declaration_and_access():
    prog = _parse("void main() { int arr[5]; arr[0] = 10; print(arr[0]); }")
    func_decl = prog.declarations[0]
    arr_decl, arr_assign, print_stmt = func_decl.body.statements
    assert isinstance(arr_decl, ast.ArrayDecl)
    assert arr_decl.size == 5
    assert isinstance(arr_assign, ast.ExprStmt)
    assert isinstance(arr_assign.expression, ast.ArrayAssignment)
    assert isinstance(print_stmt, ast.PrintStmt)
    assert isinstance(print_stmt.expression, ast.ArrayAccess)

def test_syntax_error():
    with pytest.raises(Exception, match="Expected"):
        _parse("int x = ;")

def test_const_array_declaration_keeps_const_flag():
    program = Parser(Lexer("const int a[3]; int b[2]; void main() {}").tokenize()).parse()
    assert program.declarations[0].is_const is True
    assert program.declarations[1].is_const is False

def test_nested_function_declaration_rejected():
    for code in ("void main() { void helper() { print(1); } helper(); }",
                 "void main() { int f() { return 1; } print(f()); }",
                 "void main() { if (true) { int g() { return 2; } } }"):
        with pytest.raises(Exception, match="cannot be declared inside"):
            _parse(code)

def test_top_level_functions_and_local_variables_still_parse():
    program = _parse("int f() { return 1; } void main() { int x = f(); }")
    assert len(program.declarations) == 2

def test_calling_a_non_function_gives_clear_error():
    with pytest.raises(Exception, match="Only a function name can be called"):
        _parse("void main() { int x = 5 (3); }")
