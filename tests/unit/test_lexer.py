import pytest
from src.frontend.lexer import Lexer
from src.frontend.token_type import TokenType, Token

def assert_token(token, type, value, line=None, col=None):
    assert token.type == type
    assert token.value == value
    if line: assert token.line == line
    if col: assert token.column == col

def test_empty_source():
    lexer = Lexer("")
    tokens = lexer.tokenize()
    assert len(tokens) == 1
    assert_token(tokens[0], TokenType.EOF, "")

def test_numbers():
    source = "123 45.67"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    assert len(tokens) == 3
    assert_token(tokens[0], TokenType.INTEGER, "123")
    assert_token(tokens[1], TokenType.FLOAT, "45.67")
    assert_token(tokens[2], TokenType.EOF, "")

def test_operators():
    source = "+ - * / % = == != < > <= >= && || !"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    expected_types = [
        TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.MODULO,
        TokenType.ASSIGN, TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT, 
        TokenType.LTE, TokenType.GTE, TokenType.AND, TokenType.OR, TokenType.NOT
    ]
    assert len(tokens) == len(expected_types) + 1
    for i, type in enumerate(expected_types):
        assert tokens[i].type == type

def test_keywords_and_identifiers():
    source = "int x = 10; if (x > 5) return;"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    expected = [
        (TokenType.KW_INT, "int"),
        (TokenType.IDENTIFIER, "x"),
        (TokenType.ASSIGN, "="),
        (TokenType.INTEGER, "10"),
        (TokenType.SEMICOLON, ";"),
        (TokenType.KW_IF, "if"),
        (TokenType.LPAREN, "("),
        (TokenType.IDENTIFIER, "x"),
        (TokenType.GT, ">"),
        (TokenType.INTEGER, "5"),
        (TokenType.RPAREN, ")"),
        (TokenType.KW_RETURN, "return"),
        (TokenType.SEMICOLON, ";"),
        (TokenType.EOF, "")
    ]
    
    assert len(tokens) == len(expected)
    for i, (type, val) in enumerate(expected):
        assert_token(tokens[i], type, val)

def test_comments():
    source = """
    int x = 1; // This is a specific comment
    // Another comment line
    int y = 2;
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    # int, x, =, 1, ;, int, y, =, 2, ; EOF
    assert len(tokens) == 11 
    assert_token(tokens[0], TokenType.KW_INT, "int")
    assert_token(tokens[4], TokenType.SEMICOLON, ";")
    assert_token(tokens[5], TokenType.KW_INT, "int")

def test_multiline_positions():
    source = "a\nb\n  c"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    assert_token(tokens[0], TokenType.IDENTIFIER, "a", line=1, col=1)
    assert_token(tokens[1], TokenType.IDENTIFIER, "b", line=2, col=1)
    assert_token(tokens[2], TokenType.IDENTIFIER, "c", line=3, col=3)

def test_unknown_char():
    source = "int $ var;"
    lexer = Lexer(source)
    with pytest.raises(Exception) as excinfo:
        lexer.tokenize()
    assert "Unexpected character '$'" in str(excinfo.value)
