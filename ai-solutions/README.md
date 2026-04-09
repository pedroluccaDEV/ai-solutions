# 🏗️ Manual Compacto de Arquitetura FastAPI

## 📐 Estrutura e Princípios

```
api-server/
├── controllers/v1/    # HTTP endpoints (orquestração apenas)
├── services/v1/       # Lógica de negócio
├── dao/              # Acesso a dados
│   ├── mongo/v1/     # MongoDB (sync)
│   └── postgres/v1/  # PostgreSQL (async)
├── schemas/v1/       # Validação Pydantic
├── models/           # ORM/Documentos
├── core/
│   ├── auth/         # Firebase
│   └── config/       # Database, settings
└── routes/           # Registro de rotas
```

**Princípios**: Controllers orquestram → Services validam → DAOs persistem. PostgreSQL async, MongoDB sync, lazy initialization.

---

## ⚙️ Configuração

### Settings (core/config/settings.py)
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_URL: str  # postgresql+asyncpg://...
    MONGO_URI: str
    MONGO_DB_NAME: str
    FIREBASE_PROJECT_ID: str
    OPENAI_API_KEY: str
    CHROMA_URL: str
    model_config = {"env_file": ".env", "extra": "ignore"}
```

### Database (core/config/database.py)
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from pymongo import MongoClient

# PostgreSQL (async)
async_engine = create_async_engine(settings.POSTGRES_URL)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession)

async def get_postgres_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# MongoDB (sync, lazy)
_mongo_client = None
_mongo_db = None

def get_mongo_db():
    global _mongo_client, _mongo_db
    if _mongo_client is None:
        _mongo_client = MongoClient(settings.MONGO_URI)
        _mongo_db = _mongo_client[settings.MONGO_DB_NAME]
    return _mongo_db
```

### Firebase Auth (core/auth/)
```python
# get_credentials.py
def get_firebase_credentials():
    client = MongoClient(os.getenv("MONGO_URI"))
    doc = client[os.getenv("MONGO_DB_NAME")].firebase_config.find_one()
    del doc["_id"]
    doc["private_key"] = doc["private_key"].replace("\\n", "\n")
    return doc

# firebase_auth.py
from firebase_admin import auth, credentials, initialize_app

@lru_cache()
def init_firebase():
    if not firebase_admin._apps:
        initialize_app(credentials.Certificate(get_firebase_credentials()))

def verify_token(request: Request) -> dict:
    token = request.headers.get("Authorization", "").split(" ")[1]
    if token == "dev-token-12345":
        return {"uid": "dev-user-id", "email": "dev@example.com"}
    return auth.verify_id_token(token)

async def get_current_user(token_data: dict = Depends(verify_token)) -> dict:
    return {"uid": token_data["uid"], "email": token_data.get("email")}
```

---

## 🧱 Implementação em Camadas

### 1. Schema (schemas/v1/agent_schema.py)
```python
from pydantic import BaseModel
from typing import List, Optional, Literal

class AgentCreateSchema(BaseModel):
    category: str
    roleDefinition: str
    goal: str
    agentRules: str
    whenToUse: str
    model: int
    visibility: Literal["public", "private"]
    color: str
    knowledgeBase: Optional[List[str]] = []
    tools: Optional[List[str]] = []
    status: Literal["active", "inactive"] = "active"

class AgentUpdateSchema(BaseModel):  # Todos opcionais
    category: Optional[str] = None
    roleDefinition: Optional[str] = None
    # ... demais campos opcionais
```

### 2. DAO (dao/mongo/v1/agent_dao.py)
```python
from bson import ObjectId
from datetime import datetime

class AgentDAO:
    _db = None
    _collection = None
    
    @classmethod
    def _get_collection(cls):
        if cls._collection is None:
            from core.config.database import get_mongo_db
            cls._collection = get_mongo_db().agents
        return cls._collection
    
    @classmethod
    def create_agent(cls, agent_data, uid: str) -> dict:
        data = agent_data.dict(exclude_unset=True)
        data.update({
            "uid": uid,
            "knowledgeBase": data.get("knowledgeBase") or [],
            "tools": data.get("tools") or [],
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        })
        result = cls._get_collection().insert_one(data)
        created = cls._get_collection().find_one({"_id": result.inserted_id})
        created["_id"] = str(created["_id"])
        return created
    
    @classmethod
    def get_agent_by_id(cls, agent_id: str, uid: str) -> Optional[dict]:
        # Busca público ou privado do usuário
        agent = cls._get_collection().find_one({
            "$or": [
                {"_id": ObjectId(agent_id), "visibility": "public", "status": "active"},
                {"_id": ObjectId(agent_id), "uid": uid, "status": "active"}
            ]
        })
        if agent:
            agent["_id"] = str(agent["_id"])
        return agent
    
    @classmethod
    def delete_agent(cls, agent_id: str, uid: str) -> bool:
        # Soft delete
        result = cls._get_collection().update_one(
            {"_id": ObjectId(agent_id), "uid": uid},
            {"$set": {"status": "inactive", "updatedAt": datetime.utcnow()}}
        )
        return result.matched_count > 0
```

### 3. Service (services/v1/agent_service.py)
```python
class AgentService:
    @staticmethod
    def create_agent(db, agent_data, uid: str) -> dict:
        validation = AgentService.validate_agent_references(db, agent_data)
        if not validation["valid"]:
            raise ValueError(f"Referências inválidas: {validation['errors']}")
        return AgentDAO.create_agent(agent_data, uid)
    
    @staticmethod
    def validate_agent_references(db, agent_data) -> dict:
        errors = []
        # Validar knowledgeBase, tools, mcps IDs
        return {"valid": len(errors) == 0, "errors": errors}
    
    @staticmethod
    def delete_agent(db, agent_id: str, uid: str) -> bool:
        deleted = AgentDAO.delete_agent(agent_id, uid)
        if deleted:
            # Limpar dependências (sessões, etc)
            pass
        return deleted
```

### 4. Controller (controllers/v1/agent_controller.py)
```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.post("/", status_code=201)
def create_agent(
    agent_data: AgentCreateSchema,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db)
):
    try:
        agent = AgentService.create_agent(db, agent_data, current_user["uid"])
        return {"agent": agent}
    except ValueError as e:
        raise HTTPException(400, detail=str(e))

@router.get("/{agent_id}")
def get_agent(agent_id: str, current_user: dict = Depends(get_current_user), db = Depends(get_mongo_db)):
    agent = AgentService.get_agent_by_id(db, agent_id, current_user["uid"])
    if not agent:
        raise HTTPException(404, "Agente não encontrado")
    return agent

@router.patch("/{agent_id}")
def partial_update(agent_id: str, updates: AgentUpdateSchema, current_user: dict = Depends(get_current_user), db = Depends(get_mongo_db)):
    update_dict = updates.dict(exclude_unset=True)
    if not update_dict:
        raise HTTPException(400, "Nenhum campo para atualizar")
    current = AgentService.get_agent_by_id(db, agent_id, current_user["uid"])
    merged = AgentCreateSchema(**{**current, **update_dict})
    return AgentService.update_agent(db, agent_id, merged, current_user["uid"])

@router.delete("/{agent_id}", status_code=204)
def delete_agent(agent_id: str, current_user: dict = Depends(get_current_user), db = Depends(get_mongo_db)):
    if not AgentService.delete_agent(db, agent_id, current_user["uid"]):
        raise HTTPException(404, "Agente não encontrado")
```

### 5. Registro (routes/router_registry.py)
```python
from fastapi import APIRouter
from controllers.v1 import agent_controller

router = APIRouter(prefix="/api/v1")
router.include_router(agent_controller.router)
```

---

## 📋 Regras Essenciais

### Nomenclatura
- Arquivos: `snake_case` (agent_controller.py)
- Classes: `PascalCase` (AgentService)
- Funções: `camelCase` (createAgent)

### Banco de Dados
- PostgreSQL: `AsyncSession`, `await`, `async def`
- MongoDB: sync, lazy init em DAOs
- Soft delete: `status="inactive"`, nunca deletar

### Autenticação
```python
# Header obrigatório
Authorization: Bearer <token>

# Controller
current_user: dict = Depends(get_current_user)
# Retorna: {"uid": "...", "email": "..."}
```

### Padrões REST
| Verbo | Rota | Schema | Status |
|-------|------|--------|--------|
| POST | `/agents` | CreateSchema | 201 |
| GET | `/agents/{id}` | - | 200 |
| PATCH | `/agents/{id}` | UpdateSchema | 200 |
| DELETE | `/agents/{id}` | - | 204 |

---

## ✅ Checklist

- [ ] Controller só orquestra (sem lógica de negócio)
- [ ] Service valida e coordena DAOs
- [ ] DAO com lazy init (MongoDB) ou async (PostgreSQL)
- [ ] Schemas separados Create/Update
- [ ] Soft delete implementado
- [ ] `Depends(get_current_user)` em rotas privadas
- [ ] Listas vazias como `[]` não `None`
- [ ] Logging (não print)
- [ ] Type hints
- [ ] Versionamento `/api/v1`

---

**Ordem de implementação**: Schema → DAO → Service → Controller → Router Registry



**Atualização de memoria de agente tanto para PLayground quanto para chat**

Fazer um sistema que gurarda na mesma coleção:
- memoria a curto prazo de 4 a 6 mensagens relevantes para o contexto da conversa atual, sobre o que estamos falando agora
- resumo a longo prazo da sessao inteira, onde contem um resumo sobre informações importantes e assuntos mencuonados na sessao ineitra (atualizado de X em X interações)

o formato esperado ao banco similar a 

- session_id
- memory_short (últimas mensagens relevantes)
- memory_summary (contexto condensado da sessão)
- outros metadados necessários

**Atualização a tomada de decisão sob uso de tools/mcps/base de conehcimento**

Camada de filtragem rapida
- compara solicitação do usuário com descrição da tool usando keywords  ou embeddings leves
- cira um filtro de recursos disponiveis compativeis com a solicitação, e disponiviliza somente os relevantes evitando conexao com multiplas ferramentas que nao serão utilizadas