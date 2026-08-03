import firebase_admin
from firebase_admin import credentials, auth, db
import os

# Inisialisasi Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred, {
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL")
})

def verify_token(token: str) -> dict:
    """
    Memverifikasi JWT Token dari Firebase Authentication
    menggunakan firebase_admin.auth.verify_id_token()
    """
    try:

        decoded_token = auth.verify_id_token(
            token,
            clock_skew_seconds=10
        )

        print("TOKEN VERIFIED")
        print(decoded_token)

        return decoded_token

    except Exception as e:

        print("VERIFY TOKEN ERROR:")
        print(type(e))
        print(str(e))

        raise e

def get_db_reference(path: str):
    """
    Mengambil referensi Firebase Realtime Database
    berdasarkan path yang diberikan
    """
    return db.reference(path)
