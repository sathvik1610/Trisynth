import pytest
from src.frontend.lexer import Lexer
from src.frontend.token_type import TokenType

def test_keywords_and_identifiers():
    lexer = Lexer("int count = 5; return count;")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.KW_INT
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].value == "count"
    assert tokens[2].type == TokenType.ASSIGN
    assert tokens[3].type == TokenType.INTEGER
    assert tokens[3].value == "5"
    assert tokens[4].type == TokenType.SEMICOLON
    assert tokens[5].type == TokenType.KW_RETURN
    assert tokens[6].type == TokenType.IDENTIFIER
    assert tokens[7].type == TokenType.SEMICOLON
    assert tokens[8].type == TokenType.EOF

def test_operators():
    lexer = Lexer("a <= b != c == d > 0")
    tokens = [t.type for t in lexer.tokenize()]
    expected = [
        TokenType.IDENTIFIER,
        TokenType.LTE,
        TokenType.IDENTIFIER,
        TokenType.NEQ,
        TokenType.IDENTIFIER,
        TokenType.EQ,
        TokenType.IDENTIFIER,
        TokenType.GT,
        TokenType.INTEGER,
        TokenType.EOF
    ]
    assert tokens == expected

def test_arrays():
    lexer = Lexer("int arr[10]; a = arr[5];")
    tokens = [t.type for t in lexer.tokenize()]
    assert TokenType.LBRACKET in tokens
    assert TokenType.RBRACKET in tokens

def test_invalid_char():
    lexer = Lexer("int x = 5 @ 2;")
    with pytest.raises(Exception, match="Lexical Error"):
        lexer.tokenize()
