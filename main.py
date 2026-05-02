from lexer import Lexer
from syntax_parser import Parser
from ast_printer import print_ast







code = """
let = 5;
let let let = = = = 5;
let x 5;
let x == 5;
let x = ;
let x = 5

print x);
print();
print(x;
print(x)
print(x + );

return ;
return x + 1 
return a + ;

if {
    print(x);
}
if x > 0
    print(x);
if x > {
    print(x);
}
if x > 0 {
    print(x);
} else
    print(y);
else {
    print(x);
}

while {
    print(x);
}
while x < 10
    print(x);
while x < {
    print(x);
}

def (a, b) {
    return a + b;
}
def suma a, b) {
    return a + b;
}
def suma(a b) {
    return a + b;
}
def suma(a, b {
    return a + b;
}
def suma(a, b)
    return a + b;
def suma(a, b) {
    return a + b
}

print(suma(x, y);
print(suma(x, ));
print(suma(, x));
print(suma(x,, y));

x + ;
+ x;
(x + 5;
();
x > ;
x and ;
not ;

if x > 0 {
    print(x);
}
}
{
}
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