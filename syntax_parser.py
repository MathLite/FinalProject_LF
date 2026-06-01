from ASTNode import *


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

#### FUNCIONES CLAVES DE RECORRIDO Y RESPUESTA DEL PARSER 

# Retorna el token actual.
    def current(self):  
        return self.tokens[self.pos]
    
# Retorna el token anterior.
    def previous(self):
        return self.tokens[self.pos - 1]
    
# Valida si se llego al final del programa y returna el token EOF.
    def is_at_end(self):
        return self.current().type == "EOF"
    
# Avanza al siguiente token.
    def advance(self):
        if not self.is_at_end():
            self.pos += 1
        return self.previous()
    
# El token actual es de cierto tipo? -> true / false
    def check(self, token_type):
        if self.is_at_end():
            return False
        return self.current().type == token_type
    
#El token actual coincide con alguno del listado de tipos -> true / false
    def match(self, *token_types):
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False
    
# Exige que el token actual sea igual al especificado en token_type y lo consume 
# (continua el analisis). Si no es el caso, retorna una respuesta con el mensaje
# de error de la regla/funcion establecida.
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

# Cuando se detecta un error, el analisis debe continuar para ello este metodo 
# permite avanzar tokens hasta encontrar un "punto apropiado" para continuar 
# (nueva sentencia, fin de un bloque, o un /n). es usado en parse_program al retornar none en 
# la respuesta de la regla de statement (parse_statement).
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

# Inicio del parser
    def parse(self):
        return self.parse_program()



