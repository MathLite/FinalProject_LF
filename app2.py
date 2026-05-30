import uuid
from flask import Flask, render_template, request, jsonify
from runner import run_code
from lexer import Lexer
from syntax_parser import Parser
from semantic_analyzer import SemanticAnalyzer
from interpreter import Interpreter, MathLiteRuntimeError, RuntimeErrorInfo
from ASTNode import ProgramNode, ExprStmtNode


app = Flask(__name__)


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

    # Firebase desactivado temporalmente.
    # El historial se envía vacío para no romper el HTML.
    test_cases = []

    if request.method == "POST":
        code = request.form.get("code", "")
        result = run_code(code)

        # No se guarda en Firebase.
        saved_id = None

    return render_template(
        "index.html",
        code=code,
        result=result,
        saved_id=saved_id,
        test_cases=test_cases
    )


@app.route("/api/test-cases/<case_id>", methods=["GET"])
def get_test_case(case_id):
    return jsonify({
        "success": False,
        "message": "Firebase está desactivado temporalmente. No es posible recuperar casos de prueba."
    }), 503


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
                output, runtime_errors = interpreter.interpret(ProgramNode(other_statements, line=ast.line))
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
            output, runtime_errors = interpreter.interpret(ast)
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