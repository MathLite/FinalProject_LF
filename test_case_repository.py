import os
import json
from datetime import datetime, timedelta

import firebase_admin
from firebase_admin import credentials, firestore


"""
Módulo: test_case_repository.py

Este módulo centraliza la comunicación con Firebase Firestore para almacenar,
consultar, actualizar y eliminar casos de prueba del proyecto MathLite.

Su propósito es separar la lógica de persistencia de datos de la aplicación web.
De esta manera, Flask no necesita conocer directamente los detalles de conexión
con Firebase, sino que utiliza esta clase como una capa intermedia.

Funciones principales:
- save_test_case(): guarda un caso ejecutado por el usuario.
- get_all_test_cases(): obtiene el historial de casos almacenados.
- get_test_case_by_id(): recupera un caso específico por identificador.
- get_test_suite(): obtiene la suite de casos de prueba.
- save_suite_case(): agrega un nuevo caso a la suite.
- update_suite_case(): actualiza un caso existente.
- delete_suite_case(): elimina un caso de la suite.
- seed_default_suite_if_empty(): carga casos iniciales si la colección está vacía.
"""

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
        cases.sort(key=lambda x: x.get("created_at_local") or x.get("created_at") or "", reverse=True)
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
        # ======================================================
        # PROGRAMAS VÁLIDOS
        # ======================================================
        {
            "id": "valid-1",
            "name": "Programa válido básico",
            "category": "Programas Válidos",
            "code": """let x = 5
    let y = 2
    let z = x + y * 3
    print(z)"""
        },
        {
            "id": "valid-2",
            "name": "Actualización con let",
            "category": "Programas Válidos",
            "code": """let x = 10
    let x = 20
    print(x)"""
        },
        {
            "id": "valid-3",
            "name": "If no crea alcance independiente",
            "category": "Programas Válidos",
            "code": """if true {
        let y = 20
    }

    print(y)"""
        },
        {
            "id": "valid-4",
            "name": "Función no modifica variable global",
            "category": "Programas Válidos",
            "code": """let x = 10

    def prueba() {
        let x = 5
        return x
    }

    print(prueba())
    print(x)"""
        },
        {
            "id": "valid-5",
            "name": "Recursividad no modifica global",
            "category": "Programas Válidos",
            "code": """let n = 100

    def factorial(n) {
        if n <= 1 {
            return 1
        }

        return n * factorial(n - 1)
    }

    print(factorial(5))
    print(n)"""
        },

        # ======================================================
        # ERRORES LÉXICOS
        # ======================================================
        {
            "id": "lex-1",
            "name": "Símbolo inválido",
            "category": "Errores Léxicos",
            "code": """let x = 5 @ 2
    print(x)"""
        },
        {
            "id": "lex-2",
            "name": "Cadena sin cerrar",
            "category": "Errores Léxicos",
            "code": """print("hola)"""
        },
        {
            "id": "lex-3",
            "name": "Símbolo numeral no permitido",
            "category": "Errores Léxicos",
            "code": """let y = 10 # 3"""
        },
        {
            "id": "lex-4",
            "name": "Carácter dólar no reconocido",
            "category": "Errores Léxicos",
            "code": """let total = 50 $ 2"""
        },
        {
            "id": "lex-5",
            "name": "Carácter arroba en identificador",
            "category": "Errores Léxicos",
            "code": """let nombre@ = 10"""
        },

        # ======================================================
        # ERRORES SINTÁCTICOS
        # Casos exclusivos de sintaxis.
        # No incluyen errores semánticos posteriores.
        # ======================================================
        {
            "id": "syntax-1",
            "name": "Paréntesis sin cerrar en print",
            "category": "Errores Sintácticos",
            "code": """print(2 + 3"""
        },
        {
            "id": "syntax-2",
            "name": "Función sin bloque",
            "category": "Errores Sintácticos",
            "code": """def suma(a, b)
        return a + b"""
        },
        {
            "id": "syntax-3",
            "name": "If sin bloque",
            "category": "Errores Sintácticos",
            "code": """if true
        print(1)"""
        },
        {
            "id": "syntax-4",
            "name": "While sin bloque",
            "category": "Errores Sintácticos",
            "code": """while true
        print(1)"""
        },
        {
            "id": "syntax-5",
            "name": "Función integrada sin paréntesis",
            "category": "Errores Sintácticos",
            "code": """print(sin)"""
        },

        # ======================================================
        # ERRORES SEMÁNTICOS
        # Sintaxis correcta, pero significado incorrecto.
        # ======================================================
        {
            "id": "semantic-1",
            "name": "Variable no declarada",
            "category": "Errores Semánticos",
            "code": """print(x)"""
        },
        {
            "id": "semantic-2",
            "name": "Aridad incorrecta",
            "category": "Errores Semánticos",
            "code": """def suma(a, b) {
        return a + b
    }

    print(suma(5))"""
        },
        {
            "id": "semantic-3",
            "name": "Tipos incompatibles",
            "category": "Errores Semánticos",
            "code": """print("hola" + 5)"""
        },
        {
            "id": "semantic-4",
            "name": "Return fuera de función",
            "category": "Errores Semánticos",
            "code": """return 5"""
        },
        {
            "id": "semantic-5",
            "name": "Variable local no existe fuera de función",
            "category": "Errores Semánticos",
            "code": """def prueba() {
        let secreto = 7
        return secreto
    }

    print(prueba())
    print(secreto)"""
        },

        # ======================================================
        # ERRORES EN TIEMPO DE EJECUCIÓN
        # Léxico, sintaxis y semántica correctos.
        # Fallan durante la interpretación.
        # ======================================================
        {
            "id": "runtime-1",
            "name": "División por cero",
            "category": "Errores en Tiempo de Ejecución",
            "code": """let x = 10 / 0
    print(x)"""
        },
        {
            "id": "runtime-2",
            "name": "Módulo por cero",
            "category": "Errores en Tiempo de Ejecución",
            "code": """let x = 10 % 0
    print(x)"""
        },
        {
            "id": "runtime-3",
            "name": "Raíz cuadrada de número negativo",
            "category": "Errores en Tiempo de Ejecución",
            "code": """print(sqrt(-1))"""
        },
        {
            "id": "runtime-4",
            "name": "Logaritmo de cero",
            "category": "Errores en Tiempo de Ejecución",
            "code": """print(log(0))"""
        },
        {
            "id": "runtime-5",
            "name": "Límite de iteraciones",
            "category": "Errores en Tiempo de Ejecución",
            "code": """let x = 1

    while x > 0 {
        let x = x + 1
    }

    print(x)"""
        }
    ]


        base_time = datetime.now()
        batch = self.db.batch()
        for idx, case in enumerate(default_cases):
            doc_ref = self.suite_collection.document()
            # Descending order sorting (reverse=True) is used.
            # So the first case (idx=0) should have the newest timestamp (base_time),
            # and subsequent cases will have older timestamps (base_time - seconds).
            case_time = base_time - timedelta(seconds=idx)
            case_data = {
                **case,
                "created_at": firestore.SERVER_TIMESTAMP,
                "created_at_local": case_time.isoformat()
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