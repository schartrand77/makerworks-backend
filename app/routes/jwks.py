# app/routes/jwks.py

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.backends import default_backend
from jwcrypto import jwk

from app.config.settings import settings
from app.models import User
from app.dependencies.auth import get_user_from_headers

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 🔷 Load and cache JWK at startup
def load_jwk():
    with open(settings.private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )

    if isinstance(private_key, rsa.RSAPrivateKey):
        public_key = private_key.public_key()
    elif isinstance(private_key, ec.EllipticCurvePrivateKey):
        public_key = private_key.public_key()
    else:
        raise ValueError("Unsupported key type for JWKS")

    jwk_obj = jwk.JWK.from_pyca(public_key)
    jwk_obj["kid"] = settings.private_key_kid
    jwk_obj["alg"] = settings.jwt_algorithm  # e.g., RS256
    jwk_obj["use"] = "sig"

    return jwk_obj.export(as_dict=True)


# 🔷 Load at startup & reuse
JWKS_KEYS = [load_jwk()]


@router.get("/.well-known/jwks.json", include_in_schema=False)
async def serve_jwks(user: User = Depends(get_user_from_headers)):
    """
    Serve JWKS (JSON Web Key Set) containing the public signing key(s).
    """
    logger.debug("Serving JWKS with %d key(s)", len(JWKS_KEYS))
    response = JSONResponse({"keys": JWKS_KEYS})
    # Optional: tell clients they can cache it
    response.headers["Cache-Control"] = "public, max-age=300"
    return response