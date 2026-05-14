from lexer import Lexer
from syntax_parser import Parser
from ast_printer import print_ast

code = """let x = 10
let y = 20
if x > 5 {
    print(x + y)
}"""


# 1. Análisis léxico
lexer = Lexer(code)
tokens, lexical_errors = lexer.tokenize()

print("TOKENS")
print("-" * 60)
for token in tokens:
    print(f"{token.type:<12} {token.lexeme!r:<15} línea={token.line:<3} columna={token.column}")

print("\nERRORES LÉXICOS")
print("-" * 60)
if not lexical_errors:
    print("Sin errores léxicos.")
else:
    for error in lexical_errors:
        print(f"{error.message}: {error.lexeme!r} en línea {error.line}, columna {error.column}")


# 2. Solo parsear si no hay errores léxicos
if not lexical_errors:
    parser = Parser(tokens)
    ast = parser.parse()

    print("\nERRORES SINTÁCTICOS")
    print("-" * 60)
    if not parser.errors:
        print("Sin errores sintácticos.")
    else:
        for error in parser.errors:
            print(error)

    print("\nAST")
    print("-" * 60)
    print_ast(ast)