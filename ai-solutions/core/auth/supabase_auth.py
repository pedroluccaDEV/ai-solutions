import os
import time
import jwt
import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("SUPABASE_URL ou SUPABASE_ANON_KEY não configurados")

security = HTTPBearer()
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"

# Cache manual com TTL (10 minutos)
# lru_cache sem TTL é perigoso pois Supabase pode rotacionar as chaves
_jwks_cache: dict = {"keys": [], "fetched_at": 0}
JWKS_TTL = 600  # segundos


def get_public_keys() -> list:
    """
    Busca as chaves públicas do Supabase (JWKS) com cache de 10 minutos.
    Supabase usa ES256 por padrão nos projetos mais novos.
    """
    now = time.time()

    # Usa o cache se ainda estiver válido
    if _jwks_cache["keys"] and (now - _jwks_cache["fetched_at"]) < JWKS_TTL:
        return _jwks_cache["keys"]

    try:
        response = requests.get(
            JWKS_URL,
            headers={"apikey": SUPABASE_ANON_KEY},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        # Se já tínhamos chaves em cache, usa o stale (melhor que falhar)
        if _jwks_cache["keys"]:
            return _jwks_cache["keys"]
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Não foi possível buscar chaves JWKS: {e}",
        )

    jwks = response.json()
    keys = []
    for key_data in jwks.get("keys", []):
        alg = key_data.get("alg", "")
        try:
            if alg == "ES256":
                keys.append(jwt.algorithms.ECAlgorithm.from_jwk(key_data))
            elif alg == "RS256":
                keys.append(jwt.algorithms.RSAAlgorithm.from_jwk(key_data))
        except Exception:
            continue  # Ignora chaves malformadas

    if not keys:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nenhuma chave pública válida encontrada no JWKS",
        )

    _jwks_cache["keys"] = keys
    _jwks_cache["fetched_at"] = now
    return keys


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Valida o JWT do Supabase e retorna os dados do usuário autenticado.
    
    Uso nos controllers:
        current_user: dict = Depends(get_current_user)
        uid = current_user["uid"]
    """
    token = credentials.credentials
    public_keys = get_public_keys()  # HTTPException já tratada dentro da função

    last_error = None

    for key in public_keys:
        try:
            payload = jwt.decode(
                token,
                key,
                algorithms=["ES256", "RS256"],
                audience="authenticated",
            )
            return {
                "uid": payload["sub"],           # UUID do usuário
                "email": payload.get("email"),
                "role": payload.get("role"),
                "app_metadata": payload.get("app_metadata", {}),
                "user_metadata": payload.get("user_metadata", {}),
            }

        # Bug corrigido: trata ExpiredSignatureError ANTES de InvalidTokenError
        # pois ExpiredSignatureError é subclasse de InvalidTokenError
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            last_error = e
            continue  # Tenta a próxima chave

    # Nenhuma chave conseguiu validar o token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Token inválido: {last_error}",
        headers={"WWW-Authenticate": "Bearer"},
    )