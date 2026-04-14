# This takes the stream of tokens and builds a proper hierarchical syntax tree.

from typing import List, Optional
from src.frontend.token_type import TokenType, Token
from src.frontend.lexer import Lexer
import src.frontend.ast as ast

class Parser:
\
\
\
\
\
\
\
\
       

    def __init__(self, tokens: List[Token]):
\
\
           
        # This initializes the base properties.
        self.tokens = tokens
        self.pos = 0                      
        self.length = len(tokens)

                            

    def _peek(self, offset: int = 0) -> Token:
                                                                
        # This handles the primary logic for peek operations.
        if self.pos + offset >= self.length:
            return self.tokens[-1]      
        return self.tokens[self.pos + offset]

    def _current(self) -> Token:
        # This handles the primary logic for current operations.
        return self._peek(0)

    def _advance(self) -> Token:
                                                         
        # This handles the primary logic for advance operations.
        if self.pos < self.length:
            current = self.tokens[self.pos]
            self.pos += 1
            return current
        return self.tokens[-1]

    def _match(self, *types: TokenType) -> bool:
\
\
\
           
        # This handles the primary logic for match operations.
        for type in types:
            if self._current().type == type:
                self._advance()
                return True
        return False
    
                                     

    def parse_primary(self) -> ast.Expr:
                                                   
        # This handles the primary logic for parse primary operations.
        if self._match(TokenType.INTEGER):
            return ast.Literal(int(self.tokens[self.pos-1].value), "int")


    def _consume(self, type: TokenType, message: str) -> Token:
\
\
\
           
        # This handles the primary logic for consume operations.
        if self._current().type == type:
            return self._advance()
        raise Exception(f"Syntax Error at {self._current().line}:{self._current().column}: {message}")

    def _check(self, type: TokenType) -> bool:
                                                                           
        # This handles the primary logic for check operations.
        if self._current().type == TokenType.EOF:
             return type == TokenType.EOF
        return self._current().type == type

                           

    def parse(self) -> ast.Program:
\
\
\
           
        # This handles the primary logic for parse operations.
        declarations = []
        while not self._check(TokenType.EOF):
            declarations.append(self.parse_declaration())
        return ast.Program(declarations)


    def parse_declaration(self) -> ast.Stmt:
\
\
           
        # This handles the primary logic for parse declaration operations.
        is_const = False
        if self._match(TokenType.KW_CONST):
            is_const = True

                    
        type_token = self._current()
        if type_token.type not in (TokenType.KW_INT, TokenType.KW_UINT32, TokenType.KW_FLOAT, 
                                   TokenType.KW_BOOL, TokenType.KW_CHAR, TokenType.KW_VOID, TokenType.KW_STRING):
             raise Exception(f"Expected type declaration at {type_token.line}:{type_token.column}")
        
        type_str = type_token.value
        self._advance()               

                          
        name_token = self._consume(TokenType.IDENTIFIER, "Expected variable or function name.")
        name_str = name_token.value

                                              
        if self._check(TokenType.LPAREN):
            if is_const:
                raise Exception("Functions cannot be const.")
            return self.parse_function_decl(type_str, name_str)
        else:
            return self.parse_variable_decl(type_str, name_str, is_const)

    def parse_variable_decl(self, type_str: str, name_str: str, is_const: bool = False) -> ast.Stmt:
\
\
\
           
                                                 
        # This handles the primary logic for parse variable decl operations.
        if self._match(TokenType.LBRACKET):
            if is_const:
                                                                                                                 
                                                                                                
                pass
            size_token = self._consume(TokenType.INTEGER, "Expected array size.")
            size = int(size_token.value)
            if size <= 0:
                raise Exception(f"Array size must be a positive integer at {size_token.line}:{size_token.column}")
            self._consume(TokenType.RBRACKET, "Expected ']' after array size.")
            self._consume(TokenType.SEMICOLON, "Expected ';' after array declaration.")
            return ast.ArrayDecl(type_str, name_str, size)

        initializer = None
        if self._match(TokenType.ASSIGN):
            initializer = self.parse_expression()
        elif is_const:
            raise Exception("Const variable must be initialized.")
        
        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration.")
        return ast.VarDecl(type_str, name_str, initializer, is_const)

    def parse_function_decl(self, return_type: str, name_str: str) -> ast.FunctionDecl:
\
\
           
        # This handles the primary logic for parse function decl operations.
        self._consume(TokenType.LPAREN, "Expected '(' after function name.")
        
        params = []
        if not self._check(TokenType.RPAREN):
            while True:
                            
                pt_token = self._current()
                if pt_token.type not in (TokenType.KW_INT, TokenType.KW_UINT32, TokenType.KW_FLOAT, 
                                   TokenType.KW_BOOL, TokenType.KW_CHAR, TokenType.KW_VOID, TokenType.KW_STRING):
                     raise Exception(f"Expected parameter type at {pt_token.line}:{pt_token.column}")
                pt_str = pt_token.value
                self._advance()

                            
                pn_token = self._consume(TokenType.IDENTIFIER, "Expected parameter name.")
                
                                                      
                if self._match(TokenType.LBRACKET):
                    self._consume(TokenType.RBRACKET, "Expected ']' after array parameter name.")
                    pt_str += "[]"

                params.append((pt_str, pn_token.value))

                if not self._match(TokenType.COMMA):
                    break
        
        self._consume(TokenType.RPAREN, "Expected ')' after parameters.")
        
        body = self.parse_block()
        return ast.FunctionDecl(return_type, name_str, params, body)

    def parse_block(self) -> ast.Block:
                                     
        # This handles the primary logic for parse block operations.
        self._consume(TokenType.LBRACE, "Expected '{' to start block.")
        statements = []
        while not self._check(TokenType.RBRACE) and not self._check(TokenType.EOF):
            statements.append(self.parse_statement())
        self._consume(TokenType.RBRACE, "Expected '}' to end block.")
        return ast.Block(statements)

    def parse_statement(self) -> ast.Stmt:
\
\
           
        # This handles the primary logic for parse statement operations.
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
        
                                                     
                                    
        current_type = self._current().type
        if current_type in (TokenType.KW_INT, TokenType.KW_UINT32, TokenType.KW_FLOAT, 
                            TokenType.KW_BOOL, TokenType.KW_CHAR, TokenType.KW_VOID,
                            TokenType.KW_CONST, TokenType.KW_STRING):
             return self.parse_declaration()                        

        return self.parse_expression_statement()

    def parse_for_statement(self) -> ast.ForStmt:
                                                                  
        # This handles the primary logic for parse for statement operations.
        self._consume(TokenType.LPAREN, "Expected '(' after 'for'.")
        
                                        
        init = None
        if not self._match(TokenType.SEMICOLON):
                                   
            current_type = self._current().type
            if current_type in (TokenType.KW_INT, TokenType.KW_UINT32, TokenType.KW_FLOAT,
                                TokenType.KW_BOOL, TokenType.KW_CHAR, TokenType.KW_VOID, TokenType.KW_STRING):
                 init = self.parse_declaration()                     
            else:
                 init = self.parse_expression_statement()                     
        
                   
        condition = None
        if not self._check(TokenType.SEMICOLON):
            condition = self.parse_expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after for condition.")
        
                
        update = None
        if not self._check(TokenType.RPAREN):
            update = self.parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after for clauses.")
        
        body = self.parse_statement()
        return ast.ForStmt(init, condition, update, body)

    def parse_if_statement(self) -> ast.IfStmt:
                                                        
        # This handles the primary logic for parse if statement operations.
        self._consume(TokenType.LPAREN, "Expected '(' after 'if'.")
        condition = self.parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after if condition.")
        
        then_branch = self.parse_statement()
        else_branch = None
        if self._match(TokenType.KW_ELSE):
            else_branch = self.parse_statement()
            
        return ast.IfStmt(condition, then_branch, else_branch)

    def parse_while_statement(self) -> ast.WhileStmt:
                                                
        # This handles the primary logic for parse while statement operations.
        self._consume(TokenType.LPAREN, "Expected '(' after 'while'.")
        condition = self.parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after while condition.")
        
        body = self.parse_statement()
        return ast.WhileStmt(condition, body)

    def parse_return_statement(self) -> ast.ReturnStmt:
                                                     
        # This handles the primary logic for parse return statement operations.
        value = None
        if not self._check(TokenType.SEMICOLON):
            value = self.parse_expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after return value.")
        return ast.ReturnStmt(value)

    def parse_print_statement(self) -> ast.PrintStmt:
                                                   
                                                               
        # This handles the primary logic for parse print statement operations.
        self._consume(TokenType.LPAREN, "Expected '(' after 'print'.")
        expr = self.parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after expression.")
        self._consume(TokenType.SEMICOLON, "Expected ';' after statement.")
        return ast.PrintStmt(expr)

    def parse_expression_statement(self) -> ast.ExprStmt:
                                        
        # This handles the primary logic for parse expression statement operations.
        expr = self.parse_expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after expression.")
        return ast.ExprStmt(expr)

                                                      

    def parse_expression(self) -> ast.Expr:
                                       
        # This handles the primary logic for parse expression operations.
        return self.parse_assignment()

    def parse_assignment(self) -> ast.Expr:
                                                        
        # This handles the primary logic for parse assignment operations.
        expr = self.parse_logical_or()

        if self._match(TokenType.ASSIGN):
                                                                                              
            if isinstance(expr, (ast.Variable, ast.ArrayAccess)):
                value = self.parse_assignment()
                                                                                                       
                                                                        
                                                                                   
                                                                               
                                                              
                                                                                
                                                    
                                                                            
                                                                                                   
                                                                                                   
                                                                       
                                                                                                          
                                                            
                                                                                        
                                                               
                                                                   
                if isinstance(expr, ast.Variable):
                    return ast.Assignment(expr.name, value)
                elif isinstance(expr, ast.ArrayAccess):
                    return ast.ArrayAssignment(expr.name, expr.index, value)
            raise Exception("Invalid assignment target.")
        
        return expr

    def parse_logical_or(self) -> ast.Expr:
        # This handles the primary logic for parse logical or operations.
        expr = self.parse_logical_and()
        while self._match(TokenType.OR):
            operator = self.tokens[self.pos-1].type
            right = self.parse_logical_and()
            expr = ast.LogicalExpr(expr, operator, right)
        return expr

    def parse_logical_and(self) -> ast.Expr:
        # This handles the primary logic for parse logical and operations.
        expr = self.parse_equality()
        while self._match(TokenType.AND):
            operator = self.tokens[self.pos-1].type
            right = self.parse_equality()
            expr = ast.LogicalExpr(expr, operator, right)
        return expr

    def parse_equality(self) -> ast.Expr:
        # This handles the primary logic for parse equality operations.
        return self._parse_binary(self.parse_relational, [TokenType.EQ, TokenType.NEQ])

    def parse_relational(self) -> ast.Expr:
        # This handles the primary logic for parse relational operations.
        return self._parse_binary(self.parse_shift, [TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE])

    def parse_shift(self) -> ast.Expr:
        # This handles the primary logic for parse shift operations.
        return self._parse_binary(self.parse_additive, [TokenType.LSHIFT, TokenType.RSHIFT])

    def parse_additive(self) -> ast.Expr:
        # This handles the primary logic for parse additive operations.
        return self._parse_binary(self.parse_multiplicative, [TokenType.PLUS, TokenType.MINUS])

    def parse_multiplicative(self) -> ast.Expr:
        # This handles the primary logic for parse multiplicative operations.
        return self._parse_binary(self.parse_unary, [TokenType.STAR, TokenType.SLASH, TokenType.MODULO])

    def _parse_binary(self, next_precedence_func, operators: List[TokenType]) -> ast.Expr:
        # This handles the primary logic for parse binary operations.
        expr = next_precedence_func()
        while self._current().type in operators:
            operator = self._advance().type
            right = next_precedence_func()
            expr = ast.BinaryExpr(expr, operator, right)
        return expr

    def parse_unary(self) -> ast.Expr:
                                                        
        # This handles the primary logic for parse unary operations.
        if self._match(TokenType.INCREMENT, TokenType.DECREMENT):
            operator = self.tokens[self.pos - 1].type
                                         
                                                                                                  
                                                
            operand = self.parse_call_or_primary() 
            
                                                                                       
                                                                        
                                                                       
                                                    
                                                                                      
            
            if isinstance(operand, ast.Variable):
                var_name = operand.name
                one = ast.Literal(1, "int")
                op = TokenType.PLUS if operator == TokenType.INCREMENT else TokenType.MINUS
                binary = ast.BinaryExpr(operand, op, one)
                return ast.Assignment(var_name, binary)
            elif isinstance(operand, ast.ArrayAccess):
                                                                                            
                                                                                                        
                                                                  
                                                                                 
                                               
                pass                                   
            else:
                 raise Exception("Increment/Decrement requires a variable.")
            
            return ast.UnaryExpr(operator, operand)

        if self._match(TokenType.NOT, TokenType.MINUS):
            operator = self.tokens[self.pos - 1].type                        
            right = self.parse_unary()
            return ast.UnaryExpr(operator, right)
        return self.parse_call_or_primary()

    def parse_call_or_primary(self) -> ast.Expr:
                                                                        
        # This handles the primary logic for parse call or primary operations.
        expr = self.parse_primary()
        
                                    
        if self._check(TokenType.LPAREN):
            self._consume(TokenType.LPAREN, "Expected '(' after function name.")
            if isinstance(expr, ast.Variable):
                return self._finish_call(expr)
                                                                     

                                   
        if self._match(TokenType.LBRACKET):
            if isinstance(expr, ast.Variable):
                 index = self.parse_expression()
                 self._consume(TokenType.RBRACKET, "Expected ']' after array index.")
                                                                                        
                                                              
                                         
                 return ast.ArrayAccess(expr.name, index)
            else:
                 raise Exception(f"Expected array name before '[', found {expr}")
        
        return expr

    def _finish_call(self, callee: ast.Variable) -> ast.CallExpr:
        # This handles the primary logic for finish call operations.
        arguments = []
        if not self._check(TokenType.RPAREN):
            while True:
                arguments.append(self.parse_expression())
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RPAREN, "Expected ')' after arguments.")
        return ast.CallExpr(callee.name, arguments)

    def parse_primary(self) -> ast.Expr:
        # This handles the primary logic for parse primary operations.
        if self._match(TokenType.INTEGER):
            return ast.Literal(int(self.tokens[self.pos-1].value), "int")
        if self._match(TokenType.FLOAT):
            return ast.Literal(float(self.tokens[self.pos-1].value), "float")
        if self._match(TokenType.STRING):
            return ast.StringLiteral(self.tokens[self.pos-1].value)
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
