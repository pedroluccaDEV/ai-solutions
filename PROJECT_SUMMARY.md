# AI Solutions - Documentação Completa do Projeto

## Visão Geral

**AI Solutions** é uma plataforma de serviços de IA composta por dois projetos:

| Projeto | Stack | Porta | Descrição |
|---------|-------|-------|-----------|
| `ai-solutions/` | FastAPI + Python | 8000 | Backend API — agentes de IA, multicanal, CRM, webhooks |
| `agents-interface/` | React 19 + Vite + TypeScript | 5173 | Frontend — landing pages e catálogo de soluções de IA |

---

## Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                       FRONTEND (React 19 + Vite)                │
│  Landing Pages  ·  Catálogo de Soluções  ·  Formulários        │
│  React Router v7  ·  Tailwind CSS  ·  Three.js                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP / REST
┌──────────────────────────────▼──────────────────────────────────┐
│                       BACKEND (FastAPI)                         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Controllers  │→ │  Services    │→ │  DAOs (Data Access)  │  │
│  │ (Rotas API)  │  │ (Lógica)    │  │  (MongoDB Queries)   │  │
│  └──────────────┘  └──────────────┘  └──────────┬───────────┘  │
│                                                  │              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────▼───────────┐  │
│  │   Features   │  │   Schemas    │  │    Databases         │  │
│  │ (AI Agents)  │  │ (Validação)  │  │ MongoDB · ChromaDB   │  │
│  └──────────────┘  └──────────────┘  │ PostgreSQL (Alembic) │  │
│                                      └──────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Integrações Externas                          │   │
│  │ WhatsApp (Evolution) · Telegram · Widget · Discord(WIP) │   │
│  │ OpenAI · DeepSeek · OpenRouter · Anthropic · Firecrawl  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Autenticação                                  │   │
│  │ Supabase JWT (ES256/RS256) · Firebase Admin             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Backend (`ai-solutions/`)

### Padrão Arquitetural: Layered Architecture

```
Controller  →  Service  →  DAO  →  MongoDB / PostgreSQL
   (HTTP)       (Lógica)    (Queries)   (Persistência)
```

### Estrutura de Diretórios

```
ai-solutions/
├── main.py                    # Entry point FastAPI — startup, CORS, middleware
├── requirements.txt           # Dependências Python
├── dockerfile                 # Docker: Ubuntu 24.04 + Python venv
├── Procfile                   # Deploy Railway: python railway_startup.py
├── alembic.ini                # Config Alembic (migrações PostgreSQL)
├── pytest.ini                 # Config testes
│
├── controllers/               # 🎯 Camada de apresentação (Rotas HTTP)
│   ├── agent_controller.py    #   CRUD de agentes de IA
│   ├── channel_controller.py  #   CRUD de canais (WhatsApp, Telegram, Widget)
│   ├── crm_controller.py      #   CRUD de leads + execução do agente CRM
│   └── webhook_saphien_controller.py  #   Webhook do widget Saphien
│
├── routes/
│   └── router_registery.py    # 🔌 Auto-discovery e registro dinâmico de rotas
│
├── schemas/                   # ✅ Validação de entrada (Pydantic)
│   ├── agent_schema.py        #   AgentCreateSchema, AgentUpdateSchema
│   ├── channel_schema.py      #   ChannelCreateSchema, metadata, preferences
│   ├── crm_schema.py          #   LeadCreate, LeadUpdate, AgentRunRequest
│   └── webhook_saphien_schema.py  #   MessagePayload, SessionPayload
│
├── services/                  # 💼 Camada de lógica de negócio
│   ├── agent_service.py       #   CRUD agentes + soft delete/reactivate
│   ├── channel_service.py     #   Gerenciamento de canais + handlers
│   ├── crm_service.py         #   Leads (in-memory) + agente CRM
│   ├── memory_chat_service.py #   Persistência de memória por sessão
│   ├── saphien_session_service.py  #   Sessões de visitantes do widget
│   └── webhook_saphien_service.py  #   Processamento de mensagens do widget
│
├── dao/                       # 🗄️ Data Access Objects
│   └── mongo/
│       ├── agent_dao.py       #   Queries MongoDB para agentes
│       ├── channel_dao.py     #   Queries MongoDB para canais
│       ├── memory_chat_dao.py #   Queries de memória de chat
│       └── saphien_session_dao.py  #   Queries de sessões do widget
│
├── models/                    # 📐 Modelos de dados MongoDB
│   ├── __init__.py
│   └── mongo/
│       ├── agent_model.py     #   Modelo: category, role, goal, tools, etc.
│       └── channel_model.py   #   Modelo: type, metadata, status, agents
│
├── core/                      # ⚙️ Configurações e infraestrutura
│   ├── auth/
│   │   └── supabase_auth.py   #   JWT verification (JWKS, ES256/RS256)
│   ├── config/
│   │   ├── settings.py        #   Variáveis de ambiente (Pydantic Settings)
│   │   ├── mongo.py           #   Conexão MongoDB (singleton, pool)
│   │   ├── chroma_client.py   #   Conexão ChromaDB (vector embeddings)
│   │   └── init_db.py         #   Inicialização de collections e indexes
│   └── database/
│       └── ...                #   Config PostgreSQL + Alembic
│
├── features/                  # 🤖 Módulos de IA e integrações
│   ├── base_flow/             #   Pipeline de execução de agentes
│   │   ├── agent_builder.py   #     Construção do agente (system prompt)
│   │   ├── planner_agent.py   #     Decomposição de tarefas
│   │   ├── executor_agent.py  #     Execução de passos + tools/MCPs
│   │   ├── chat_agent_streaming.py  # Streaming em tempo real
│   │   ├── session_title.py   #     Geração automática de título
│   │   └── enhance_prompt.py  #     Enriquecimento de prompt com contexto
│   │
│   ├── widget/                #   Widget Saphien (chat embeddable)
│   │   ├── agent/             #     Builder → Planner → Executor → Run
│   │   └── connection/        #     Geração de script + token
│   │
│   ├── crm_agent/             #   Agente CRM (classificação de leads)
│   │
│   └── evolution_agent/       #   Integração Evolution API (WhatsApp)
│
├── alembic/                   # 🔄 Migrações de banco PostgreSQL
│   ├── env.py
│   └── script.py.mako
│
└── scripts/                   # 🛠️ Scripts utilitários
    ├── create_database_table.py
    ├── populate_apps.py
    ├── export_mongodb.py
    ├── test_endpoints.py
    └── ... (50+ scripts de setup, migração e teste)
```

