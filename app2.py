from flask import Flask, render_template, request, jsonify
from runner import run_code


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


if __name__ == "__main__":
    app.run(debug=True)