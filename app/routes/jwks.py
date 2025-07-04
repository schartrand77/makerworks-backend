# app/routes/jwks.py

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from jwcrypto import jwk
from app.config import settings

router = APIRouter()

@router.get("/.well-known/jwks.json", include_in_schema=False)
async def serve_jwks():
    with open(settings.private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )

    public_key = private_key.public_key()
    public_jwk = jwk.JWK.from_pyca(public_key)
    public_jwk["kid"] = settings.private_key_kid
    return JSONResponse({"keys": [public_jwk.export(as_dict=True)]})
