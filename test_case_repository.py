import os
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore


class TestCaseRepository:
    def __init__(self):
        if not firebase_admin._apps:
            base_dir = os.path.dirname(os.path.abspath(__file__))

            credential_path = os.path.join(
                base_dir,
                "firebase_credentials",
                "firebase_key.json"
            )

            if not os.path.exists(credential_path):
                raise FileNotFoundError(
                    "No se encontró el archivo firebase_key.json. "
                    "Verifica que esté ubicado en firebase_credentials/firebase_key.json"
                )

            cred = credentials.Certificate(credential_path)
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()
        self.collection = self.db.collection("test_cases")

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