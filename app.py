from flask import Flask, render_template, request, jsonify
from runner import run_code
from test_case_repository import TestCaseRepository


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


if __name__ == "__main__":
    app.run(debug=True)