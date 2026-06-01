import re
from dataclasses import dataclass


@dataclass
class Token:
    type: str
    lexeme: str
    line: int
    column: int


@dataclass
class LexicalError:
    message: str
    line: int
    column: int
    lexeme: str = ""

"""
Clase Lexer
# ==========================================================
#
# Métodos principales:
#   - tokenize():
#       Ejecuta el análisis léxico completo y retorna la lista
#       de tokens junto con los errores encontrados.
#
#   - scan_token():
#       Analiza el carácter actual y decide qué tipo de token
#       debe construirse.
#
#   - read_identifier():
#       Reconoce identificadores y palabras reservadas.
#
#   - read_number():
#       Reconoce literales numéricos enteros y reales.
#
#   - read_string():
#       Reconoce cadenas de texto delimitadas por comillas.
#
#   - add_token():
#       Agrega un token reconocido a la lista de salida.
#
#   - add_error():
#       Registra un error léxico con línea, columna y lexema.

"""

class Lexer:
    def __init__(self, input):
        self.input = input
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        self.errors = []

        # Palabras reservadas
        self.reserved_words = {
            "let": "LET",
            "def": "DEF",
            "return": "RETURN",
            "if": "IF",
            "else": "ELSE",
            "while": "WHILE",
            "print": "PRINT",
            "true": "TRUE",
            "false": "FALSE",
            "and": "AND",
            "or": "OR",
            "not": "NOT",
            "sin": "SIN", 
            "cos": "COS", 
            "tan": "TAN",
            "sqrt": "SQRT", 
            "log": "LOG", 
            "abs": "ABS", 
            "floor": "FLOOR", 
            "ceil": "CEIL"
        }

        # Operadores dobles
        self.double_tokens = {
            "==": "EQ",
            "!=": "NEQ",
            "<=": "LTE",
            ">=": "GTE",
        }

        # Operadores simples y delimitadores
        self.single_tokens = {
            "+": "PLUS",
            "-": "MINUS",
            "*": "MULT",
            "/": "DIV",
            "%": "MOD",
            "^": "POW",
            "=": "ASSIGN",
            "<": "LT",
            ">": "GT",
            "(": "LPAREN",
            ")": "RPAREN",
            "{": "LBRACE",
            "}": "RBRACE",
            ",": "COMMA",
        }

        # Expresiones regulares
        self.comment_re = re.compile(r'--[^\n]*')
        self.string_re = re.compile(r'"[^"\n]*"')
        self.real_re = re.compile(r'\d+\.\d+')
        self.int_re = re.compile(r'\d+')
        self.id_re = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')

    def finished(self):
        return self.position >= len(self.input)

    # retorna el texto restante de la linea a partir de la position.
    def current_text(self):
        return self.input[self.position:]

    def move(self, text):
        for ch in text:
            if ch == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1

        self.position += len(text)

    def add_token(self, token_type, lexeme, line, column):
        self.tokens.append(Token(token_type, lexeme, line, column))

    def add_error(self, message, lexeme, line, column):
        self.errors.append(LexicalError(message, line, column, lexeme))

    def skip_spaces(self):
        while not self.finished() and self.input[self.position] in " \t\r":
            self.move(self.input[self.position])


    def regex_match(self, pattern):
        match = pattern.match(self.current_text())

        if match:
            return match.group(0)

        return None

    def tokenize(self):
        while not self.finished():
            self.skip_spaces()

            if self.finished():
                break

            # NEWLINE
            if self.input[self.position] == "\n":
                self.add_token("NEWLINE", "\\n", self.line, self.column)
                self.move("\n")
                continue

            start_line = self.line
            start_column = self.column
            rest = self.current_text()

            # 1. Comentarios
            lexeme = self.regex_match(self.comment_re)
            if lexeme:
                self.move(lexeme)
                continue

            # 2. Cadenas válidas
            lexeme = self.regex_match(self.string_re)
            if lexeme:
                self.add_token("STRING", lexeme, start_line, start_column)
                self.move(lexeme)
                continue

            # 3. Cadena sin cerrar
            if rest.startswith('"'):
                i = 1

                while i < len(rest) and rest[i] not in ['"', '\n']:
                    i += 1

                bad_lexeme = rest[:i]

                self.add_error(
                    "Cadena sin comilla de cierre",
                    bad_lexeme,
                    start_line,
                    start_column
                )

                self.move(bad_lexeme)
                continue

            # 4. Reales
            lexeme = self.regex_match(self.real_re)
            if lexeme:
                self.add_token("REAL", lexeme, start_line, start_column)
                self.move(lexeme)
                continue

            # 5. Enteros
            lexeme = self.regex_match(self.int_re)
            if lexeme:
                self.add_token("INT", lexeme, start_line, start_column)
                self.move(lexeme)
                continue

            # 6. Identificadores o palabras reservadas
            lexeme = self.regex_match(self.id_re)
            if lexeme:
                token_type = self.reserved_words.get(lexeme, "ID")
                self.add_token(token_type, lexeme, start_line, start_column)
                self.move(lexeme)
                continue

            # 7. Operadores dobles
            two = rest[:2]
            if two in self.double_tokens:
                self.add_token(self.double_tokens[two], two, start_line, start_column)
                self.move(two)
                continue

            # 8. Operadores simples y delimitadores
            one = rest[0]
            if one in self.single_tokens:
                self.add_token(self.single_tokens[one], one, start_line, start_column)
                self.move(one)
                continue

            # 9. Error léxico
            self.add_error("Carácter inválido", one, start_line, start_column)
            self.move(one)

        self.add_token("EOF", "", self.line, self.column)

        return self.tokens, self.errors