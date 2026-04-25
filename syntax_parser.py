from ASTNode import *


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    def current(self):
        return self.tokens[self.pos]

    def previous(self):
        return self.tokens[self.pos - 1]

    def is_at_end(self):
        return self.current().type == "EOF"

    def advance(self):
        if not self.is_at_end():
            self.pos += 1
        return self.previous()

    def check(self, token_type):
        if self.is_at_end():
            return False
        return self.current().type == token_type

    def match(self, *token_types):
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def consume(self, token_type, message):
        if self.check(token_type):
            return self.advance()
        self.error(self.current(), message)
        return None

    def error(self, token, message):
        error_msg = (
            f"Error sintáctico en línea {token.line}, columna {token.column}: "
            f"{message}. Se encontró '{token.lexeme}'"
        )
        self.errors.append(error_msg)

    # =========================
    # PUNTO DE ENTRADA
    # =========================
    def parse(self):
        return self.parse_program()

    # =========================
    # PROGRAMA Y SENTENCIAS
    # =========================
    def parse_program(self):
        statements = []

        while not self.is_at_end():
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
            else:
                self.advance()

        return ProgramNode(statements)

    def parse_statement(self):
        if self.check("LET"):
            return self.parse_var_decl()
        if self.check("DEF"):
            return self.parse_func_decl()
        if self.check("IF"):
            return self.parse_if_stmt()
        if self.check("WHILE"):
            return self.parse_while_stmt()
        if self.check("PRINT"):
            return self.parse_print_stmt()
        if self.check("RETURN"):
            return self.parse_return_stmt()

        return self.parse_expr_stmt()

    def parse_var_decl(self):
        self.consume("LET", "Se esperaba 'let'")
        name_token = self.consume("ID", "Se esperaba un identificador")
        self.consume("ASSIGN", "Se esperaba '='")
        value = self.parse_expression()
        self.consume("SEMICOLON", "Se esperaba ';'")

        if name_token is None:
            return None
        return VarDeclNode(name_token.lexeme, value)

    def parse_func_decl(self):
        self.consume("DEF", "Se esperaba 'def'")
        name_token = self.consume("ID", "Se esperaba el nombre de la función")
        self.consume("LPAREN", "Se esperaba '('")

        params = []
        if not self.check("RPAREN"):
            first_param = self.consume("ID", "Se esperaba un parámetro")
            if first_param is not None:
                params.append(first_param.lexeme)

            while self.match("COMMA"):
                param = self.consume("ID", "Se esperaba un parámetro")
                if param is not None:
                    params.append(param.lexeme)

        self.consume("RPAREN", "Se esperaba ')'")
        body = self.parse_block()

        if name_token is None:
            return None
        return FuncDefNode(name_token.lexeme, params, body)

    def parse_block(self):
        self.consume("LBRACE", "Se esperaba '{'")
        statements = []

        while not self.check("RBRACE") and not self.is_at_end():
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
            else:
                self.advance()

        self.consume("RBRACE", "Se esperaba '}'")
        return BlockNode(statements)

    def parse_if_stmt(self):
        self.consume("IF", "Se esperaba 'if'")
        condition = self.parse_expression()
        then_block = self.parse_block()

        else_block = None
        if self.match("ELSE"):
            else_block = self.parse_block()

        return IfNode(condition, then_block, else_block)

    def parse_while_stmt(self):
        self.consume("WHILE", "Se esperaba 'while'")
        condition = self.parse_expression()
        body = self.parse_block()

        return WhileNode(condition, body)

    def parse_print_stmt(self):
        self.consume("PRINT", "Se esperaba 'print'")
        self.consume("LPAREN", "Se esperaba '('")
        expr = self.parse_expression()
        self.consume("RPAREN", "Se esperaba ')'")
        self.consume("SEMICOLON", "Se esperaba ';'")

        return PrintNode(expr)

    def parse_return_stmt(self):
        self.consume("RETURN", "Se esperaba 'return'")
        expr = self.parse_expression()
        self.consume("SEMICOLON", "Se esperaba ';'")

        return ReturnNode(expr)

    def parse_expr_stmt(self):
        expr = self.parse_expression()
        self.consume("SEMICOLON", "Se esperaba ';'")
        return ExprStmtNode(expr)

    # =========================
    # EXPRESIONES
    # =========================
    def parse_expression(self):
        return self.parse_logical_or()

    def parse_logical_or(self):
        expr = self.parse_logical_and()

        while self.match("OR"):
            operator = self.previous().lexeme
            right = self.parse_logical_and()
            expr = BinOpNode(expr, operator, right)

        return expr

    def parse_logical_and(self):
        expr = self.parse_equality()

        while self.match("AND"):
            operator = self.previous().lexeme
            right = self.parse_equality()
            expr = BinOpNode(expr, operator, right)

        return expr

    def parse_equality(self):
        expr = self.parse_comparison()

        while self.match("EQ", "NEQ"):
            operator = self.previous().lexeme
            right = self.parse_comparison()
            expr = BinOpNode(expr, operator, right)

        return expr

    def parse_comparison(self):
        expr = self.parse_term()

        while self.match("LT", "GT", "LTE", "GTE"):
            operator = self.previous().lexeme
            right = self.parse_term()
            expr = BinOpNode(expr, operator, right)

        return expr

    def parse_term(self):
        expr = self.parse_factor()

        while self.match("PLUS", "MINUS"):
            operator = self.previous().lexeme
            right = self.parse_factor()
            expr = BinOpNode(expr, operator, right)

        return expr

    def parse_factor(self):
        expr = self.parse_power()

        while self.match("MULT", "DIV", "MOD"):
            operator = self.previous().lexeme
            right = self.parse_power()
            expr = BinOpNode(expr, operator, right)

        return expr

    def parse_power(self):
        expr = self.parse_unary()

        if self.match("POW"):
            operator = self.previous().lexeme
            right = self.parse_power()
            expr = BinOpNode(expr, operator, right)

        return expr

    def parse_unary(self):
        if self.match("NOT", "MINUS"):
            operator = self.previous().lexeme
            operand = self.parse_unary()
            return UnaryOpNode(operator, operand)

        return self.parse_primary()

    def parse_primary(self):
        if self.match("INT", "REAL"):
            return NumberNode(self.previous().lexeme)

        if self.match("STRING"):
            return StringNode(self.previous().lexeme)

        if self.match("TRUE"):
            return BoolNode(True)

        if self.match("FALSE"):
            return BoolNode(False)

        if self.match("ID"):
            name = self.previous().lexeme

            if self.match("LPAREN"):
                args = []

                if not self.check("RPAREN"):
                    args.append(self.parse_expression())

                    while self.match("COMMA"):
                        args.append(self.parse_expression())

                self.consume("RPAREN", "Se esperaba ')'")
                return FuncCallNode(name, args)

            return VariableNode(name)

        if self.match("LPAREN"):
            expr = self.parse_expression()
            self.consume("RPAREN", "Se esperaba ')'")
            return expr

        self.error(self.current(), "Se esperaba una expresión válida")
        return None