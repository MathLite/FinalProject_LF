from lexer import Lexer
from syntax_parser import Parser
from ast_printer import print_ast
from semantic_analyzer import SemanticAnalyzer
from interpreter import Interpreter

import io
import sys


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
        "phase": None
    }

    lexer = Lexer(code)
    tokens, lexical_errors = lexer.tokenize()

    result["tokens"] = format_tokens(tokens)
    result["lexical_errors"] = format_lexical_errors(lexical_errors)

    parser = Parser(tokens)
    ast = parser.parse()

    result["syntax_errors"] = parser.errors

    if ast is not None:
        result["ast"] = get_ast_as_text(ast)

        analyzer = SemanticAnalyzer()
        semantic_errors = analyzer.analyze(ast)

        result["semantic_errors"] = semantic_errors

        interpreter = Interpreter()
        output, runtime_errors = interpreter.interpret(ast)

        result["output"] = output
        result["runtime_errors"] = format_runtime_errors(runtime_errors)

    result["success"] = (
        len(result["lexical_errors"]) == 0 and
        len(result["syntax_errors"]) == 0 and
        len(result["semantic_errors"]) == 0 and
        len(result["runtime_errors"]) == 0
    )

    result["phase"] = determine_phase(
        result["lexical_errors"],
        result["syntax_errors"],
        result["semantic_errors"],
        result["runtime_errors"]
    )

    return result