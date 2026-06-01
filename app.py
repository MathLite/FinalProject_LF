import uuid
from flask import Flask, render_template, request, jsonify
from runner import run_code
from test_case_repository import TestCaseRepository
from lexer import Lexer
from syntax_parser import Parser
from semantic_analyzer import SemanticAnalyzer
from interpreter import Interpreter, MathLiteRuntimeError, RuntimeErrorInfo
from ASTNode import ProgramNode, ExprStmtNode


"""
Este módulo implementa la interfaz web de MathLite mediante Flask. Permite que
el usuario escriba código fuente, lo envíe al sistema de análisis y visualice
los resultados producidos por cada fase del intérprete.

La aplicación muestra tokens, errores léxicos, errores sintácticos, errores
semánticos, errores en tiempo de ejecución, AST, salida del programa y fase
final alcanzada. También puede incluir una suite de casos de prueba para validar
el comportamiento del lenguaje.

Funciones y rutas principales:
- index(): renderiza la página principal y procesa el código enviado.
- /api/test-suite: permite consultar o administrar casos de prueba locales.
- /api/repl: permite evaluar fragmentos de código en modo interactivo.
- /api/repl/reset: reinicia el entorno del REPL.
- run_code(): función externa llamada para ejecutar el flujo completo.
"""



app = Flask(__name__)
repository = TestCaseRepository()
repository.seed_default_suite_if_empty()


DEFAULT_CODE = """let x = 5
let y = 2
let z = x + y * 3
print(z)

print(2 ^ 3 ^ 2)

if z > 10 and true {
    print("z es mayor que 10")
}
else {
    print("z no es mayor que 10")
}

let i = 1
while i <= 3 {
    print(i)
    let i = i + 1
}

def suma(a, b) {
    return a + b
}

print(suma(10, 20))

print(sqrt(25))
"""


@app.route("/", methods=["GET", "POST"])
def index():
    code = DEFAULT_CODE
    result = None
    saved_id = None

    if request.method == "POST":
        code = request.form.get("code", "")
        result = run_code(code)
        saved_id = repository.save_test_case(code, result)

    test_cases = repository.get_all_test_cases()
    test_suite = repository.get_test_suite()

    return render_template(
        "index.html",
        code=code,
        result=result,
        saved_id=saved_id,
        test_cases=test_cases,
        test_suite=test_suite
    )


@app.route("/api/test-cases/<case_id>", methods=["GET"])
def get_test_case(case_id):
    case = repository.get_test_case_by_id(case_id)

    if case is None:
        return jsonify({
            "success": False,
            "message": "Caso de prueba no encontrado"
        }), 404

    code = case.get("code", "")

    return jsonify({
        "success": True,
        "id": case.get("id"),
        "code": code,
        "phase": case.get("phase"),
        "output": case.get("output", [])
    })


@app.route("/api/test-suite", methods=["GET"])
def get_test_suite_api():
    cases = repository.get_test_suite()
    return jsonify({
        "success": True,
        "cases": cases
    })


@app.route("/api/test-suite", methods=["POST"])
def add_test_suite_case():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    category = data.get("category", "Personalizados").strip()
    code = data.get("code", "").strip()

    if not name or not code:
        return jsonify({
            "success": False,
            "message": "El nombre y el código son obligatorios."
        }), 400

    new_case = repository.save_suite_case(name, category, code)
    return jsonify({
        "success": True,
        "case": new_case
    })


@app.route("/api/test-suite/<case_id>", methods=["PUT"])
def update_test_suite_case(case_id):
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    category = data.get("category", "Personalizados").strip()
    code = data.get("code", "").strip()

    if not name or not code:
        return jsonify({
            "success": False,
            "message": "El nombre y el código son obligatorios."
        }), 400

    try:
        updated_case = repository.update_suite_case(case_id, name, category, code)
        return jsonify({
            "success": True,
            "case": updated_case
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/test-suite/<case_id>", methods=["DELETE"])
def delete_test_suite_case(case_id):
    try:
        repository.delete_suite_case(case_id)
        return jsonify({
            "success": True
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/repl", methods=["POST"])
def repl_evaluate():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    code = data.get("code", "").strip()

    new_session_id, session = get_repl_session(session_id)
    analyzer = session["analyzer"]
    interpreter = session["interpreter"]

    if not code:
        return jsonify({
            "session_id": new_session_id,
            "output": [],
            "errors": [],
            "result": None
        })

    # Lexer
    lexer = Lexer(code)
    tokens, lex_errors = lexer.tokenize()
    if lex_errors:
        formatted_lex_errors = [
            "Error Léxico (Línea {}, Columna {}): {} (Lexema: '{}')".format(
                err.line, err.column, err.message, err.lexeme
            )
            for err in lex_errors
        ]
        return jsonify({
            "session_id": new_session_id,
            "output": [],
            "errors": formatted_lex_errors,
            "result": None
        })

    # Parser
    parser = Parser(tokens)
    ast = parser.parse()
    if parser.errors:
        return jsonify({
            "session_id": new_session_id,
            "output": [],
            "errors": parser.errors,
            "result": None
        })

    if ast is None:
        return jsonify({
            "session_id": new_session_id,
            "output": [],
            "errors": ["El analizador no generó ningún AST."],
            "result": None
        })

    # Semantic Analyzer
    sem_errors = analyzer.analyze(ast)
    if sem_errors:
        return jsonify({
            "session_id": new_session_id,
            "output": [],
            "errors": sem_errors,
            "result": None
        })

    # Interpreter
    output = []
    errors = []
    result_val = None

    if isinstance(ast, ProgramNode) and ast.statements:
        statements = ast.statements
        last_stmt = statements[-1]

        if isinstance(last_stmt, ExprStmtNode):
            other_statements = statements[:-1]
            if other_statements:
                output, runtime_errors = interpreter.interpret(ProgramNode(other_statements, line=ast.line), reset_state=False)
                if runtime_errors:
                    errors = [str(err) for err in runtime_errors]
                    return jsonify({
                        "session_id": new_session_id,
                        "output": output,
                        "errors": errors,
                        "result": None
                    })

            try:
                val = interpreter.visit(last_stmt.expression)
                if val is not None:
                    result_val = interpreter.format_value(val)
            except MathLiteRuntimeError as err:
                errors.append("Error en tiempo de ejecución (Línea {}): {}".format(
                    err.node.line if err.node else 0, err.message
                ))
            except Exception as err:
                errors.append("Error en tiempo de ejecución: {}".format(err))
        else:
            output, runtime_errors = interpreter.interpret(ast, reset_state=False)
            if runtime_errors:
                errors = [str(err) for err in runtime_errors]

    return jsonify({
        "session_id": new_session_id,
        "output": output,
        "errors": errors,
        "result": result_val
    })


@app.route("/api/repl/reset", methods=["POST"])
def repl_reset():
    data = request.get_json() or {}
    session_id = data.get("session_id")

    if session_id in repl_sessions:
        del repl_sessions[session_id]

    new_session_id, _ = get_repl_session(None)

    return jsonify({
        "success": True,
        "session_id": new_session_id,
        "message": "Entorno del REPL reiniciado."
    })


repl_sessions = {}

def get_repl_session(session_id):
    if not session_id or session_id not in repl_sessions:
        session_id = str(uuid.uuid4())
        repl_sessions[session_id] = {
            "analyzer": SemanticAnalyzer(),
            "interpreter": Interpreter()
        }
    return session_id, repl_sessions[session_id]


if __name__ == "__main__":
    app.run(debug=True)