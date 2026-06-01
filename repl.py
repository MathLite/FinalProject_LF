import sys
from lexer import Lexer
from syntax_parser import Parser
from semantic_analyzer import SemanticAnalyzer
from interpreter import Interpreter, RuntimeErrorInfo, MathLiteRuntimeError
from ASTNode import ProgramNode, ExprStmtNode, PrintNode


def run_repl():
    print("=== MathLite Interactive REPL ===")
    print("Escribe 'exit' o 'quit' para salir.\n")

    # Instancias persistentes para mantener variables y funciones en memoria
    semantic_analyzer = SemanticAnalyzer()
    interpreter = Interpreter()

    while True:
        try:
            line = input("mathlite> ")
            if line.strip() in ("exit", "quit"):
                break
            if not line.strip():
                continue

            # 1. Analizador Léxico
            lexer = Lexer(line)
            tokens, lex_errors = lexer.tokenize()
            if lex_errors:
                for err in lex_errors:
                    print("Error Léxico (Línea {}, Columna {}): {} (Lexema: '{}')".format(
                        err.line, err.column, err.message, err.lexeme
                    ))
                continue

            # 2. Analizador Sintáctico
            parser = Parser(tokens)
            ast = parser.parse()
            if parser.errors:
                for err in parser.errors:
                    print(err)
                continue

            if ast is None:
                continue

            # 3. Analizador Semántico (Persistente)
            sem_errors = semantic_analyzer.analyze(ast)
            if sem_errors:
                for err in sem_errors:
                    print(err)
                continue

            # 4. Intérprete (Persistente)
            if isinstance(ast, ProgramNode) and ast.statements:
                statements = ast.statements
                last_stmt = statements[-1]
                
                if isinstance(last_stmt, ExprStmtNode):
                    # Si el último nodo es una expresión, ejecutamos todo lo anterior normalmente
                    other_statements = statements[:-1]
                    if other_statements:
                        output, runtime_errors = interpreter.interpret(ProgramNode(other_statements, line=ast.line), reset_state=False)
                        for out in output:
                            print(out)
                        if runtime_errors:
                            for err in runtime_errors:
                                print(err)
                            continue
                    
                    # Y evaluamos la última expresión directamente para mostrar su resultado implícito
                    try:
                        val = interpreter.visit(last_stmt.expression)
                        if val is not None:
                            print(interpreter.format_value(val))
                    except MathLiteRuntimeError as err:
                        print("Error en tiempo de ejecución (Línea {}): {}".format(
                            err.node.line if err.node else 0, err.message
                        ))
                    except Exception as err:
                        print("Error en tiempo de ejecución: {}".format(err))
                else:
                    # Si no es una expresión (por ejemplo, let, def, if, while, print)
                    output, runtime_errors = interpreter.interpret(ast, reset_state=False)
                    for out in output:
                        print(out)
                    if runtime_errors:
                        for err in runtime_errors:
                            print(err)
            else:
                # Caso por defecto
                output, runtime_errors = interpreter.interpret(ast, reset_state=False)
                for out in output:
                    print(out)
                if runtime_errors:
                    for err in runtime_errors:
                        print(err)

        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo...")
            break
        except Exception as e:
            print("Error inesperado en el REPL: {}".format(e))


if __name__ == "__main__":
    run_repl()