---

### Endpoints da API

#### Agentes (`/agents/`)

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| `POST` | `/agents/` | ✅ | Criar agente de IA |
| `GET` | `/agents/` | ✅ | Listar agentes do usuário |
| `GET` | `/agents/public` | ❌ | Listar agentes públicos |
| `GET` | `/agents/{id}` | ✅ | Buscar agente por ID |
| `PUT` | `/agents/{id}` | ✅ | Atualizar agente (completo) |
| `PATCH` | `/agents/{id}` | ✅ | Atualizar agente (parcial) |
| `DELETE` | `/agents/{id}` | ✅ | Soft delete (status=inactive) |
| `POST` | `/agents/{id}/reactivate` | ✅ | Reativar agente deletado |

#### Canais (`/channels/`)

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| `POST` | `/` | ✅ | Criar canal (evolution/telegram/webhook_saphien) |
| `GET` | `/` | ✅ | Listar canais do usuário (filtro por tipo) |
| `GET` | `/{id}` | ✅ | Buscar canal por ID |
| `GET` | `/by-instance/{type}/{name}` | ✅ | Buscar por instance_name |
| `PATCH` | `/{id}` | ✅ | Atualizar canal |
| `DELETE` | `/{id}` | ✅ | Desativar canal (enabled=false) |

**Limite**: 10 canais por tipo por usuário.

#### CRM (`/crm/`)

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| `POST` | `/leads` | ✅ | Criar lead |
| `GET` | `/leads` | ✅ | Listar leads |
| `GET` | `/leads/{id}` | ✅ | Buscar lead |
| `PATCH` | `/leads/{id}` | ✅ | Atualizar lead |
| `DELETE` | `/leads/{id}` | ✅ | Deletar lead |
| `POST` | `/agent/run` | ✅ | Executar agente CRM sobre um lead |

#### Widget Saphien (`/webhook_saphien/`)

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| `POST` | `/webhook_saphien` | Header: X-Widget-Token | Processar mensagem do visitante |
| `POST` | `/webhook_saphien/session` | Header: X-Widget-Token | Registrar sessão do visitante |
| `GET` | `/webhook_saphien/messages` | Header: X-Widget-Token | Buscar mensagens da sessão |

---

### Bancos de Dados

