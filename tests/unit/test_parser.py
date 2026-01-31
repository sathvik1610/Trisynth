import pytest
from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
import src.frontend.ast as ast

def parse_source(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()

def test_var_decl():
    ast_root = parse_source("int x = 10;")
    assert len(ast_root.declarations) == 1
    decl = ast_root.declarations[0]
    assert isinstance(decl, ast.VarDecl)
    assert decl.type_name == "int"
    assert decl.name == "x"
    assert isinstance(decl.initializer, ast.Literal)
    assert decl.initializer.value == 10

def test_func_decl():
    source = """
    int add(int a, int b) {
        return a + b;
    }
    """
    ast_root = parse_source(source)
    decl = ast_root.declarations[0]
    assert isinstance(decl, ast.FunctionDecl)
    assert decl.name == "add"
    assert decl.return_type == "int"
    assert len(decl.params) == 2
    assert decl.params[0] == ("int", "a")
    assert decl.params[1] == ("int", "b")
    
    assert isinstance(decl.body, ast.Block)
    return_stmt = decl.body.statements[0]
    assert isinstance(return_stmt, ast.ReturnStmt)
    assert isinstance(return_stmt.value, ast.BinaryExpr)

def test_control_flow():
    source = """
    void main() {
        if (x > 0) {
            print(x);
        } else {
            return;
        }
        while (count < 10) {
            count = count + 1;
        }
    }
    """
    ast_root = parse_source(source)
    func = ast_root.declarations[0]
    body = func.body.statements
    
    # Check If
    if_stmt = body[0]
    assert isinstance(if_stmt, ast.IfStmt)
    assert isinstance(if_stmt.condition, ast.BinaryExpr)
    
    # Check PrintStmt inside block
    then_block = if_stmt.then_branch
    assert isinstance(then_block, ast.Block)
    assert len(then_block.statements) == 1
    assert isinstance(then_block.statements[0], ast.PrintStmt)
    
    # Check Else content
    assert isinstance(if_stmt.else_branch, ast.Block)
    
    # Check While
    while_stmt = body[1]
    assert isinstance(while_stmt, ast.WhileStmt)
    assert isinstance(while_stmt.condition, ast.BinaryExpr)

def test_expressions():
    # 1 + 2 * 3 should be 1 + (2 * 3) due to precedence
    source = "int x = 1 + 2 * 3;"
    ast_root = parse_source(source)
    init = ast_root.declarations[0].initializer
    
    assert isinstance(init, ast.BinaryExpr)
    assert init.left.value == 1 # 1
    
    right = init.right # 2 * 3
    assert isinstance(right, ast.BinaryExpr)
    assert right.left.value == 2
    assert right.right.value == 3

def test_syntax_error():
    source = "int x = ;" # Missing initializer
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    
    with pytest.raises(Exception) as excinfo:
        parser.parse()
    assert "Expected expression" in str(excinfo.value)
