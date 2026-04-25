import re
from dataclasses import dataclass
from typing import List, Tuple, Optional


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


class Lexer:
    RESERVED_WORDS = {
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
    }

    DOUBLE_TOKENS = {
        "==": "EQ",
        "!=": "NEQ",
        "<=": "LTE",
        ">=": "GTE",
    }

    SINGLE_TOKENS = {
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
        ";": "SEMICOLON",
    }

    COMMENT_RE = re.compile(r'--[^\n]*')
    STRING_RE = re.compile(r'"[^"\n]*"')
    REAL_RE = re.compile(r'\d+\.\d+')
    INT_RE = re.compile(r'\d+')
    ID_RE = re.compile(r'[A-Za-z][A-Za-z0-9_]*')

    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []   # type: List[Token]
        self.errors = []   # type: List[LexicalError]

    def is_at_end(self) -> bool:
        return self.position >= len(self.source)

    def current_slice(self) -> str:
        return self.source[self.position:]

    def advance_text(self, text: str):
        for ch in text:
            if ch == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        self.position += len(text)

    def add_token(self, token_type: str, lexeme: str, line: int, column: int) :
        self.tokens.append(Token(token_type, lexeme, line, column))

    def add_error(self, message: str, lexeme: str, line: int, column: int) :
        self.errors.append(LexicalError(message, line, column, lexeme))

    def skip_whitespace(self):
        while not self.is_at_end() and self.source[self.position] in " \t\r\n":
            self.advance_text(self.source[self.position])

    def match_regex(self, pattern: re.Pattern):
        match = pattern.match(self.current_slice())
        if match:
            return match.group(0)
        return None

    def tokenize(self) -> Tuple[List[Token], List[LexicalError]]:
        while not self.is_at_end():
            self.skip_whitespace()

            if self.is_at_end():
                break

            start_line = self.line
            start_column = self.column
            rest = self.current_slice()

            lexeme = self.match_regex(self.COMMENT_RE)
            if lexeme:
                self.advance_text(lexeme)
                continue

            lexeme = self.match_regex(self.STRING_RE)
            if lexeme:
                self.add_token("STRING", lexeme, start_line, start_column)
                self.advance_text(lexeme)
                continue

            if rest.startswith('"'):
                i = 1
                while i < len(rest) and rest[i] not in ['"', '\n']:
                    i += 1
                bad_lexeme = rest[:i]
                self.add_error("Cadena sin comilla de cierre", bad_lexeme, start_line, start_column)
                self.advance_text(bad_lexeme)
                continue

            lexeme = self.match_regex(self.REAL_RE)
            if lexeme:
                self.add_token("REAL", lexeme, start_line, start_column)
                self.advance_text(lexeme)
                continue

            lexeme = self.match_regex(self.INT_RE)
            if lexeme:
                self.add_token("INT", lexeme, start_line, start_column)
                self.advance_text(lexeme)
                continue

            lexeme = self.match_regex(self.ID_RE)
            if lexeme:
                token_type = self.RESERVED_WORDS.get(lexeme, "ID")
                self.add_token(token_type, lexeme, start_line, start_column)
                self.advance_text(lexeme)
                continue

            two_chars = rest[:2]
            if two_chars in self.DOUBLE_TOKENS:
                self.add_token(self.DOUBLE_TOKENS[two_chars], two_chars, start_line, start_column)
                self.advance_text(two_chars)
                continue

            one_char = rest[0]
            if one_char in self.SINGLE_TOKENS:
                self.add_token(self.SINGLE_TOKENS[one_char], one_char, start_line, start_column)
                self.advance_text(one_char)
                continue

            self.add_error("Carácter inválido", one_char, start_line, start_column)
            self.advance_text(one_char)

        self.add_token("EOF", "", self.line, self.column)
        return self.tokens, self.errors