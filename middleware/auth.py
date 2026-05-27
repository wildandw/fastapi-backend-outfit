from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.firebase import verify_token

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    Mengekstrak dan memverifikasi Bearer Token dari header Authorization
    menggunakan firebase_admin.auth.verify_id_token()
    Mengembalikan decoded token berisi uid dan email pengguna
    """
    try:
        token = credentials.credentials
        decoded_token = verify_token(token)
        return decoded_token
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Token tidak valid atau sudah kadaluarsa"
        )
