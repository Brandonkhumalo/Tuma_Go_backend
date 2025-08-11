import os, json
import firebase_admin
from firebase_admin import credentials, initialize_app

'''def initialize_firebase():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(BASE_DIR, 'delivery.json')

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)'''

# Get JSON string from environment variable
firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS")

# Parse it
firebase_creds_dict = json.loads(firebase_creds_json)

# Initialize Firebase Admin SDK
cred = credentials.Certificate(firebase_creds_dict)
firebase_admin.initialize_app(cred)