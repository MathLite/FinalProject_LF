from flask import Flask, render_template, request
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
    i = i + 1
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

    if request.method == "POST":
        code = request.form.get("code", "")
        result = run_code(code)

    return render_template(
        "index.html",
        code=code,
        result=result
    )


if __name__ == "__main__":
    app.run(debug=True)