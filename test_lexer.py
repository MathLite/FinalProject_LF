from lexer2 import Lexer


def test_lexer(code: str) -> None:
    lexer = Lexer(code)
    tokens, errors = lexer.tokenize()

    print("TOKENS")
    print("-" * 60)
    for token in tokens:
        print(f"{token.type:<12} {token.lexeme!r:<15} línea={token.line:<3} columna={token.column}")

    print("\nERRORES")
    print("-" * 60)
    if not errors:
        print("Sin errores léxicos.")
    else:
        for error in errors:
            print(f"{error.message}: {error.lexeme!r} en línea {error.line}, columna {error.column}")


code = """
    let x = @5;
    let y = 3.14;
    let z = "la suma es"";
    def suma(a, b) {
        return a + b;
    }
    print(z));
    print(suma(x, y));
    -- comentario
    
    """

test_lexer(code)