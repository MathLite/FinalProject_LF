from ASTNode import *


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    # =========================
    # UTILIDADES BÁSICAS
    # =========================
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
            "Error sintáctico en línea {}, columna {}: {}. "
            "Se encontró '{}'"
        ).format(token.line, token.column, message, token.lexeme)

        self.errors.append(error_msg)

    def synchronize(self):
        if not self.is_at_end():
            self.advance()

        while not self.is_at_end():

            if self.previous().type == "NEWLINE":
                return

            if self.current().type in (
                "LET", "DEF", "IF", "WHILE",
                "PRINT", "RETURN", "RBRACE"
            ):
                return

            self.advance()

    def skip_newlines(self):
        while self.match("NEWLINE"):
            pass

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

        self.skip_newlines()

        while not self.is_at_end():

            stmt = self.parse_statement()

            if stmt is not None:
                statements.append(stmt)
            else:
                self.synchronize()

            self.skip_newlines()

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
        
        if self.check("ID"):
            next_token_index = self.pos + 1
            if next_token_index < len(self.tokens) and self.tokens[next_token_index].type == "ASSIGN":
                return self.parse_assign_stmt()

        return self.parse_expr_stmt()

    def parse_var_decl(self):

        let_token = self.consume("LET", "Se esperaba 'let'")
        if let_token is None:
            return None

        name_token = self.consume("ID", "Se esperaba un identificador")
        if name_token is None:
            return None

        assign_token = self.consume("ASSIGN", "Se esperaba '='")
        if assign_token is None:
            return None

        value = self.parse_expression()
        if value is None:
            return None

        return VarDeclNode(name_token.lexeme, value)

    def parse_func_decl(self):

        def_token = self.consume("DEF", "Se esperaba 'def'")
        if def_token is None:
            return None

        name_token = self.consume("ID", "Se esperaba el nombre de la función")
        if name_token is None:
            return None

        lparen_token = self.consume("LPAREN", "Se esperaba '('")
        if lparen_token is None:
            return None

        params = []

        if not self.check("RPAREN"):

            first_param = self.consume("ID", "Se esperaba un parámetro")
            if first_param is None:
                return None

            params.append(first_param.lexeme)

            while self.match("COMMA"):

                param = self.consume("ID", "Se esperaba un parámetro")
                if param is None:
                    return None

                params.append(param.lexeme)

        rparen_token = self.consume("RPAREN", "Se esperaba ')'")
        if rparen_token is None:
            return None

        body = self.parse_block()
        if body is None:
            return None

        return FuncDefNode(name_token.lexeme, params, body)

    def parse_block(self):

        lbrace_token = self.consume("LBRACE", "Se esperaba '{'")
        if lbrace_token is None:
            return None

        statements = []

        self.skip_newlines()

        while not self.check("RBRACE") and not self.is_at_end():

            stmt = self.parse_statement()

            if stmt is not None:
                statements.append(stmt)
            else:
                self.synchronize()

            self.skip_newlines()

        rbrace_token = self.consume("RBRACE", "Se esperaba '}'")
        if rbrace_token is None:
            return None

        return BlockNode(statements)

    def parse_if_stmt(self):

        if_token = self.consume("IF", "Se esperaba 'if'")
        if if_token is None:
            return None

        condition = self.parse_expression()
        if condition is None:
            return None

        then_block = self.parse_block()
        if then_block is None:
            return None

        else_block = None

        if self.match("ELSE"):

            else_block = self.parse_block()

            if else_block is None:
                return None

        return IfNode(condition, then_block, else_block)

    def parse_while_stmt(self):

        while_token = self.consume("WHILE", "Se esperaba 'while'")
        if while_token is None:
            return None

        condition = self.parse_expression()
        if condition is None:
            return None

        body = self.parse_block()
        if body is None:
            return None

        return WhileNode(condition, body)

    def parse_print_stmt(self):

        print_token = self.consume("PRINT", "Se esperaba 'print'")
        if print_token is None:
            return None

        lparen_token = self.consume("LPAREN", "Se esperaba '('")
        if lparen_token is None:
            return None

        expr = self.parse_expression()
        if expr is None:
            return None

        rparen_token = self.consume("RPAREN", "Se esperaba ')'")
        if rparen_token is None:
            return None

        return PrintNode(expr)

    def parse_return_stmt(self):

        return_token = self.consume("RETURN", "Se esperaba 'return'")
        if return_token is None:
            return None

        expr = self.parse_expression()
        if expr is None:
            return None

        return ReturnNode(expr)

    def parse_expr_stmt(self):

        expr = self.parse_expression()

        if expr is None:
            return None

        return ExprStmtNode(expr)

    def parse_assign_stmt(self):

        name_token = self.advance()
        self.consume("ASSIGN", "Se esperaba '='")
        value_expr = self.parse_expression()

        return AssignNode(name_token.lexeme, value_expr)

    # =========================
    # EXPRESIONES
    # =========================
    def parse_expression(self):
        return self.parse_logical_or()

    def parse_logical_or(self):

        expr = self.parse_logical_and()
        if expr is None:
            return None

        while self.match("OR"):

            operator = self.previous().lexeme

            right = self.parse_logical_and()
            if right is None:
                return None

            expr = BinOpNode(expr, operator, right)

        return expr

    def parse_logical_and(self):

        expr = self.parse_equality()
        if expr is None:
            return None

        while self.match("AND"):

            operator = self.previous().lexeme

            right = self.parse_equality()
            if right is None:
                return None

            expr = BinOpNode(expr, operator, right)

        return expr

    def parse_equality(self):

        expr = self.parse_comparison()
        if expr is None:
            return None

        while self.match("EQ", "NEQ"):

            operator = self.previous().lexeme

            right = self.parse_comparison()
            if right is None:
                return None

            expr = BinOpNode(expr, operator, right)

        return expr

    def parse_comparison(self):

        expr = self.parse_term()
        if expr is None:
            return None

        while self.match("LT", "GT", "LTE", "GTE"):

            operator = self.previous().lexeme

            right = self.parse_term()
            if right is None:
                return None

            expr = BinOpNode(expr, operator, right)

        return expr

    def parse_term(self):

        expr = self.parse_factor()
        if expr is None:
            return None

        while self.match("PLUS", "MINUS"):

            operator = self.previous().lexeme

            right = self.parse_factor()
            if right is None:
                return None

            expr = BinOpNode(expr, operator, right)

        return expr

    def parse_factor(self):

        expr = self.parse_power()
        if expr is None:
            return None

        while self.match("MULT", "DIV", "MOD"):

            operator = self.previous().lexeme

            right = self.parse_power()
            if right is None:
                return None

            expr = BinOpNode(expr, operator, right)

        return expr

    def parse_power(self):

        expr = self.parse_unary()
        if expr is None:
            return None

        if self.match("POW"):

            operator = self.previous().lexeme

            right = self.parse_power()
            if right is None:
                return None

            expr = BinOpNode(expr, operator, right)

        return expr

    def parse_unary(self):

        if self.match("NOT", "MINUS"):

            operator = self.previous().lexeme

            operand = self.parse_unary()
            if operand is None:
                return None

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

        if self.match("ID", "SIN", "COS", "TAN", "SQRT", "LOG", "ABS", "FLOOR", "CEIL"):

            name = self.previous().lexeme

            if self.match("LPAREN"):

                args = []

                if not self.check("RPAREN"):

                    first_arg = self.parse_expression()
                    if first_arg is None:
                        return None

                    args.append(first_arg)

                    while self.match("COMMA"):

                        arg = self.parse_expression()
                        if arg is None:
                            return None

                        args.append(arg)

                rparen_token = self.consume("RPAREN", "Se esperaba ')'")
                if rparen_token is None:
                    return None

                return FuncCallNode(name, args)

            return VariableNode(name)

        if self.match("LPAREN"):

            expr = self.parse_expression()
            if expr is None:
                return None

            rparen_token = self.consume("RPAREN", "Se esperaba ')'")
            if rparen_token is None:
                return None

            return expr

        self.error(self.current(), "Se esperaba una expresión válida")
        return None