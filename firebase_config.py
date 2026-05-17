import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(
            "firebase_credentials/firebase_key.json"
        )
        firebase_admin.initialize_app(cred)

    return firestore.client()