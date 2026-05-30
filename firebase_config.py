import os
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

def initialize_firebase():
    if not firebase_admin._apps:
        firebase_key_env = os.environ.get("FIREBASE_KEY_JSON") or os.environ.get("FIREBASE_CREDENTIALS_JSON")
        
        if firebase_key_env:
            try:
                cred_dict = json.loads(firebase_key_env)
                cred = credentials.Certificate(cred_dict)
            except Exception as e:
                cred = credentials.Certificate(
                    "firebase_credentials/firebase_key.json"
                )
        else:
            cred = credentials.Certificate(
                "firebase_credentials/firebase_key.json"
            )
            
        firebase_admin.initialize_app(cred)

    return firestore.client()