#------------
#### FUNCIONES DE LA GRAMATICA LL(1)

    def parse_program(self):
        line = self.current().line
        statements = []

        self.skip_newlines()

        while not self.is_at_end():

            stmt = self.parse_statement()

            if stmt is not None:
                statements.append(stmt)
            else:
                self.synchronize()

            self.skip_newlines()

        return ProgramNode(statements, line=line)

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
        line = self.current().line

        let_token = self.consume("LET", "Se esperaba 'let'")
        if let_token is None:
            return None

        if self.is_builtin_function_token(self.current().type):
            token = self.current()
            self.error(
                token,
                "No se puede usar '{}' como nombre de variable porque es una palabra reservada del lenguaje".format(token.lexeme)
            )
            self.advance()
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

        return VarDeclNode(name_token.lexeme, value, line=line)

    def parse_func_decl(self):
        line = self.current().line

        def_token = self.consume("DEF", "Se esperaba 'def'")
        if def_token is None:
            return None

        if self.is_builtin_function_token(self.current().type):
            token = self.current()
            self.error(
                token,
                "No se puede definir la función '{}' porque es una palabra reservada del lenguaje".format(token.lexeme)
            )
            self.advance()
            return None

        name_token = self.consume("ID", "Se esperaba el nombre de la función")
        if name_token is None:
            return None

        lparen_token = self.consume("LPAREN", "Se esperaba '('")
        if lparen_token is None:
            return None

        params = []

        if not self.check("RPAREN"):

            if self.is_builtin_function_token(self.current().type):
                token = self.current()
                self.error(
                    token,
                    "No se puede usar '{}' como nombre de parámetro porque es una palabra reservada del lenguaje".format(token.lexeme)
                )
                self.advance()
                return None

            first_param = self.consume("ID", "Se esperaba un parámetro")
            if first_param is None:
                return None

            params.append(first_param.lexeme)

            while self.match("COMMA"):

                if self.is_builtin_function_token(self.current().type):
                    token = self.current()
                    self.error(
                        token,
                        "No se puede usar '{}' como nombre de parámetro porque es una palabra reservada del lenguaje".format(token.lexeme)
                    )
                    self.advance()
                    return None

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

        return FuncDefNode(name_token.lexeme, params, body, line=line)


    def parse_block(self):
        line = self.current().line

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

        return BlockNode(statements, line=line)

    def parse_if_stmt(self):
        line = self.current().line

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

        self.skip_newlines()

        if self.match("ELSE"):
            self.skip_newlines()

            else_block = self.parse_block()

            if else_block is None:
                return None

        return IfNode(condition, then_block, else_block, line=line)

    def parse_while_stmt(self):
        line = self.current().line

        while_token = self.consume("WHILE", "Se esperaba 'while'")
        if while_token is None:
            return None

        condition = self.parse_expression()
        if condition is None:
            return None

        body = self.parse_block()
        if body is None:
            return None

        return WhileNode(condition, body, line=line)

    def parse_print_stmt(self):
        line = self.current().line

        print_token = self.consume("PRINT", "Se esperaba 'print'")
        if print_token is None:
            return None

        lparen_token = self.consume("LPAREN", "Se esperaba '(' después de 'print'")
        if lparen_token is None:
            return None

        expression = self.parse_expression()
        if expression is None:
            return None

        rparen_token = self.consume("RPAREN", "Se esperaba ')'")
        if rparen_token is None:
            return None

        return PrintNode(expression, line=line)

    def parse_return_stmt(self):
        line = self.current().line

        return_token = self.consume("RETURN", "Se esperaba 'return'")
        if return_token is None:
            return None

        expr = self.parse_expression()
        if expr is None:
            return None

        return ReturnNode(expr, line=line)

    def parse_expr_stmt(self):
        line = self.current().line

        expr = self.parse_expression()

        if expr is None:
            return None

        return ExprStmtNode(expr, line=line)

    # =========================
    # EXPRESIONES
    # =========================
    def parse_expression(self):
        return self.parse_logical_or()

    def parse_logical_or(self):
        expr = self.parse_logical_and() 

        while self.match("OR"):
            operator_token = self.previous() 
            operator = operator_token.lexeme
            line = operator_token.line      

            right = self.parse_logical_and()
            if right is None:
                return None

            expr = BinOpNode(expr, operator, right, line=line)

        return expr

    def parse_logical_and(self):
        expr = self.parse_equality()
        if expr is None:
            return None

        while self.match("AND"):
            operator_token = self.previous()
            operator = operator_token.lexeme
            line = operator_token.line

            right = self.parse_equality()
            if right is None:
                return None

            expr = BinOpNode(expr, operator, right, line=line)

        return expr

    def parse_equality(self):
        expr = self.parse_comparison()
        if expr is None:
            return None

        while self.match("EQ", "NEQ"):
            operator_token = self.previous()
            operator = operator_token.lexeme
            line = operator_token.line

            right = self.parse_comparison()
            if right is None:
                return None

            expr = BinOpNode(expr, operator, right, line=line)

        return expr

    def parse_comparison(self):
        expr = self.parse_term()
        if expr is None:
            return None

        while self.match("LT", "GT", "LTE", "GTE"):
            operator_token = self.previous()
            operator = operator_token.lexeme
            line = operator_token.line

            right = self.parse_term()
            if right is None:
                return None

            expr = BinOpNode(expr, operator, right, line=line)

        return expr

    def parse_term(self):
        expr = self.parse_factor()
        if expr is None:
            return None

        while self.match("PLUS", "MINUS"):
            operator_token = self.previous()
            operator = operator_token.lexeme
            line = operator_token.line

            right = self.parse_factor()
            if right is None:
                return None

            expr = BinOpNode(expr, operator, right, line=line)

        return expr

    def parse_factor(self):
        expr = self.parse_power()
        if expr is None:
            return None

        while self.match("MULT", "DIV", "MOD"):
            operator_token = self.previous()
            operator = operator_token.lexeme
            line = operator_token.line

            right = self.parse_power()
            if right is None:
                return None

            expr = BinOpNode(expr, operator, right, line=line)

        return expr

    def parse_power(self):
        expr = self.parse_unary()
        if expr is None:
            return None

        if self.match("POW"):
            operator_token = self.previous()
            operator = operator_token.lexeme
            line = operator_token.line

            right = self.parse_power()
            if right is None:
                return None

            expr = BinOpNode(expr, operator, right, line=line)

        return expr

    def parse_unary(self):
        if self.match("NOT", "MINUS"):
            operator_token = self.previous()
            operator = operator_token.lexeme
            line = operator_token.line 

            operand = self.parse_unary()
            if operand is None:
                return None

            return UnaryOpNode(operator, operand, line=line)

        return self.parse_primary()
    


    def parse_builtin_call(self):
        function_token = self.advance()
        function_name = function_token.lexeme
        line = function_token.line

        if not self.match("LPAREN"):
            self.error(
                function_token,
                "La función integrada '{}' debe invocarse con paréntesis".format(function_name)
            )
            return None

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

        rparen_token = self.consume(
            "RPAREN",
            "Se esperaba ')' después de los argumentos de la función integrada"
        )

        if rparen_token is None:
            return None

        return FuncCallNode(function_name, args, line=line)
    
    def is_builtin_function_token(self, token_type):
        return token_type in (
            "SIN",
            "COS",
            "TAN",
            "SQRT",
            "LOG",
            "ABS",
            "FLOOR",
            "CEIL"
        )

    def parse_primary(self):
        if self.match("INT", "REAL"):
            return NumberNode(self.previous().lexeme, line=self.previous().line)

        if self.match("STRING"):
            return StringNode(self.previous().lexeme, line=self.previous().line)

        if self.match("TRUE"):
            return BoolNode(True, line=self.previous().line)

        if self.match("FALSE"):
            return BoolNode(False, line=self.previous().line)

        if self.is_builtin_function_token(self.current().type):
            return self.parse_builtin_call()

        if self.match("ID"):
            line = self.previous().line
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

                return FuncCallNode(name, args, line=line)

            return VariableNode(name, line=line)

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
