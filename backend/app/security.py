import base64, os, json
from fastapi import HTTPException
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

def require_api_key(x_api_key: str | None):
    if settings.INGEST_API_KEY:
        if not x_api_key or x_api_key != settings.INGEST_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")

def _key() -> bytes:
    if not settings.ENCRYPTION_KEY:
        raise RuntimeError("ENCRYPTION_KEY not set")
    k = base64.b64decode(settings.ENCRYPTION_KEY)
    if len(k) != 32:
        raise RuntimeError("ENCRYPTION_KEY must be base64 of 32 bytes")
    return k

def encrypt_json(obj: dict) -> dict:
    data = json.dumps(obj).encode("utf-8")
    aes = AESGCM(_key())
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, data, None)
    return {"nonce": base64.b64encode(nonce).decode(), "ciphertext": base64.b64encode(ct).decode()}

def decrypt_json(enc: dict) -> dict:
    aes = AESGCM(_key())
    nonce = base64.b64decode(enc["nonce"])
    ct = base64.b64decode(enc["ciphertext"])
    data = aes.decrypt(nonce, ct, None)
    return json.loads(data.decode("utf-8"))
