from lexer import Lexer
from syntax_parser import Parser
from ast_printer import print_ast
from semantic_analyzer import SemanticAnalyzer
from interpreter import Interpreter

import io
import sys



"""

El runner recibe el código fuente desde la aplicación web, ejecuta las fases
en el orden correspondiente y retorna un diccionario con tokens, errores,
AST, salida del programa, estado de éxito y fase final alcanzada.

Funciones principales:
- run_code(): ejecuta el flujo completo de análisis y ejecución.
- format_tokens(): transforma los tokens en una estructura serializable.
- format_lexical_errors(): formatea los errores léxicos.
- format_runtime_errors(): formatea los errores en tiempo de ejecución.
- get_ast_as_text(): obtiene una representación textual del AST.
- determine_phase(): determina la fase final alcanzada por el programa.
"""
def get_ast_as_text(ast):
    old_stdout = sys.stdout
    buffer = io.StringIO()

    try:
        sys.stdout = buffer
        print_ast(ast)
        return buffer.getvalue()
    finally:
        sys.stdout = old_stdout


def format_tokens(tokens):
    result = []

    for token in tokens:
        result.append({
            "type": token.type,
            "lexeme": token.lexeme,
            "line": token.line,
            "column": token.column
        })

    return result


def format_lexical_errors(errors):
    result = []

    for error in errors:
        result.append({
            "message": error.message,
            "lexeme": error.lexeme,
            "line": error.line,
            "column": error.column
        })

    return result


def format_runtime_errors(errors):
    result = []

    for error in errors:
        result.append(str(error))

    return result


def determine_phase(lexical_errors, syntax_errors, semantic_errors, runtime_errors):
    if lexical_errors:
        return "LEXICAL"

    if syntax_errors:
        return "SYNTAX"

    if semantic_errors:
        return "SEMANTIC"

    if runtime_errors:
        return "RUNTIME"

    return "SUCCESS"

def run_code(code):
    result = {
        "tokens": [],
        "lexical_errors": [],
        "syntax_errors": [],
        "semantic_errors": [],
        "runtime_errors": [],
        "output": [],
        "ast": None,
        "success": False,
        "phase": None,

        "syntax_executed": False,
        "semantic_executed": False,
        "semantic_partial": False,
        "runtime_executed": False,
        "runtime_skipped_reason": None,

        "ast_diagnostic": False,
        "ast_message": None
    }

    # =========================
    # 1. ANÁLISIS LÉXICO
    # =========================

    lexer = Lexer(code)
    tokens, lexical_errors = lexer.tokenize()

    result["tokens"] = format_tokens(tokens)
    result["lexical_errors"] = format_lexical_errors(lexical_errors)

    # Si hay errores léxicos, no se continúa con parser, semántica ni ejecución.
    if result["lexical_errors"]:
        result["runtime_skipped_reason"] = (
            "El análisis se detuvo en la fase léxica. "
            "No se ejecutó el análisis sintáctico porque existen errores léxicos."
        )

        result["success"] = False
        result["phase"] = determine_phase(
            result["lexical_errors"],
            result["syntax_errors"],
            result["semantic_errors"],
            result["runtime_errors"]
        )

        return result

    # =========================
    # 2. ANÁLISIS SINTÁCTICO
    # =========================

    parser = Parser(tokens)
    ast = parser.parse()

    result["syntax_executed"] = True
    result["syntax_errors"] = parser.errors

    if ast is not None:
        result["ast"] = get_ast_as_text(ast)

        if result["syntax_errors"]:
            result["ast_diagnostic"] = True
            result["ast_message"] = (
                "AST de diagnóstico generado durante la recuperación de errores sintácticos. "
                "Las sentencias incompletas no se incorporan como nodos válidos del árbol."
            )

    # =========================
    # 3. ANÁLISIS SEMÁNTICO
    # =========================

    if ast is not None:
        analyzer = SemanticAnalyzer()
        semantic_errors = analyzer.analyze(ast)

        result["semantic_errors"] = semantic_errors
        result["semantic_executed"] = True

        if result["syntax_errors"]:
            result["semantic_partial"] = True

    # =========================
    # 4. EJECUCIÓN
    # =========================

    has_previous_errors = (
        len(result["lexical_errors"]) > 0 or
        len(result["syntax_errors"]) > 0 or
        len(result["semantic_errors"]) > 0
    )

    if ast is None:
        result["runtime_skipped_reason"] = (
            "No se generó un AST válido para ejecutar el programa."
        )

    elif has_previous_errors:
        result["runtime_skipped_reason"] = (
            "La ejecución no se realizó porque existen errores sintácticos "
            "o semánticos pendientes."
        )

    else:
        interpreter = Interpreter()
        output, runtime_errors = interpreter.interpret(ast)

        result["output"] = output
        result["runtime_errors"] = format_runtime_errors(runtime_errors)
        result["runtime_executed"] = True

    # =========================
    # 5. RESULTADO FINAL
    # =========================

    result["success"] = (
        len(result["lexical_errors"]) == 0 and
        len(result["syntax_errors"]) == 0 and
        len(result["semantic_errors"]) == 0 and
        len(result["runtime_errors"]) == 0 and
        result["runtime_executed"]
    )

    result["phase"] = determine_phase(
        result["lexical_errors"],
        result["syntax_errors"],
        result["semantic_errors"],
        result["runtime_errors"]
    )

    return result