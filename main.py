from lexer import Lexer
from syntax_parser import Parser
from ast_printer import print_ast
from semantic_analyzer import SemanticAnalyzer
from interpreter import Interpreter


#code = 
"""
-- 1. Engaño de Scopes (Shadowing y colisión con parámetros)
let variable_global = 100
def calcular(variable_global, descuento) {
    let descuento = 50 
    return variable_global - descuento
}

-- 2. Parámetros duplicados en la firma de la función
def funcion_mala(a, b, a) {
    return a + b
}

-- 3. Confusión de identidades (Llamar a una variable como si fuera función)
let mi_numero = 10
mi_numero(5) 

-- 4. Errores matemáticos profundos y en cascada
let locura = 10 + 20 * (30 - "texto_intruso") / 5

-- 5. Reasignación a variables inexistentes con operaciones malas
variable_fantasma = funcion_que_no_existe() + 10

-- 6. Pasar funciones fantasma como argumentos de funciones válidas
def multiplicar(x, y) {
    return x * y
}
multiplicar(10, otra_fantasma(5, "hola"))

-- 7. Trampa de Contexto: Return escondido dentro de bloques condicionales globales
let i = 0
while i < 3 {
    if i == 1 {
        return 0 
    }
    i = i + 1
}
"""




#code = 
"""
-- Prueba completa de la Fase 5: Intérprete

let x = 5
let y = 2
let z = x + y * 3
print(z)

print(2 ^ 3 ^ 2)

if z > 10 and true {
    print("z es mayor que 10")
} else {
    print("z no es mayor que 10")
}

let i = 1
while i <= 3 {
    print(i)
    i = i + 1
}

def suma(a, b) {
    return a + b
}

print(suma(10, 20))

def cuadrado(n) {
    return n * n
}

print(cuadrado(6))

print(sqrt(25))
print(abs(-8))
print(floor(3.9))
print(ceil(3.1))
print(sin(0))
"""

code = """
let x = --5;
print(x)
"""

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

if lexical_errors:
    print("\nNo se ejecuta el análisis sintáctico porque existen errores léxicos.")
else:
    parser = Parser(tokens)
    ast = parser.parse()

    print("\nERRORES SINTÁCTICOS")
    print("-" * 60)

    if not parser.errors:
        print("Sin errores sintácticos.")
    else:
        for error in parser.errors:
            print(error)

    if parser.errors:
        print("\nNo se ejecuta el análisis semántico porque existen errores sintácticos.")
    else:
        print("\nAST")
        print("-" * 60)
        print_ast(ast)

        print("\nINICIANDO ANÁLISIS SEMÁNTICO...")
        print("-" * 60)

        analyzer = SemanticAnalyzer()
        semantic_errors = analyzer.analyze(ast)

        if semantic_errors:
            print("¡SE ENCONTRARON ERRORES SEMÁNTICOS!\n")

            for err in semantic_errors:
                print(err)

            print("\nNo se ejecuta el intérprete porque existen errores semánticos.")

        else:
            print("Análisis Semántico exitoso. El código es válido.")

            print("\nINICIANDO INTERPRETACIÓN...")
            print("-" * 60)

            interpreter = Interpreter()
            output, runtime_errors = interpreter.interpret(ast)

            print("\nERRORES EN TIEMPO DE EJECUCIÓN")
            print("-" * 60)

            if runtime_errors:
                for error in runtime_errors:
                    print(error)
            else:
                print("Sin errores en tiempo de ejecución.")

            print("\nSALIDA DEL PROGRAMA")
            print("-" * 60)

            if output:
                for line in output:
                    print(line)
            else:
                print("El programa no generó salida.")