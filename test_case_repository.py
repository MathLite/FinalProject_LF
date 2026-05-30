import os
import json
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore


class TestCaseRepository:
    def __init__(self):
        if not firebase_admin._apps:
            firebase_key_env = os.environ.get("FIREBASE_KEY_JSON") or os.environ.get("FIREBASE_CREDENTIALS_JSON")
            if firebase_key_env:
                try:
                    cred_dict = json.loads(firebase_key_env)
                    cred = credentials.Certificate(cred_dict)
                except Exception as e:
                    # Si falla, intentar buscar el archivo
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    credential_path = os.path.join(
                        base_dir,
                        "firebase_credentials",
                        "firebase_key.json"
                    )
                    if not os.path.exists(credential_path):
                        raise FileNotFoundError(
                            f"No se encontró la credencial de Firebase en entorno ni en archivo local: {e}"
                        )
                    cred = credentials.Certificate(credential_path)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                credential_path = os.path.join(
                    base_dir,
                    "firebase_credentials",
                    "firebase_key.json"
                )
                if not os.path.exists(credential_path):
                    raise FileNotFoundError(
                        "No se encontró el archivo firebase_key.json y tampoco está la variable FIREBASE_KEY_JSON ni FIREBASE_CREDENTIALS_JSON."
                    )
                cred = credentials.Certificate(credential_path)

            firebase_admin.initialize_app(cred)

        self.db = firestore.client()
        self.collection = self.db.collection("test_cases")
        self.suite_collection = self.db.collection("test_suite")

    def sanitize_for_json(self, data):
        """
        Sanea los datos para que puedan ser serializados a JSON de manera segura.
        Convierte objetos datetime a cadenas ISO y maneja los sentinelas de Firebase.
        """
        if isinstance(data, dict):
            return {k: self.sanitize_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_for_json(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        elif hasattr(data, '__class__') and ('Sentinel' in data.__class__.__name__ or 'Sentinel' in str(type(data))):
            return datetime.now().isoformat()
        return data

    def get_value(self, result, key, default=None):
        """
        Permite leer el resultado tanto si es diccionario como si es objeto.
        """
        if isinstance(result, dict):
            return result.get(key, default)

        return getattr(result, key, default)

    def save_test_case(self, code, result):
        tokens = self.get_value(result, "tokens", [])
        lexical_errors = self.get_value(result, "lexical_errors", [])

        data = {
            "code": code,
            "success": self.get_value(result, "success", False),
            "phase": self.get_value(result, "phase", "UNKNOWN"),
            "output": self.get_value(result, "output", []),
            "tokens": self.serialize_tokens(tokens),
            "lexical_errors": self.serialize_lexical_errors(lexical_errors),
            "syntax_errors": self.get_value(result, "syntax_errors", []),
            "semantic_errors": self.get_value(result, "semantic_errors", []),
            "runtime_errors": self.get_value(result, "runtime_errors", []),
            "ast": self.get_value(result, "ast", ""),
            "created_at": firestore.SERVER_TIMESTAMP,
            "created_at_local": datetime.now().isoformat()
        }

        doc_ref = self.collection.document()
        doc_ref.set(data)

        return doc_ref.id

    def get_last_test_cases(self, limit=10):
        docs = (
            self.collection
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )

        cases = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            cases.append(data)

        return cases

    def get_all_test_cases(self):
        docs = (
            self.collection
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .stream()
        )

        cases = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            cases.append(data)

        return cases

    def get_test_case_by_id(self, case_id):
        doc = self.collection.document(case_id).get()

        if not doc.exists:
            return None

        data = doc.to_dict()
        data["id"] = doc.id

        return data

    def serialize_tokens(self, tokens):
        serialized = []

        if not tokens:
            return serialized

        for token in tokens:
            if isinstance(token, dict):
                serialized.append({
                    "type": token.get("type"),
                    "lexeme": token.get("lexeme"),
                    "line": token.get("line"),
                    "column": token.get("column")
                })
            else:
                serialized.append({
                    "type": token.type,
                    "lexeme": token.lexeme,
                    "line": token.line,
                    "column": token.column
                })

        return serialized

    def serialize_lexical_errors(self, errors):
        serialized = []

        if not errors:
            return serialized

        for error in errors:
            if isinstance(error, dict):
                serialized.append({
                    "message": error.get("message"),
                    "line": error.get("line"),
                    "column": error.get("column"),
                    "lexeme": error.get("lexeme")
                })
            else:
                serialized.append({
                    "message": error.message,
                    "line": error.line,
                    "column": error.column,
                    "lexeme": error.lexeme
                })

        return serialized

    def get_test_suite(self):
        docs = self.suite_collection.stream()
        cases = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            cases.append(self.sanitize_for_json(data))
        cases.sort(key=lambda x: x.get("created_at") or x.get("created_at_local") or "", reverse=True)
        return cases

    def save_suite_case(self, name, category, code):
        data = {
            "name": name,
            "category": category,
            "code": code,
            "created_at": firestore.SERVER_TIMESTAMP,
            "created_at_local": datetime.now().isoformat(),
            "is_default": False
        }
        doc_ref = self.suite_collection.document()
        doc_ref.set(data)
        data["id"] = doc_ref.id
        return self.sanitize_for_json(data)

    def seed_default_suite_if_empty(self):
        docs = self.suite_collection.limit(1).get()
        if len(docs) > 0:
            return

        default_cases = [
            # Programas Válidos
            {
                "name": "Fibonacci Recursivo con Evaluación de Tipos",
                "category": "Programas Válidos",
                "code": "def fib(n) {\n    if n <= 1 {\n        return n\n    }\n    return fib(n - 1) + fib(n - 2)\n}\nprint(fib(7))",
                "is_default": True
            },
            {
                "name": "Algoritmo de Euclides (MCD) y Modulo",
                "category": "Programas Válidos",
                "code": "def mcd(a, b) {\n    while b != 0 {\n        let temp = b\n        let b = a % b\n        let a = temp\n    }\n    return a\n}\nprint(mcd(48, 18))",
                "is_default": True
            },
            {
                "name": "Verificación de Números Primos y Retorno Temprano",
                "category": "Programas Válidos",
                "code": "def es_primo(n) {\n    if n <= 1 {\n        return false\n    }\n    let i = 2\n    while i * i <= n {\n        if n % i == 0 {\n            return false\n        }\n        let i = i + 1\n    }\n    return true\n}\nprint(es_primo(17))",
                "is_default": True
            },
            {
                "name": "Cálculos Trigonométricos y Matemáticos Aninados",
                "category": "Programas Válidos",
                "code": "let a = abs(-10.5)\nlet b = floor(a)\nlet c = ceil(a)\nlet val = log(sqrt(b^2 + c^2))\nprint(val)",
                "is_default": True
            },
            {
                "name": "Evaluación Compleja de Booleanos y Cortocircuito",
                "category": "Programas Válidos",
                "code": "let x = 10\nlet y = 20\nlet cond1 = x < y and not (x == 10) or y >= 20\nlet cond2 = (x + y == 30) and (true or false)\nif cond1 and cond2 {\n    print(\"Expresion valida\")\n}",
                "is_default": True
            },

            # Errores Léxicos
            {
                "name": "Cadena sin comilla de cierre en bloque",
                "category": "Errores Léxicos",
                "code": "def test() {\n    let x = \"cadena sin terminar\n}",
                "is_default": True
            },
            {
                "name": "Carácter inválido (@) en aritmética",
                "category": "Errores Léxicos",
                "code": "let a = 10 + 20 @ 3",
                "is_default": True
            },
            {
                "name": "Carácter no soportado (#) en declaración",
                "category": "Errores Léxicos",
                "code": "def calcular#area(r) {\n    return 3.14 * r^2\n}",
                "is_default": True
            },
            {
                "name": "Identificador con prefijo inválido ($)",
                "category": "Errores Léxicos",
                "code": "let $variable = 100",
                "is_default": True
            },
            {
                "name": "Símbolos no permitidos ([) al final del bloque",
                "category": "Errores Léxicos",
                "code": "let x = 10\nlet y = 20 [",
                "is_default": True
            },

            # Errores Sintácticos
            {
                "name": "Paréntesis desbalanceados en función integrada",
                "category": "Errores Sintácticos",
                "code": "let x = sin(cos(3.14)",
                "is_default": True
            },
            {
                "name": "Definición de función sin cuerpo o llaves",
                "category": "Errores Sintácticos",
                "code": "def duplicar(x)\n    return x * 2",
                "is_default": True
            },
            {
                "name": "Operador binario sin operando derecho",
                "category": "Errores Sintácticos",
                "code": "let x = 10 + (20 * )",
                "is_default": True
            },
            {
                "name": "Bucle while sin llaves ni bloque",
                "category": "Errores Sintácticos",
                "code": "while x < 10",
                "is_default": True
            },
            {
                "name": "Sentencia else huérfana sin bloque if",
                "category": "Errores Sintácticos",
                "code": "else {\n    print(\"error\")\n}",
                "is_default": True
            },

            # Errores Semánticos
            {
                "name": "Redeclaración de variable en el mismo bloque",
                "category": "Errores Semánticos",
                "code": "let x = 10\nlet x = 20",
                "is_default": True
            },
            {
                "name": "Sentencia return fuera del cuerpo de función",
                "category": "Errores Semánticos",
                "code": "let x = 10\nreturn x",
                "is_default": True
            },
            {
                "name": "Suma inválida de tipos incompatibles (Cadena + Entero)",
                "category": "Errores Semánticos",
                "code": "let x = \"hola\" + 10",
                "is_default": True
            },
            {
                "name": "Llamada a función con número incorrecto de argumentos",
                "category": "Errores Semánticos",
                "code": "def suma(a, b) {\n    return a + b\n}\nlet res = suma(1, 2, 3)",
                "is_default": True
            },
            {
                "name": "Variable no declarada en condición de bucle",
                "category": "Errores Semánticos",
                "code": "while variable_inexistente < 10 {\n    print(1)\n}",
                "is_default": True
            },

            # Errores de Ejecución
            {
                "name": "División por cero explícita",
                "category": "Errores en Tiempo de Ejecución",
                "code": "let resultado = 100 / 0",
                "is_default": True
            },
            {
                "name": "División por cero con variable dinámica",
                "category": "Errores en Tiempo de Ejecución",
                "code": "let x = 10 - 10\nlet y = 50 / x",
                "is_default": True
            },
            {
                "name": "Módulo por cero en expresión matemática",
                "category": "Errores en Tiempo de Ejecución",
                "code": "let res = 15 % (3 * 0)",
                "is_default": True
            },
            {
                "name": "Bucle infinito por límite de iteraciones",
                "category": "Errores en Tiempo de Ejecución",
                "code": "while true {\n    let x = 1\n}",
                "is_default": True
            },
            {
                "name": "Raíz cuadrada de número negativo (Error de dominio)",
                "category": "Errores en Tiempo de Ejecución",
                "code": "let x = sqrt(-9)",
                "is_default": True
            }
        ]

        batch = self.db.batch()
        for case in default_cases:
            doc_ref = self.suite_collection.document()
            case_data = {
                **case,
                "created_at": firestore.SERVER_TIMESTAMP,
                "created_at_local": datetime.now().isoformat()
            }
            batch.set(doc_ref, case_data)
        batch.commit()

    def delete_suite_case(self, case_id):
        self.suite_collection.document(case_id).delete()

    def update_suite_case(self, case_id, name, category, code):
        doc_ref = self.suite_collection.document(case_id)
        doc_ref.update({
            "name": name,
            "category": category,
            "code": code,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        data = doc_ref.get().to_dict()
        data["id"] = case_id
        return self.sanitize_for_json(data)