| Banco | Uso | Collections/Tabelas |
|-------|-----|---------------------|
| **MongoDB** | Dados principais | `agents`, `channels`, `chat_sessions`, `chat_messages`, `memory_user`, `memory_chat`, `saphien_sessions`, `saphien_messages` |
| **ChromaDB** | Embeddings vetoriais | Collections dinâmicas por knowledge base |
| **PostgreSQL** | Dados relacionais (via Alembic) | Preparado mas pouco utilizado atualmente |

---

### Pipeline de IA (Agent Execution)

```
Mensagem do Usuário
       │
       ▼
┌─────────────────┐
│  Agent Builder   │  ← Monta system prompt + regras + contexto
└────────┬────────┘
         ▼
┌─────────────────┐
│  Planner Agent   │  ← Decompõe em passos executáveis
└────────┬────────┘
         ▼
┌─────────────────┐
│  Executor Agent  │  ← Executa passos + chama tools/MCPs
└────────┬────────┘
         ▼
┌─────────────────┐
│  Streaming Chat  │  ← Resposta em tempo real (SSE)
└────────┬────────┘
         ▼
   Resposta Final
```

**LLMs Suportados**: OpenAI, DeepSeek, OpenRouter, Anthropic

---

### Canais de Comunicação

| Canal | Tipo | Status | Handler |
|-------|------|--------|---------|
| WhatsApp | `evolution` | ✅ Produção | Evolution API (QR Code, webhook) |
| Telegram | `telegram` | ✅ Ativo | Bot API (webhook) |
| Widget Web | `webhook_saphien` | ✅ Ativo | Token + allowed_origins |
| Discord | `discord` | 🔧 Estruturado | Bot token + guild_id (WIP) |

---

### Variáveis de Ambiente Necessárias

```env
# === Database ===
MONGO_URI=mongodb+srv://user:pass@cluster/...
MONGO_DB_NAME=zenith

# === Autenticação ===
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOi...
FIREBASE_API_KEY=AIza...
FIREBASE_AUTH_DOMAIN=projeto.firebaseapp.com
FIREBASE_PROJECT_ID=projeto-id
FIREBASE_STORAGE_BUCKET=projeto.appspot.com

# === LLM APIs ===
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com
ANTHROPIC_API_KEY=sk-ant-... (opcional)
FIRECRAWL_API_KEY=fc-...

# === Vector Database ===
CHROMA_URL=https://chroma-instance-url
CHROMA_AUTH=bearer-token

# === Evolution API (WhatsApp) ===
EVOLUTION_BASE_URL=https://evolution-api.example.com
EVOLUTION_API_KEY=api-key
EVOLUTION_WEBHOOK_PATH=/api/v1/evolution/webhook

# === Servidor ===
HOST=0.0.0.0
PORT=8000
PROJECT_NAME=Zenith Server
API_PREFIX=/api/v1
API_BASE_URL=https://api.seudominio.com

# === Contexto IA ===
MAX_CONTEXT_TOKENS=4096
MAX_HISTORY_RESPONSES=20

# === Dev (opcional) ===
DEV_USER_UID=uid-dev
DEV_USER_EMAIL=dev@email.com
LOG_LEVEL=INFO
```

---

## Frontend (`agents-interface/`)

### Stack Tecnológica

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| React | 19.2.4 | Framework UI |
| TypeScript | 5.9.3 | Tipagem estática |
| Vite | 8.0.1 | Build tool + HMR |
| React Router | 7.13.2 | Roteamento SPA |
| Tailwind CSS | 3.4.1 | Utilitários CSS |
| Three.js | 0.183.2 | Gráficos 3D (Trainify) |
| Lucide React | 1.8.0 | Biblioteca de ícones |

### Estrutura de Diretórios

```
agents-interface/
├── index.html                 # HTML base (SPA entry)
├── package.json               # Dependências + scripts
├── vite.config.ts             # Config Vite
├── tailwind.config.js         # Config Tailwind
├── tsconfig.json              # Config TypeScript
│
├── public/                    # Assets estáticos
│
└── src/
    ├── main.tsx               # Ponto de entrada React (Router)
    ├── App.tsx                # Componente demo (não usado nas rotas)
    ├── index.css              # Reset + Tailwind imports
    │
    ├── app/
    │   └── router.tsx         # 🗺️ Definição de rotas (createBrowserRouter)
    │
    ├── assets/                # Imagens e SVGs
    │   ├── hero.png
    │   ├── react.svg
    │   └── vite.svg
    │
    └── pages/                 # 📄 Páginas da aplicação
        ├── home/
        │   └── home.tsx       #   Landing principal — catálogo de soluções
        ├── cliniflow/
        │   └── cliniflow.tsx  #   CliniFlow AI — gestão de clínicas
        ├── ai-crm/
        │   └── ai-crm.tsx     #   AI CRM — automação de vendas
        ├── trainify-ai/
        │   └── trainify.tsx   #   Trainify AI — personal training (Three.js)
        └── contract-ai/
            └── contract-ai.tsx #  Contract AI — análise de contratos
```

### Rotas

| Rota | Página | Descrição |
|------|--------|-----------|
| `/` | Home | Catálogo principal com 6+ soluções de IA filtráveis |
| `/ai-crm` | AI CRM | Landing de automação de vendas e CRM |
| `/trainify` | Trainify | Landing de fitness com 3D shaders (Three.js) |
| `/contract-ai` | Contract AI | Landing de análise jurídica |
| `/cliniflow-ai` | CliniFlow AI | Landing de gestão de clínicas |

### Características do Frontend

- **Páginas self-contained**: cada página é um componente completo com CSS inline
- **Animações avançadas**: IntersectionObserver, keyframes, count-up, split-text
- **Renderização 3D**: Three.js com shaders customizados (Trainify)
- **Responsivo**: breakpoint mobile em 768px
- **Efeitos visuais**: Aurora backgrounds, glass cards, backdrop blur
- **Sem estado global**: apenas `useState`/`useRef` local
- **Sem integração API**: formulários não enviam dados (apenas UI)
- **Sem autenticação**: nenhuma página protegida

---

## Como Startar Cada Projeto

### Backend (`ai-solutions/`)

```bash
# 1. Navegar até o diretório
cd ai-solutions

# 2. Criar e ativar ambiente virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
# Criar arquivo .env com as variáveis listadas acima

# 5. Iniciar o servidor
python main.py
# → http://localhost:8000
# → Docs Swagger: http://localhost:8000/docs
```

**Via Docker:**
```bash
docker build -t ai-solutions .
docker run -p 8000:8000 --env-file .env ai-solutions
```

**Via Railway (produção):**
```bash
# Utiliza o Procfile: web: python railway_startup.py
```

### Frontend (`agents-interface/`)

```bash
# 1. Navegar até o diretório
cd agents-interface

# 2. Instalar dependências
npm install

# 3. Iniciar servidor de desenvolvimento
npm run dev
# → http://localhost:5173

# 4. Build de produção
npm run build

# 5. Preview do build
npm run preview
```

---

## Onde Incluir Autenticação com Supabase

### Status Atual

O **backend já possui** autenticação Supabase implementada em `core/auth/supabase_auth.py`:
- Verificação JWT via JWKS (ES256/RS256)
- Dependency `get_current_user` para rotas protegidas
- Extração de `uid`, `email` e `role` do token

O **frontend NÃO possui** nenhuma autenticação implementada.

### Onde Implementar no Frontend

```
agents-interface/src/
├── app/
│   ├── router.tsx             ← Adicionar rotas protegidas + /login + /signup
│   ├── auth/
│   │   ├── supabase-client.ts ← 🆕 Inicializar createClient(@supabase/supabase-js)
│   │   ├── auth-context.tsx   ← 🆕 React Context com estado de auth
│   │   ├── auth-provider.tsx  ← 🆕 Provider com onAuthStateChange
│   │   └── protected-route.tsx← 🆕 Wrapper para rotas que exigem login
│   ├── hooks/
│   │   └── use-auth.ts        ← 🆕 Hook useAuth() para acessar usuário
│   └── services/
│       └── api.ts             ← 🆕 Cliente HTTP com token Bearer automático
│
├── pages/
│   ├── auth/
│   │   ├── login.tsx          ← 🆕 Página de login
│   │   └── signup.tsx         ← 🆕 Página de cadastro
│   └── dashboard/
│       └── dashboard.tsx      ← 🆕 Área logada (gerenciar agentes, canais, etc.)
```

### Passo a Passo Recomendado

#### 1. Instalar SDK do Supabase no Frontend

```bash
cd agents-interface
npm install @supabase/supabase-js
```

#### 2. Criar Cliente Supabase (`src/app/auth/supabase-client.ts`)

```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

#### 3. Criar Auth Context (`src/app/auth/auth-context.tsx`)

```typescript
import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from './supabase-client'
import type { User, Session } from '@supabase/supabase-js'

