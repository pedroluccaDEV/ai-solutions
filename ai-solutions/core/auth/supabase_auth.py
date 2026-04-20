import os
import jwt
import requests
from functools import lru_cache
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("SUPABASE_URL ou SUPABASE_ANON_KEY não configurados")

security = HTTPBearer()

JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"


@lru_cache(maxsize=1)
def get_public_keys():
    response = requests.get(
        JWKS_URL,
        headers={"apikey": SUPABASE_ANON_KEY}
    )
    response.raise_for_status()

    jwks = response.json()

    keys = []
    for key in jwks.get("keys", []):
        alg = key.get("alg", "")

        if alg == "ES256":
            keys.append(jwt.algorithms.ECAlgorithm.from_jwk(key))
        elif alg == "RS256":
            keys.append(jwt.algorithms.RSAAlgorithm.from_jwk(key))

    return keys


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    token = credentials.credentials

    try:
        public_keys = get_public_keys()

        for key in public_keys:
            try:
                payload = jwt.decode(
                    token,
                    key,
                    algorithms=["ES256", "RS256"],
                    audience="authenticated",
                )

                return {
                    "uid": payload.get("sub"),
                    "email": payload.get("email"),
                    "role": payload.get("role"),
                }

            except jwt.InvalidTokenError:
                continue

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro de autenticação: {e}"
        )