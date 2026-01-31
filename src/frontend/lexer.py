import re
from typing import List, Optional
from src.frontend.token_type import TokenType, Token

class Lexer:
    """
    The Lexical Analyzer (Lexer) for the Trisynth Compiler.
    
    Responsibility:
    - Reads raw source code.
    - Converts it into a stream of Token objects.
    - Handles whitespace and comments.
    - Detects lexical errors (illegal characters).
    """

    def __init__(self, source_code: str):
        """
        Initialize the Lexer with source code.

        Args:
            source_code (str): The complete source code to be tokenized.
        """
        self.source_code = source_code
        self.length = len(source_code)
        self.tokens: List[Token] = []
        
        # Cursor position tracking
        self.pos = 0
        self.line = 1
        self.column = 1

    def _match(self, pattern: str) -> Optional[str]:
        """
        Try to match a regex pattern at the current position.
        
        Args:
            pattern (str): The regex pattern to match.
            
        Returns:
            Optional[str]: The matched text if successful, None otherwise.
        """
        # Compile user pattern to match from start of string
        regex = re.compile(pattern)
        match = regex.match(self.source_code, self.pos)
        if match:
            text = match.group(0)
            return text
        return None

    def _advance(self, length: int):
        """
        Advance the cursor position by a given length.
        Updates line and column counters.
        
        Args:
            length (int): Number of characters to advance.
        """
        text = self.source_code[self.pos : self.pos + length]
        for char in text:
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        self.pos += length

    def _add_token(self, type: TokenType, value: str):
        """
        Create a Token and add it to the list.
        
        Args:
            type (TokenType): The type of the token.
            value (str): The token's value.
        """
        # Use current line/col. Note: We might want the start position of the token.
        # Since _advance updates line/col, we should capture them BEFORE advance?
        # Ideally, the main loop loop captures start_line/start_column before matching.
        # But here valid tokens are added after matching.
        # Let's adjust logic in tokenize() to capture start pos.
        pass

    def tokenize(self) -> List[Token]:
        """
        Main method to tokenize the source code.
        
        Returns:
            List[Token]: A list of Token objects ending with EOF.
        
        Raises:
            Exception: If an illegal character is encountered.
        """
        self.tokens = []
        
        # Map of keywords string -> TokenType
        keywords = {
            "int": TokenType.KW_INT,
            "uint32": TokenType.KW_UINT32,
            "float": TokenType.KW_FLOAT,
            "bool": TokenType.KW_BOOL,
            "char": TokenType.KW_CHAR,
            "void": TokenType.KW_VOID,
            "if": TokenType.KW_IF,
            "else": TokenType.KW_ELSE,
            "while": TokenType.KW_WHILE,
            "for": TokenType.KW_FOR,
            "break": TokenType.KW_BREAK,
            "continue": TokenType.KW_CONTINUE,
            "return": TokenType.KW_RETURN,
            "print": TokenType.KW_PRINT,
            "readInt": TokenType.KW_READ_INT,
            "true": TokenType.KW_TRUE,
            "false": TokenType.KW_FALSE,
            "const": TokenType.KW_CONST,
        }

        # List of (Regex Pattern, TokenType OR None for complex handling)
        # Order matters! Longer matches should come first (urMaximal Munch).
        token_specs = [
            # Skip whitespace
            (r'[ \t\r\n]+', None),
            
            # Skip comments (Single line // ...)
            (r'//[^\n]*', None),

            # Numeric Literals
            (r'\d+\.\d+', TokenType.FLOAT), # Float before Int
            (r'\d+', TokenType.INTEGER),

            # Identifier (or Keyword)
            (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.IDENTIFIER),

            # Operators (Multi-char)
            (r'\+\+', TokenType.INCREMENT),
            (r'--', TokenType.DECREMENT),
            (r'==', TokenType.EQ),
            (r'!=', TokenType.NEQ),
            (r'<=', TokenType.LTE),
            (r'>=', TokenType.GTE),
            (r'&&', TokenType.AND),
            (r'\|\|', TokenType.OR),

            # Operators (Single-char)
            (r'\+', TokenType.PLUS),
            (r'-', TokenType.MINUS),
            (r'\*', TokenType.STAR),
            (r'/', TokenType.SLASH),
            (r'%', TokenType.MODULO),
            (r'=', TokenType.ASSIGN),
            (r'<', TokenType.LT),
            (r'>', TokenType.GT),
            (r'!', TokenType.NOT),

            # Delimiters
            (r'\(', TokenType.LPAREN),
            (r'\)', TokenType.RPAREN),
            (r'\{', TokenType.LBRACE),
            (r'\}', TokenType.RBRACE),
            (r'\[', TokenType.LBRACKET),
            (r'\]', TokenType.RBRACKET),
            (r';', TokenType.SEMICOLON),
            (r',', TokenType.COMMA),
            
            # Character Literal (basic support)
            (r"'[^']'", TokenType.CHAR), 
        ]

        while self.pos < self.length:
            matched = False
            
            # Capture start position of the potential token
            start_line = self.line
            start_col = self.column

            for pattern, token_type in token_specs:
                text = self._match(pattern)
                if text:
                    # If it's whitespace or comment (token_type is None), just skip
                    if token_type:
                        if token_type == TokenType.IDENTIFIER:
                            # Check if it's actually a keyword
                            final_type = keywords.get(text, TokenType.IDENTIFIER)
                            self.tokens.append(Token(final_type, text, start_line, start_col))
                        elif token_type == TokenType.CHAR:
                             # Strip quotes for value? Or keep them? Usually keep raw value in token.
                             self.tokens.append(Token(token_type, text, start_line, start_col))
                        else:
                            self.tokens.append(Token(token_type, text, start_line, start_col))
                    
                    self._advance(len(text))
                    matched = True
                    break
            
            if not matched:
                # If no pattern detected, it's an error
                char = self.source_code[self.pos]
                raise Exception(f"Lexical Error: Unexpected character '{char}' at {self.line}:{self.column}")

        # Add EOF token at the end
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens
