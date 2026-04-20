"""
Teste isolado: Supabase Auth + Create Agent (sem dependência de settings.py / MongoDB)

Como usar:
  1. python test_auth_isolated.py
     → Sobe um servidor FastAPI mínimo em http://localhost:9999

  2. Em outro terminal, teste COM token válido:
     curl -X POST http://localhost:9999/agents/ \
       -H "Authorization: Bearer SEU_TOKEN_SUPABASE" \
       -H "Content-Type: application/json" \
       -d '{"category":"support","roleDefinition":"Agente de teste","goal":"Testar auth","agentRules":"Nenhuma","whenToUse":"Testes","model":1,"visibility":"public","color":"#00FF00"}'

  3. Teste SEM token (deve retornar 403):
     curl -X POST http://localhost:9999/agents/ \
       -H "Content-Type: application/json" \
       -d '{"category":"test"}'

  4. Teste com token INVÁLIDO (deve retornar 401):
     curl -X POST http://localhost:9999/agents/ \
       -H "Authorization: Bearer token_invalido_aqui" \
       -H "Content-Type: application/json" \
       -d '{"category":"test"}'

  Para obter um token válido do Supabase, use o endpoint:
     curl -X POST https://SEU_PROJETO.supabase.co/auth/v1/token?grant_type=password \
       -H "apikey: SUA_ANON_KEY" \
       -H "Content-Type: application/json" \
       -d '{"email":"seu@email.com","password":"sua_senha"}'
"""

import os
import uvicorn
from dotenv import load_dotenv

# Carrega .env ANTES de qualquer import que use os.getenv
load_dotenv()

# ── Imports do auth (NÃO depende de settings.py) ──
from core.auth.supabase_auth import get_current_user

# ── Imports do schema (NÃO depende de DB) ──
from schemas.agent_schema import AgentCreateSchema

from fastapi import FastAPI, Depends, HTTPException, status
from datetime import datetime, timezone


app = FastAPI(title="Teste Isolado - Auth + Create Agent")


# ────────────────────────────────────────────────────
# Rota 1: Health check (sem auth)
# ────────────────────────────────────────────────────
@app.get("/health")
def health():
    supabase_url = os.getenv("SUPABASE_URL", "NÃO CONFIGURADO")
    return {
        "status": "ok",
        "supabase_url": supabase_url,
        "message": "Servidor de teste rodando. Auth isolado pronto."
    }


# ────────────────────────────────────────────────────
# Rota 2: Testar APENAS o auth (quem sou eu?)
# ────────────────────────────────────────────────────
@app.get("/me")
def who_am_i(current_user: dict = Depends(get_current_user)):
    return {
        "message": "✅ Auth funcionando!",
        "user": current_user
    }


# ────────────────────────────────────────────────────
# Rota 3: Simular create_agent COM auth (mock, sem DB)
# ────────────────────────────────────────────────────
@app.post("/agents/", status_code=status.HTTP_201_CREATED)
def create_agent(
    agent_data: AgentCreateSchema,
    current_user: dict = Depends(get_current_user),
):
    """
    Simula o controller create_agent REAL, mas retorna mock ao invés de salvar no MongoDB.
    Isso testa:
      - Validação do JWT Supabase (get_current_user)
      - Validação do body (AgentCreateSchema / Pydantic)
      - Extração do uid do token
    """
    now = datetime.now(timezone.utc)
    mock_agent = {
        "_id": "mock_id_12345",
        "uid": current_user["uid"],
        **agent_data.model_dump(),
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat(),
    }

    print(f"\n{'='*60}")
    print(f"✅ AUTH OK — Usuário autenticado:")
    print(f"   uid:   {current_user['uid']}")
    print(f"   email: {current_user.get('email')}")
    print(f"   role:  {current_user.get('role')}")
    print(f"\n📦 AGENT DATA recebido (Pydantic validou):")
    for key, value in agent_data.model_dump().items():
        print(f"   {key}: {value}")
    print(f"{'='*60}\n")

    return mock_agent


# ────────────────────────────────────────────────────
# Rota 4: Gerar token de teste (login direto no Supabase)
# ────────────────────────────────────────────────────
@app.post("/auth/login")
def login(email: str, password: str):
    """
    Helper: faz login no Supabase e retorna o access_token.
    Uso: POST /auth/login?email=seu@email.com&password=suasenha
    """
    import requests
    
    supabase_url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not anon_key:
        raise HTTPException(500, "SUPABASE_URL ou SUPABASE_ANON_KEY não configurados no .env")
    
    resp = requests.post(
        f"{supabase_url}/auth/v1/token?grant_type=password",
        json={"email": email, "password": password},
        headers={
            "apikey": anon_key,
            "Content-Type": "application/json",
        },
        timeout=10,
    )
    
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, f"Erro Supabase: {resp.text}")
    
    data = resp.json()
    return {
        "message": "✅ Login OK! Use o access_token abaixo no header Authorization: Bearer <token>",
        "access_token": data.get("access_token"),
        "expires_in": data.get("expires_in"),
        "user_id": data.get("user", {}).get("id"),
        "email": data.get("user", {}).get("email"),
    }


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 SERVIDOR DE TESTE ISOLADO")
    print("=" * 60)
    print(f"  SUPABASE_URL: {os.getenv('SUPABASE_URL', '❌ NÃO CONFIGURADO')}")
    print(f"  SUPABASE_ANON_KEY: {'✅ configurado' if os.getenv('SUPABASE_ANON_KEY') else '❌ NÃO CONFIGURADO'}")
    print()
    print("  Endpoints disponíveis:")
    print("    GET  /health        → Health check (sem auth)")
    print("    GET  /me            → Testar auth (retorna dados do user)")
    print("    POST /agents/       → Simular create_agent com auth")
    print("    POST /auth/login    → Fazer login e obter token")
    print("    GET  /docs          → Swagger UI interativo")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=9999)
