from datetime import datetime
from firebase_admin import firestore
from firebase_config import initialize_firebase


class TestCaseRepository:
    def __init__(self):
        self.db = initialize_firebase()
        self.collection_name = "test_cases"

    def save_test_case(self, code, result):
        data = {
            "code": code,
            "success": result.get("success"),
            "phase": result.get("phase"),
            "output": result.get("output"),
            "lexical_errors": result.get("lexical_errors"),
            "syntax_errors": result.get("syntax_errors"),
            "semantic_errors": result.get("semantic_errors"),
            "runtime_errors": result.get("runtime_errors"),
            "created_at": datetime.utcnow(),
        }

        doc_ref = self.db.collection(self.collection_name).document()
        doc_ref.set(data)

        return doc_ref.id

    def get_last_test_cases(self, limit=10):
        docs = (
            self.db.collection(self.collection_name)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )

        test_cases = []

        for doc in docs:
            item = doc.to_dict()
            item["id"] = doc.id
            test_cases.append(item)

        return test_cases