interface AuthState {
  user: User | null
  session: Session | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session)
        setUser(session?.user ?? null)
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  const signIn = async (email: string, password: string) => {
    await supabase.auth.signInWithPassword({ email, password })
  }

  const signUp = async (email: string, password: string) => {
    await supabase.auth.signUp({ email, password })
  }

  const signOut = async () => {
    await supabase.auth.signOut()
  }

  return (
    <AuthContext.Provider value={{ user, session, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
```

#### 4. Criar Rota Protegida (`src/app/auth/protected-route.tsx`)

```typescript
import { Navigate } from 'react-router-dom'
import { useAuth } from './auth-context'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) return <div>Carregando...</div>
  if (!user) return <Navigate to="/login" replace />

  return <>{children}</>
}
```

#### 5. Criar Serviço de API com Token Automático (`src/app/services/api.ts`)

```typescript
import { supabase } from '../auth/supabase-client'

const API_BASE = import.meta.env.VITE_API_URL // ex: http://localhost:8000

export async function apiFetch(path: string, options: RequestInit = {}) {
  const { data: { session } } = await supabase.auth.getSession()

  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${session?.access_token}`,
      ...options.headers,
    },
  })
}
```

#### 6. Atualizar Router com Rotas Protegidas

```typescript
// src/app/router.tsx
import { ProtectedRoute } from './auth/protected-route'
import Login from '../pages/auth/login'
import Dashboard from '../pages/dashboard/dashboard'

const router = createBrowserRouter([
  { path: '/', element: <Home /> },
  { path: '/login', element: <Login /> },
  { path: '/signup', element: <Signup /> },
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    ),
  },
  // ... rotas públicas existentes
])
```

#### 7. Envolver App com AuthProvider

```typescript
// src/main.tsx
import { AuthProvider } from './app/auth/auth-context'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </React.StrictMode>
)
```

#### 8. Adicionar Variáveis de Ambiente no Frontend

```env
# agents-interface/.env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOi...
VITE_API_URL=http://localhost:8000
```

### Fluxo Completo de Autenticação

```
Frontend (React)                    Backend (FastAPI)              Supabase
     │                                    │                          │
     │  1. signIn(email, password) ───────────────────────────────► │
     │  ◄──────────────────────────── JWT access_token ──────────── │
     │                                    │                          │
     │  2. API Request                    │                          │
     │  Authorization: Bearer <token> ──► │                          │
     │                                    │  3. Verify JWT           │
     │                                    │  JWKS → decode → uid ──►│
     │                                    │  ◄── validated ──────── │
     │                                    │                          │
     │  ◄── Response (dados do user) ──── │                          │
```

### Pontos de Atenção

| Local | Arquivo | O que fazer |
|-------|---------|-------------|
| Backend Auth | `core/auth/supabase_auth.py` | ✅ Já implementado — verificação JWT funcional |
| Backend Routes | `controllers/*_controller.py` | ✅ Já usam `Depends(get_current_user)` |
| Frontend Client | `src/app/auth/supabase-client.ts` | 🆕 Criar — inicializar SDK |
| Frontend Context | `src/app/auth/auth-context.tsx` | 🆕 Criar — gerenciar estado de auth |
| Frontend Pages | `src/pages/auth/login.tsx` | 🆕 Criar — UI de login |
| Frontend Router | `src/app/router.tsx` | ✏️ Modificar — adicionar rotas protegidas |
| Frontend API | `src/app/services/api.ts` | 🆕 Criar — enviar token Bearer em requests |
| Frontend ENV | `.env` | 🆕 Criar — VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY |

---

## Resumo de Funcionalidades por Diretório

| Diretório | Responsabilidade |
|-----------|-----------------|
| `controllers/` | Endpoints HTTP, validação de request, orquestração |
| `services/` | Lógica de negócio, handlers de canais, processamento |
| `dao/mongo/` | Queries MongoDB, serialização de ObjectId, indexes |
| `models/mongo/` | Definição de campos e indexes das collections |
| `schemas/` | Validação de entrada/saída com Pydantic |
| `core/auth/` | Verificação JWT Supabase (JWKS) |
| `core/config/` | Settings, conexões de banco, inicialização |
| `features/base_flow/` | Pipeline de IA: builder → planner → executor → streaming |
| `features/widget/` | Widget chat embeddable (Saphien) |
| `features/crm_agent/` | Agente de classificação de leads |
| `features/evolution_agent/` | Integração WhatsApp via Evolution API |
| `routes/` | Auto-discovery e registro de rotas |
| `alembic/` | Migrações PostgreSQL |
| `scripts/` | Utilidades: setup, migração, populate, testes |
| `pages/` (frontend) | Landing pages das soluções de IA |
| `app/` (frontend) | Router e configuração da SPA |
