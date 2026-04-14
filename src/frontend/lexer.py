# This part of the code is responsible for reading the raw text you type and chunking it out into recognizable tokens that we can parse later.

import re
from typing import List, Optional
from src.frontend.token_type import TokenType, Token

class Lexer:
\
\
\
\
\
\
\
\
       

    def __init__(self, source_code: str):
\
\
\
\
\
           
        # This initializes the base properties.
        self.source_code = source_code
        self.length = len(source_code)
        self.tokens: List[Token] = []
        
                                  
        self.pos = 0
        self.line = 1
        self.column = 1

    def _match(self, pattern: str) -> Optional[str]:
\
\
\
\
\
\
\
\
           
                                                            
        # This handles the primary logic for match operations.
        regex = re.compile(pattern)
        match = regex.match(self.source_code, self.pos)
        if match:
            text = match.group(0)
            return text
        return None

    def _advance(self, length: int):
\
\
\
\
\
\
           
        # This handles the primary logic for advance operations.
        text = self.source_code[self.pos : self.pos + length]
        for char in text:
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        self.pos += length

    def _add_token(self, type: TokenType, value: str):
\
\
\
\
\
\
           
                                                                                    
                                                                                 
                                                                                       
                                                         
                                                                
        # This handles the primary logic for add token operations.
        pass

    def tokenize(self) -> List[Token]:
\
\
\
\
\
\
\
\
           
        # This handles the primary logic for tokenize operations.
        self.tokens = []
        
                                             
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
            "string": TokenType.KW_STRING,
        }

                                                                         
                                                                            
        token_specs = [
                             
            (r'[ \t\r\n]+', None),

                                       
            (r'//[^\n]*', None),

                                                       
            (r'/\*.*?\*/', None),                                                        

                              
            (r'\d+\.\d+', TokenType.FLOAT),
            (r'\d+', TokenType.INTEGER),

                                     
            (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.IDENTIFIER),

                                                                 
            (r'\+\+', TokenType.INCREMENT),
            (r'--', TokenType.DECREMENT),
            (r'==', TokenType.EQ),
            (r'!=', TokenType.NEQ),
            (r'<=', TokenType.LTE),
            (r'>=', TokenType.GTE),
            (r'<<', TokenType.LSHIFT),
            (r'>>', TokenType.RSHIFT),
            (r'&&', TokenType.AND),
            (r'\|\|', TokenType.OR),

                                   
            (r'\+', TokenType.PLUS),
            (r'-', TokenType.MINUS),
            (r'\*', TokenType.STAR),
            (r'/', TokenType.SLASH),
            (r'%', TokenType.MODULO),
            (r'=', TokenType.ASSIGN),
            (r'<', TokenType.LT),
            (r'>', TokenType.GT),
            (r'!', TokenType.NOT),

                        
            (r'\(', TokenType.LPAREN),
            (r'\)', TokenType.RPAREN),
            (r'\{', TokenType.LBRACE),
            (r'\}', TokenType.RBRACE),
            (r'\[', TokenType.LBRACKET),
            (r'\]', TokenType.RBRACKET),
            (r';', TokenType.SEMICOLON),
            (r',', TokenType.COMMA),

                            
            (r'"[^"\\]*(\\.[^"\\]*)*"', TokenType.STRING),

                               
            (r"'[^']'", TokenType.CHAR),
        ]

        while self.pos < self.length:
            matched = False

                                                                         
            if self.source_code[self.pos:self.pos+2] == '/*':
                end = self.source_code.find('*/', self.pos + 2)
                if end == -1:
                    raise Exception(f"Lexical Error: Unclosed block comment starting at {self.line}:{self.column}")
                text = self.source_code[self.pos:end+2]
                self._advance(len(text))
                continue

            start_line = self.line
            start_col = self.column

            for pattern, token_type in token_specs:
                text = self._match(pattern)
                if text:
                                                                                   
                    if token_type:
                        if token_type == TokenType.IDENTIFIER:
                                                              
                            final_type = keywords.get(text, TokenType.IDENTIFIER)
                            self.tokens.append(Token(final_type, text, start_line, start_col))
                        elif token_type == TokenType.CHAR:
                                                                                                     
                             self.tokens.append(Token(token_type, text, start_line, start_col))
                        elif token_type == TokenType.STRING:
                                                    
                             value = text[1:-1]
                             self.tokens.append(Token(token_type, value, start_line, start_col))
                        else:
                            self.tokens.append(Token(token_type, text, start_line, start_col))
                    
                    self._advance(len(text))
                    matched = True
                    break
            
            if not matched:
                                                       
                char = self.source_code[self.pos]
                raise Exception(f"Lexical Error: Unexpected character '{char}' at {self.line}:{self.column}")

                                  
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens
