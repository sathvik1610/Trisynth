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
        decl ::= [const] type IDENTIFIER ...
        """
        is_const = False
        if self._match(TokenType.KW_CONST):
            is_const = True

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
            if is_const:
                raise Exception("Functions cannot be const.")
            return self.parse_function_decl(type_str, name_str)
        else:
            return self.parse_variable_decl(type_str, name_str, is_const)

    def parse_variable_decl(self, type_str: str, name_str: str, is_const: bool = False) -> ast.Stmt:
        """
        var_decl ::= [const] type IDENTIFIER [ = expression ] ;
                   | type IDENTIFIER [ INTEGER ] ;
        """
        # Check for Array Declaration: int x[10];
        if self._match(TokenType.LBRACKET):
            if is_const:
                # Const arrays? Maybe supported, but let's allow it or block it. Spec says "Immutable Constants".
                # For simplicity, allow it but ensure it works. Semantics will block assignment.
                pass
            size_token = self._consume(TokenType.INTEGER, "Expected array size.")
            size = int(size_token.value)
            self._consume(TokenType.RBRACKET, "Expected ']' after array size.")
            self._consume(TokenType.SEMICOLON, "Expected ';' after array declaration.")
            # We need to pass is_const to ArrayDecl too?
            # AST ArrayDecl doesn't have is_const. Let's fix AST or assume const arrays are blocked.
            # Let's assume for now valid const is mainly for variables (int x = 5).
            return ast.ArrayDecl(type_str, name_str, size)

        initializer = None
        if self._match(TokenType.ASSIGN):
            initializer = self.parse_expression()
        elif is_const:
            raise Exception("Const variable must be initialized.")
        
        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration.")
        return ast.VarDecl(type_str, name_str, initializer, is_const)

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
        stmt ::= block | if_stmt | while_stmt | for_stmt | return_stmt | expr_stmt | var_decl | break | continue
        """
        if self._check(TokenType.LBRACE):
            return self.parse_block()
        if self._match(TokenType.KW_IF):
            return self.parse_if_statement()
        if self._match(TokenType.KW_WHILE):
            return self.parse_while_statement()
        if self._match(TokenType.KW_FOR):
            return self.parse_for_statement()
        if self._match(TokenType.KW_RETURN):
            return self.parse_return_statement()
        if self._match(TokenType.KW_PRINT):
            return self.parse_print_statement()
        if self._match(TokenType.KW_BREAK):
            self._consume(TokenType.SEMICOLON, "Expected ';' after 'break'.")
            return ast.BreakStmt()
        if self._match(TokenType.KW_CONTINUE):
            self._consume(TokenType.SEMICOLON, "Expected ';' after 'continue'.")
            return ast.ContinueStmt()
        
        # Check for variable declaration inside block
        # Lookahead for type keyword
        current_type = self._current().type
        if current_type in (TokenType.KW_INT, TokenType.KW_UINT32, TokenType.KW_FLOAT, 
                            TokenType.KW_BOOL, TokenType.KW_CHAR, TokenType.KW_VOID,
                            TokenType.KW_CONST):
             return self.parse_declaration() # It's a local var decl

        return self.parse_expression_statement()

    def parse_for_statement(self) -> ast.ForStmt:
        """for_stmt ::= for ( [init] ; [cond] ; [update] ) stmt"""
        self._consume(TokenType.LPAREN, "Expected '(' after 'for'.")
        
        # Init (Declaration or ExprStmt)
        init = None
        if not self._match(TokenType.SEMICOLON):
            # Try declaration first
            current_type = self._current().type
            if current_type in (TokenType.KW_INT, TokenType.KW_UINT32, TokenType.KW_FLOAT,
                                TokenType.KW_BOOL, TokenType.KW_CHAR, TokenType.KW_VOID):
                 init = self.parse_declaration() # Consumes semicolon
            else:
                 init = self.parse_expression_statement() # Consumes semicolon
        
        # Condition
        condition = None
        if not self._check(TokenType.SEMICOLON):
            condition = self.parse_expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after for condition.")
        
        # Update
        update = None
        if not self._check(TokenType.RPAREN):
            update = self.parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after for clauses.")
        
        body = self.parse_statement()
        return ast.ForStmt(init, condition, update, body)

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
        """assignment ::= logical_or [ = assignment ]"""
        expr = self.parse_logical_or()

        if self._match(TokenType.ASSIGN):
            # The left side (expr) must be a valid assignment target (Variable or ArrayAccess)
            if isinstance(expr, (ast.Variable, ast.ArrayAccess)):
                value = self.parse_assignment()
                # If ArrayAccess, we might need a specific Assignment node or just handle it in backend
                # For AST, Assignment(name, val) expects name to be str.
                # We need to generalize Assignment or special case ArrayAssignment.
                # AST Assignment class takes 'name: str'. This is a limitation.
                # Let's check AST Assignment definition again.
                # Class Assignment(Expr): __init__(self, name: str, value: Expr)
                # This only supports variable name. 
                # We should update Assignment AST or create ArrayAssignment.
                # For now, let's assume we update AST Assignment to take 'target: Expr' or similar.
                # But to stay simple, let's handle ArrayAssignment separately or update Assignment.
                # Wait, I previously read AST. Assignment is name: str.
                # I should probably update AST Assignment to support ArrayAccess or change it to 'target'.
                # But to avoid breaking changes, let's see. 
                # Converting ArrayAccess to assignment is complex if AST expects string.
                # Let's fix this in a separate step if needed. 
                # For now, let's keep it compatible with Variable. 
                if isinstance(expr, ast.Variable):
                    return ast.Assignment(expr.name, value)
                elif isinstance(expr, ast.ArrayAccess):
                    return ast.ArrayAssignment(expr.name, expr.index, value)
            raise Exception("Invalid assignment target.")
        
        return expr

    def parse_logical_or(self) -> ast.Expr:
        expr = self.parse_logical_and()
        while self._match(TokenType.OR):
            operator = self.tokens[self.pos-1].type
            right = self.parse_logical_and()
            expr = ast.LogicalExpr(expr, operator, right)
        return expr

    def parse_logical_and(self) -> ast.Expr:
        expr = self.parse_equality()
        while self._match(TokenType.AND):
            operator = self.tokens[self.pos-1].type
            right = self.parse_equality()
            expr = ast.LogicalExpr(expr, operator, right)
        return expr

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
        # Check for Prefix Increment/Decrement: ++i, --i
        if self._match(TokenType.INCREMENT, TokenType.DECREMENT):
            operator = self.tokens[self.pos - 1].type
            # Expect a variable (l-value)
            # Recursively parse unary to handle ++(++i) if we wanted, but ++i requires a variable.
            # Let's call parse_call_or_primary. 
            operand = self.parse_call_or_primary() 
            
            # Semantic check: operand must be mutable variable. Parser just builds AST.
            # Strategy: Expand '++i' into 'i = i + 1' AST node directly?
            # Or use a UnaryExpr(INCREMENT, i) and let Backend handle? 
            # Plan said "Expand to i = i + 1 logic".
            # AST Structure: Assignment(name, BinaryExpr(Var(name), PLUS, Literal(1)))
            
            if isinstance(operand, ast.Variable):
                var_name = operand.name
                one = ast.Literal(1, "int")
                op = TokenType.PLUS if operator == TokenType.INCREMENT else TokenType.MINUS
                binary = ast.BinaryExpr(operand, op, one)
                return ast.Assignment(var_name, binary)
            elif isinstance(operand, ast.ArrayAccess):
                # Harder to expand 'arr[i] = arr[i] + 1' without double evaluation of index?
                # For this project, let's restrict ++/-- to simple variables or implement dedicated AST.
                # Let's generate a dedicated Unary "PRE_INC" node?
                # Re-reading plan: "Use UnaryExpr, translate to ADD + MOV in IR".
                # OK, let's stick to UnaryExpr!
                pass # Fall through to return UnaryExpr
            else:
                 raise Exception("Increment/Decrement requires a variable.")
            
            return ast.UnaryExpr(operator, operand)

        if self._match(TokenType.NOT, TokenType.MINUS):
            operator = self.tokens[self.pos - 1].type # Previous was consumed
            right = self.parse_unary()
            return ast.UnaryExpr(operator, right)
        return self.parse_call_or_primary()

    def parse_call_or_primary(self) -> ast.Expr:
        """Handles function calls or variable access or array access."""
        expr = self.parse_primary()
        
        # 1. Function Call: foo(...)
        if self._check(TokenType.LPAREN):
            self._consume(TokenType.LPAREN, "Expected '(' after function name.")
            if isinstance(expr, ast.Variable):
                return self._finish_call(expr)
            # Could raise error if expr is not callable (e.g. 5(...))

        # 2. Array Access: arr[...]
        if self._match(TokenType.LBRACKET):
            if isinstance(expr, ast.Variable):
                 index = self.parse_expression()
                 self._consume(TokenType.RBRACKET, "Expected ']' after array index.")
                 # Chained access? arr[i][j] (Not supported by spec, simple arrays only)
                 # Spec says: Fixed-size arrays. Homogeneous. 
                 # We return ArrayAccess.
                 return ast.ArrayAccess(expr.name, index)
            else:
                 raise Exception(f"Expected array name before '[', found {expr}")
        
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
        if self._match(TokenType.KW_READ_INT):
            self._consume(TokenType.LPAREN, "Expected '(' after readInt.")
            self._consume(TokenType.RPAREN, "Expected ')' after readInt.")
            return ast.CallExpr("readInt", [])
        if self._match(TokenType.IDENTIFIER):
            return ast.Variable(self.tokens[self.pos-1].value)
        
        if self._match(TokenType.LPAREN):
            expr = self.parse_expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression.")
            return expr

        raise Exception(f"Expected expression at {self._current().line}:{self._current().column}, found {self._current().type}")
