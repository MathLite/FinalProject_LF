from flask import Flask, render_template, request
from runner import run_code
from test_case_repository import TestCaseRepository


app = Flask(__name__)
repository = TestCaseRepository()


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
    test_cases = repository.get_last_test_cases(10)

    if request.method == "POST":
        code = request.form.get("code", "")
        result = run_code(code)
        saved_id = repository.save_test_case(code, result)
        test_cases = repository.get_last_test_cases(10)

    return render_template(
        "index.html",
        code=code,
        result=result,
        saved_id=saved_id,
        test_cases=test_cases
    )


if __name__ == "__main__":
    app.run(debug=True)