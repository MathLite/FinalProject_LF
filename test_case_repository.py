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
            {
                "name": "Precedencia Mixta",
                "category": "Programas Válidos",
                "code": "print((3 + 4 * 2) / (1 - 5)^2)",
                "is_default": True
            },
            {
                "name": "Factorial Recursivo",
                "category": "Programas Válidos",
                "code": "def factorial(n) {\n    if n <= 1 {\n        return 1\n    }\n    return n * factorial(n - 1)\n}\nprint(factorial(5))",
                "is_default": True
            },
            {
                "name": "Ciclo Acumulador (1 a n)",
                "category": "Programas Válidos",
                "code": "let n = 10\nlet suma = 0\nlet i = 1\nwhile i <= n {\n    let suma = suma + i\n    let i = i + 1\n}\nprint(suma)",
                "is_default": True
            },
            {
                "name": "Funciones Trigonométricas y Matemáticas",
                "category": "Programas Válidos",
                "code": "let x = sin(0.5) * cos(0.5) + sqrt(16)\nprint(x)",
                "is_default": True
            },
            {
                "name": "Llamadas entre funciones",
                "category": "Programas Válidos",
                "code": "def duplicar(x) {\n    return x * 2\n}\ndef procesar(n) {\n    return duplicar(n) + 10\n}\nprint(procesar(5))",
                "is_default": True
            },
            {
                "name": "Definiciones y Aritmética Simple",
                "category": "Programas Válidos",
                "code": "let a = 15\nlet b = 30\nprint(a + b)",
                "is_default": True
            },
            {
                "name": "Comparaciones Lógicas",
                "category": "Programas Válidos",
                "code": "let edad = 20\nlet puede_votar = edad >= 18 and true\nprint(puede_votar)",
                "is_default": True
            },
            {
                "name": "Cálculo de Área de Círculo",
                "category": "Programas Válidos",
                "code": "let pi = 3.14159\nlet r = 5\nlet area = pi * r^2\nprint(area)",
                "is_default": True
            },

            # Errores Léxicos
            {
                "name": "Carácter inválido (@)",
                "category": "Errores Léxicos",
                "code": "let x = 10 @ 5",
                "is_default": True
            },
            {
                "name": "Carácter inválido (#)",
                "category": "Errores Léxicos",
                "code": "let y = # 100",
                "is_default": True
            },
            {
                "name": "Cadena sin comilla de cierre",
                "category": "Errores Léxicos",
                "code": "let str = \"cadena sin terminar",
                "is_default": True
            },
            {
                "name": "Carácter inválido (?)",
                "category": "Errores Léxicos",
                "code": "let x = ?",
                "is_default": True
            },
            {
                "name": "Identificador inválido ($)",
                "category": "Errores Léxicos",
                "code": "let $val = 5",
                "is_default": True
            },

            # Errores Sintácticos
            {
                "name": "Paréntesis sin cerrar",
                "category": "Errores Sintácticos",
                "code": "let x = (3 + 4 * 2",
                "is_default": True
            },
            {
                "name": "Función sin llaves de bloque",
                "category": "Errores Sintácticos",
                "code": "def suma(a, b)\n    return a + b",
                "is_default": True
            },
            {
                "name": "Sentencia if sin condición",
                "category": "Errores Sintácticos",
                "code": "if {\n    print(\"hola\")\n}",
                "is_default": True
            },
            {
                "name": "Declaración let sin asignación",
                "category": "Errores Sintácticos",
                "code": "let x",
                "is_default": True
            },
            {
                "name": "Ciclo while sin llaves de bloque",
                "category": "Errores Sintácticos",
                "code": "while true\n    print(\"bucle\")",
                "is_default": True
            },

            # Errores Semánticos
            {
                "name": "Variable no declarada",
                "category": "Errores Semánticos",
                "code": "print(x)",
                "is_default": True
            },
            {
                "name": "Aridad incorrecta de argumentos",
                "category": "Errores Semánticos",
                "code": "def suma(a, b) {\n    return a + b\n}\nprint(suma(5))",
                "is_default": True
            },
            {
                "name": "Tipos incompatibles (+)",
                "category": "Errores Semánticos",
                "code": "let res = \"hola\" + 5",
                "is_default": True
            },
            {
                "name": "Return fuera de función",
                "category": "Errores Semánticos",
                "code": "let valor = 10\nreturn valor",
                "is_default": True
            },
            {
                "name": "Redeclaración de variable en el mismo bloque",
                "category": "Errores Semánticos",
                "code": "let x = 10\nlet x = 20",
                "is_default": True
            },

            # Errores de Ejecución
            {
                "name": "División por cero",
                "category": "Errores en Tiempo de Ejecución",
                "code": "let r = 10 / 0",
                "is_default": True
            },
            {
                "name": "Llamada a función no definida",
                "category": "Errores en Tiempo de Ejecución",
                "code": "print(funcion_inexistente(10))",
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