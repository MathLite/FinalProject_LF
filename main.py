from lexer import Lexer
from syntax_parser import Parser
from ast_printer import print_ast

code = """
-- 1. Prueba de variables, guion bajo y reasignacion (AssignNode)
let mi_var_1 = 10
mi_var_1 = mi_var_1 + 5

-- 2. Prueba de trigonometria y matematicas (Lexer y Parser)
let resultado = sin(3.14) + sqrt(16) * 2

-- 3. Prueba de funciones (FuncDefNode y FuncCallNode)
def calcular_area(base, altura) {
    return base * altura
}
print(calcular_area(10, 5))

-- 4. Prueba de estructuras de control (IfNode y WhileNode)
let i = 0
while i < 3 {
    if i == 1 {
        print("es uno")
    } else {
        print("no es uno")
    }
    i = i + 1
}

-- 5. Prueba de Panic Mode (Error sintactico intencional)
let error_fatal = + = 5
print("El parser sobrevivio al error")
"""


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