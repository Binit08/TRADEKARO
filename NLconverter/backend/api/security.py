import os
from cryptography.fernet import Fernet

def get_fernet():
    key = os.getenv("MASTER_ENCRYPTION_KEY")
    if key:
        return Fernet(key.encode())
    return None

def encrypt_secret(secret: str) -> str:
    f = get_fernet()
    if f and secret:
        return f.encrypt(secret.encode()).decode()
    return secret

def decrypt_secret(encrypted_secret: str) -> str:
    f = get_fernet()
    if f and encrypted_secret:
        try:
            return f.decrypt(encrypted_secret.encode()).decode()
        except Exception:
            return encrypted_secret
    return encrypted_secret
