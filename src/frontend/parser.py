from typing import List, Optional
from src.frontend.token_type import TokenType, Token
from src.frontend.lexer import Lexer
import src.frontend.ast as ast

class Parser:
    """
    Recursive Descent Parser for Trisynth.
    
    Responsibility:
    - Consumes a stream of Tokens.
    - Validates syntax against the language grammar.
    - specific methods (e.g., parse_program, parse_statement) correspond directly to grammar rules.
    - Constructs and returns an Abstract Syntax Tree (AST).
    """

    def __init__(self, tokens: List[Token]):
        """
        Initialize the parser with a list of tokens.
        """
        self.tokens = tokens
        self.pos = 0 # Current token index
        self.length = len(tokens)

    # --- Helper Methods ---

    def _peek(self, offset: int = 0) -> Token:
        """Return the token at the current position + offset."""
        if self.pos + offset >= self.length:
            return self.tokens[-1] # EOF
        return self.tokens[self.pos + offset]

    def _current(self) -> Token:
        return self._peek(0)

    def _advance(self) -> Token:
        """Consume the current token and move forward."""
        if self.pos < self.length:
            current = self.tokens[self.pos]
            self.pos += 1
            return current
        return self.tokens[-1]

    def _match(self, *types: TokenType) -> bool:
        """
        Check if the current token matches any of the given types.
        If it does, consume it and return True.
        """
        for type in types:
            if self._current().type == type:
                self._advance()
                return True
        return False
    
    # ... (skipping some methods) ...

    def parse_primary(self) -> ast.Expr:
        # print(f"PEEK PRIMARY: {self._current()}")
        if self._match(TokenType.INTEGER):
            return ast.Literal(int(self.tokens[self.pos-1].value), "int")


    def _consume(self, type: TokenType, message: str) -> Token:
        """
        Consume the current token if it matches the type.
        If not, raise a syntax error.
        """
        if self._current().type == type:
            return self._advance()
        raise Exception(f"Syntax Error at {self._current().line}:{self._current().column}: {message}")

    def _check(self, type: TokenType) -> bool:
        """Return True if current token matches type, without consuming."""
        if self._current().type == TokenType.EOF:
             return type == TokenType.EOF
        return self._current().type == type

    # --- Grammar Rules ---

    def parse(self) -> ast.Program:
        """
        Entry point.
        program ::= decl_list
        """
        declarations = []
        while not self._check(TokenType.EOF):
            declarations.append(self.parse_declaration())
        return ast.Program(declarations)

    def parse_declaration(self) -> ast.Stmt:
        """
        decl ::= var_decl | func_decl
        
        We distinguish by looking ahead.
        Both start with: type IDENTIFIER
        Function: type IDENTIFIER ( ...
        Variable: type IDENTIFIER = ... OR type IDENTIFIER ;
        """
        # Parse Type
        type_token = self._current()
        if type_token.type not in (TokenType.KW_INT, TokenType.KW_UINT32, TokenType.KW_FLOAT, 
                                   TokenType.KW_BOOL, TokenType.KW_CHAR, TokenType.KW_VOID):
             raise Exception(f"Expected type declaration at {type_token.line}:{type_token.column}")
        
        type_str = type_token.value
        self._advance() # Consume type

        # Parse Identifier
        name_token = self._consume(TokenType.IDENTIFIER, "Expected variable or function name.")
        name_str = name_token.value

        # Lookahead to distinguish var vs func
        if self._check(TokenType.LPAREN):
            return self.parse_function_decl(type_str, name_str)
        else:
            return self.parse_variable_decl(type_str, name_str)

    def parse_variable_decl(self, type_str: str, name_str: str) -> ast.VarDecl:
        """
        var_decl ::= type IDENTIFIER [ = expression ] ;
        """
        initializer = None
        if self._match(TokenType.ASSIGN):
            initializer = self.parse_expression()
        
        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration.")
        return ast.VarDecl(type_str, name_str, initializer)

    def parse_function_decl(self, return_type: str, name_str: str) -> ast.FunctionDecl:
        """
        func_decl ::= type IDENTIFIER ( param_list ) block
        """
        self._consume(TokenType.LPAREN, "Expected '(' after function name.")
        
        params = []
        if not self._check(TokenType.RPAREN):
            while True:
                # Param type
                pt_token = self._current()
                if pt_token.type not in (TokenType.KW_INT, TokenType.KW_UINT32, TokenType.KW_FLOAT, 
                                   TokenType.KW_BOOL, TokenType.KW_CHAR, TokenType.KW_VOID):
                     raise Exception(f"Expected parameter type at {pt_token.line}:{pt_token.column}")
                pt_str = pt_token.value
                self._advance()

                # Param name
                pn_token = self._consume(TokenType.IDENTIFIER, "Expected parameter name.")
                params.append((pt_str, pn_token.value))

                if not self._match(TokenType.COMMA):
                    break
        
        self._consume(TokenType.RPAREN, "Expected ')' after parameters.")
        
        body = self.parse_block()
        return ast.FunctionDecl(return_type, name_str, params, body)

    def parse_block(self) -> ast.Block:
        """block ::= { stmt_list }"""
        self._consume(TokenType.LBRACE, "Expected '{' to start block.")
        statements = []
        while not self._check(TokenType.RBRACE) and not self._check(TokenType.EOF):
            statements.append(self.parse_statement())
        self._consume(TokenType.RBRACE, "Expected '}' to end block.")
        return ast.Block(statements)

    def parse_statement(self) -> ast.Stmt:
        """
        stmt ::= block | if_stmt | while_stmt | for_stmt | return_stmt | expr_stmt | var_decl
        """
        if self._check(TokenType.LBRACE):
            return self.parse_block()
        if self._match(TokenType.KW_IF):
            return self.parse_if_statement()
        if self._match(TokenType.KW_WHILE):
            return self.parse_while_statement()
        if self._match(TokenType.KW_RETURN):
            return self.parse_return_statement()
        if self._match(TokenType.KW_PRINT):
            return self.parse_print_statement()
        
        # Check for variable declaration inside block
        # Lookahead for type keyword
        current_type = self._current().type
        if current_type in (TokenType.KW_INT, TokenType.KW_UINT32, TokenType.KW_FLOAT, 
                            TokenType.KW_BOOL, TokenType.KW_CHAR, TokenType.KW_VOID):
             return self.parse_declaration() # It's a local var decl

        return self.parse_expression_statement()

    def parse_if_statement(self) -> ast.IfStmt:
        """if_stmt ::= if ( expr ) stmt [ else stmt ]"""
        self._consume(TokenType.LPAREN, "Expected '(' after 'if'.")
        condition = self.parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after if condition.")
        
        then_branch = self.parse_statement()
        else_branch = None
        if self._match(TokenType.KW_ELSE):
            else_branch = self.parse_statement()
            
        return ast.IfStmt(condition, then_branch, else_branch)

    def parse_while_statement(self) -> ast.WhileStmt:
        """while_stmt ::= while ( expr ) stmt"""
        self._consume(TokenType.LPAREN, "Expected '(' after 'while'.")
        condition = self.parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after while condition.")
        
        body = self.parse_statement()
        return ast.WhileStmt(condition, body)

    def parse_return_statement(self) -> ast.ReturnStmt:
        """return_stmt ::= return [ expression ] ;"""
        value = None
        if not self._check(TokenType.SEMICOLON):
            value = self.parse_expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after return value.")
        return ast.ReturnStmt(value)

    def parse_print_statement(self) -> ast.PrintStmt:
        """print_stmt ::= print ( expression ) ;"""
        # 'print' already consumed by _match in parse_statement
        self._consume(TokenType.LPAREN, "Expected '(' after 'print'.")
        expr = self.parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after expression.")
        self._consume(TokenType.SEMICOLON, "Expected ';' after statement.")
        return ast.PrintStmt(expr)

    def parse_expression_statement(self) -> ast.ExprStmt:
        """expr_stmt ::= expression ;"""
        expr = self.parse_expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after expression.")
        return ast.ExprStmt(expr)

    # --- Expression Parsing (Precedence Climbing) ---

    def parse_expression(self) -> ast.Expr:
        """expression ::= assignment"""
        return self.parse_assignment()

    def parse_assignment(self) -> ast.Expr:
        """assignment ::= equality [ = assignment ]"""
        expr = self.parse_equality()

        if self._match(TokenType.ASSIGN):
            # The left side (expr) must be a valid assignment target (Variable)
            # For this simplified parser, we check if instance is Variable
            if isinstance(expr, ast.Variable):
                value = self.parse_assignment() # Recursive for right-associativity
                return ast.Assignment(expr.name, value)
            raise Exception("Invalid assignment target.")
        
        return expr

    # Precedence: Equality < Relational < Additive < Multiplicative < Unary < Primary

    def parse_equality(self) -> ast.Expr:
        return self._parse_binary(self.parse_relational, [TokenType.EQ, TokenType.NEQ])

    def parse_relational(self) -> ast.Expr:
        return self._parse_binary(self.parse_additive, [TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE])

    def parse_additive(self) -> ast.Expr:
        return self._parse_binary(self.parse_multiplicative, [TokenType.PLUS, TokenType.MINUS])

    def parse_multiplicative(self) -> ast.Expr:
        return self._parse_binary(self.parse_unary, [TokenType.STAR, TokenType.SLASH, TokenType.MODULO])

    def _parse_binary(self, next_precedence_func, operators: List[TokenType]) -> ast.Expr:
        expr = next_precedence_func()
        while self._current().type in operators:
            operator = self._advance().type
            right = next_precedence_func()
            expr = ast.BinaryExpr(expr, operator, right)
        return expr

    def parse_unary(self) -> ast.Expr:
        if self._match(TokenType.NOT, TokenType.MINUS):
            operator = self.tokens[self.pos - 1].type # Previous was consumed
            right = self.parse_unary()
            return ast.UnaryExpr(operator, right)
        return self.parse_call_or_primary()

    def parse_call_or_primary(self) -> ast.Expr:
        """Handles function calls or variable access."""
        expr = self.parse_primary()
        
        # If the primary expression is a variable, check for '(' to see if it's a call
        if isinstance(expr, ast.Variable) and self._match(TokenType.LPAREN):
            return self._finish_call(expr)
        
        return expr

    def _finish_call(self, callee: ast.Variable) -> ast.CallExpr:
        arguments = []
        if not self._check(TokenType.RPAREN):
            while True:
                arguments.append(self.parse_expression())
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RPAREN, "Expected ')' after arguments.")
        return ast.CallExpr(callee.name, arguments)

    def parse_primary(self) -> ast.Expr:
        if self._match(TokenType.INTEGER):
            return ast.Literal(int(self.tokens[self.pos-1].value), "int")
        if self._match(TokenType.FLOAT):
            return ast.Literal(float(self.tokens[self.pos-1].value), "float")
        if self._match(TokenType.KW_TRUE):
            return ast.Literal(True, "bool")
        if self._match(TokenType.KW_FALSE):
            return ast.Literal(False, "bool")
        if self._match(TokenType.IDENTIFIER):
            return ast.Variable(self.tokens[self.pos-1].value)
        
        if self._match(TokenType.LPAREN):
            expr = self.parse_expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression.")
            return expr

        raise Exception(f"Expected expression at {self._current().line}:{self._current().column}, found {self._current().type}")
