#!/usr/bin/env python3
"""
MAESTRO AI ORCHESTRATOR - VERSÃO INTEGRADA
Agente de IA Orquestrador com LLM Real e Memória Avançada

Funcionalidades:
- Planejamento inteligente com respostas reais do DeepSeek
- Execução dinâmica com agentes especialistas reais
- Gerenciamento avançado de memória (MongoDB + ChromaDB)
- Sistema de tokens integrado (PostgreSQL)
- Cache inteligente e otimização
- Integração com ChromaDB para memória vetorial
"""

import asyncio
import json
import logging
import os
import sys
import time
import hashlib
import tiktoken
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from textwrap import dedent
from uuid import uuid4

# Importações do OpenAI/DeepSeek
from openai import OpenAI

# Importações do sistema de banco
from pymongo import MongoClient
from pymongo.database import Database
from bson import ObjectId
import asyncpg
from asyncpg.pool import Pool
from dotenv import load_dotenv

# Importações do ChromaDB (com tratamento de erro)
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
    print("[INFO] ChromaDB disponível para memória vetorial.")
except ImportError:
    chromadb = None
    CHROMADB_AVAILABLE = False
    print("[WARN] ChromaDB não encontrado. Funcionalidade de memória vetorial desativada.")

# Configuração
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Variáveis de ambiente
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:root@localhost:5433/saphien")

# Verificar se pelo menos um provedor está configurado
if not DEEPSEEK_API_KEY and not os.getenv("OPENAI_API_KEY"):
    logger.error("Nenhuma API key de provedor LLM encontrada! Configure pelo menos DEEPSEEK_API_KEY ou OPENAI_API_KEY")
    sys.exit(1)

class TaskComplexity(Enum):
    """Enum para definir complexidade da tarefa"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXPERT = "expert"

class AgentType(Enum):
    """Tipos de agentes especializados"""
    GENERAL = "general"
    ANALYST = "analyst"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    RESEARCH = "research"
    PROBLEM_SOLVER = "problem_solver"

@dataclass
class ExecutionPlan:
    """Estrutura do plano de execução"""
    task_id: str
    complexity: TaskComplexity
    required_agents: List[AgentType]
    tools_needed: List[str]
    kb_sources: List[str]
    steps: List[Dict[str, Any]]
    estimated_time: float
    priority: int = 1

@dataclass
class AgentConfig:
    """Configuração de agente especialista"""
    agent_id: str
    agent_type: AgentType
    personality: str
    temperature: float
    max_tokens: int
    tools: List[str]
    knowledge_bases: List[str]
    specialization: str
    system_prompt: str

@dataclass
class TaskResult:
    """Resultado de execução de tarefa"""
    task_id: str
    success: bool
    result: Any
    execution_time: float
    agent_used: str
    tokens_used: Dict[str, int]
    metadata: Dict[str, Any]

class DynamicLLM:
    """Interface dinâmica para diferentes provedores LLM"""
    
    def __init__(self, provider_config: Dict[str, Any] = None):
        if provider_config is None:
            # Configuração padrão (DeepSeek)
            provider_config = {
                "provider_name": "DeepSeek",
                "package_name": "openai",
                "provider_class": "OpenAI",
                "config_key": "DEEPSEEK_API_KEY",
                "api_key": os.environ.get("DEEPSEEK_API_KEY"),
                "api_base_url": "https://api.deepseek.com/v1",
                "model_name": "deepseek-chat"
            }
        
        self.provider_config = provider_config
        self.model_id = provider_config.get("model_name", "deepseek-chat")
        
        # Log da configuração do provedor e modelo
        logger.info(f"🔄 [MAESTRO LLM] Configurando provedor: {provider_config.get('provider_name', 'Desconhecido')}")
        logger.info(f"🔄 [MAESTRO LLM] Configurando modelo: {self.model_id}")
        logger.info(f"🔄 [MAESTRO LLM] Configuração completa: {provider_config}")
        
        self.client = self._create_client()
        
        try:
            self.encoding = tiktoken.encoding_for_model("gpt-4")
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def _create_client(self):
        """Cria o cliente do provedor dinamicamente"""
        try:
            package_name = self.provider_config["package_name"]
            provider_class = self.provider_config["provider_class"]
            api_key = self.provider_config["api_key"]
            base_url = self.provider_config.get("api_base_url")
            
            # Importar módulo dinamicamente
            module = __import__(package_name, fromlist=[provider_class])
            ProviderClass = getattr(module, provider_class)
            
            # Criar cliente
            if base_url:
                return ProviderClass(api_key=api_key, base_url=base_url)
            else:
                return ProviderClass(api_key=api_key)
                
        except Exception as e:
            logger.error(f"Erro ao criar cliente para {self.provider_config['provider_name']}: {e}")
            # Fallback para configuração padrão (DeepSeek) apenas se disponível
            if os.environ.get("DEEPSEEK_API_KEY"):
                logger.warning(f"Usando fallback para DeepSeek devido a erro no provedor {self.provider_config['provider_name']}")
                return OpenAI(api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1")
            else:
                logger.error(f"Nenhum provedor disponível para fallback. Erro: {e}")
                raise
    
    def count_tokens(self, text: str) -> int:
        """Conta tokens no texto"""
        return len(self.encoding.encode(text))
    
    def generate_response(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2000) -> Dict[str, Any]:
        """Gera resposta usando o provedor configurado"""
        try:
            # Log do início da geração de resposta
            logger.info(f"🔄 [MAESTRO LLM] Iniciando geração de resposta com provedor: {self.provider_config['provider_name']}")
            logger.info(f"🔄 [MAESTRO LLM] Modelo sendo utilizado: {self.model_id}")
            logger.info(f"🔄 [MAESTRO LLM] Configurações: temperature={temperature}, max_tokens={max_tokens}")
            
            # Conta tokens de entrada
            input_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            input_tokens = self.count_tokens(input_text)
            
            # Log antes da chamada à API
            logger.info(f"🔄 [MAESTRO LLM] Chamando API do provedor {self.provider_config['provider_name']} com modelo {self.model_id}")
            
            completion = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response_content = completion.choices[0].message.content
            output_tokens = self.count_tokens(response_content)
            
            # Log do sucesso
            logger.info(f"✅ [MAESTRO LLM] Resposta gerada com sucesso usando {self.provider_config['provider_name']} - {self.model_id}")
            logger.info(f"✅ [MAESTRO LLM] Tokens utilizados: input={input_tokens}, output={output_tokens}, total={input_tokens + output_tokens}")
            
            return {
                'content': response_content,
                'tokens_used': {
                    'input': input_tokens,
                    'output': output_tokens,
                    'total': input_tokens + output_tokens
                },
                'model': self.model_id,
                'provider': self.provider_config['provider_name'],
                'success': True
            }
        except Exception as e:
            logger.error(f"❌ [MAESTRO LLM] Erro na geração de resposta com {self.provider_config['provider_name']}: {e}")
            return {
                'content': f"Erro ao gerar resposta: {str(e)}",
                'tokens_used': {'input': 0, 'output': 0, 'total': 0},
                'model': self.model_id,
                'provider': self.provider_config['provider_name'],
                'success': False,
                'error': str(e)
            }

class PostgreSQLTokenTracker:
    """Rastreador de tokens usando PostgreSQL"""
    
    def __init__(self, pool: Pool):
        self.pool = pool
    
    async def initialize_tables(self):
        """Cria tabelas se não existirem"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS token_control_user (
                    id SERIAL PRIMARY KEY,
                    uid VARCHAR(255) NOT NULL,
                    llm_model VARCHAR(255) NOT NULL,
                    token_input INTEGER NOT NULL DEFAULT 0,
                    token_output INTEGER NOT NULL DEFAULT 0,
                    update_datetime TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    update_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    UNIQUE(uid, llm_model, update_date)
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS token_control_session (
                    id SERIAL PRIMARY KEY,
                    uid VARCHAR(255) NOT NULL,
                    llm_model VARCHAR(255) NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    token_input INTEGER NOT NULL DEFAULT 0,
                    token_output INTEGER NOT NULL DEFAULT 0,
                    update_datetime TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
    
    async def track_tokens(self, uid: str, model: str, session_id: str, input_tokens: int, output_tokens: int):
        """Registra uso de tokens"""
        async with self.pool.acquire() as conn:
            # Atualiza/insere tokens do usuário
            result = await conn.execute(
                """UPDATE token_control_user SET token_input = token_input + $1, 
                   token_output = token_output + $2, update_datetime = CURRENT_TIMESTAMP 
                   WHERE uid = $3 AND llm_model = $4 AND update_date = CURRENT_DATE""",
                input_tokens, output_tokens, uid, model
            )
            
            if result == "UPDATE 0":
                await conn.execute(
                    """INSERT INTO token_control_user (uid, llm_model, token_input, token_output, update_date) 
                       VALUES ($1, $2, $3, $4, CURRENT_DATE)""",
                    uid, model, input_tokens, output_tokens
                )
            
            # Registra tokens da sessão
            await conn.execute(
                """INSERT INTO token_control_session (uid, llm_model, session_id, token_input, token_output) 
                   VALUES ($1, $2, $3, $4, $5)""",
                uid, model, session_id, input_tokens, output_tokens
            )

class ChromaDBVectorMemory:
    """Sistema de memória vetorial usando ChromaDB"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        
        if CHROMADB_AVAILABLE:
            try:
                self.client = chromadb.PersistentClient(path=persist_directory)
                self.collection = self.client.get_or_create_collection(
                    name="maestro_memory",
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"ChromaDB inicializado em: {persist_directory}")
            except Exception as e:
                logger.error(f"Erro ao inicializar ChromaDB: {e}")
                self.client = None
    
    def add_memory(self, uid: str, session_id: str, content: str, metadata: Dict[str, Any] = None):
        """Adiciona memória vetorial"""
        if not self.client:
            return
        
        try:
            doc_id = f"{uid}_{session_id}_{int(time.time())}"
            self.collection.add(
                documents=[content],
                ids=[doc_id],
                metadatas=[{
                    "uid": uid,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {})
                }]
            )
        except Exception as e:
            logger.error(f"Erro ao adicionar memória vetorial: {e}")
    
    def query_memories(self, uid: str, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Consulta memórias relevantes"""
        if not self.client:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"uid": uid}
            )
            
            memories = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    memories.append({
                        'role': 'system',
                        'content': f"Memória relevante: {doc}",
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                    })
            
            return memories
        except Exception as e:
            logger.error(f"Erro ao consultar memória vetorial: {e}")
            return []

class KnowledgeBaseQuerySystem:
    """Sistema de consulta a bases de conhecimento e anexos de sessão"""
    
    def __init__(self):
        self.chroma_wrapper = None
        self._setup_chroma_wrapper()
    
    def _setup_chroma_wrapper(self):
        """Configura o wrapper do ChromaDB"""
        try:
            from features.tests.agents.agent_knowledge.chroma_client_wrapper import ChromaDbWrapper
            self.chroma_wrapper = ChromaDbWrapper
            print("[INFO] ChromaDB wrapper configurado para consulta de bases de conhecimento")
        except ImportError as e:
            print(f"[WARN] ChromaDbWrapper não encontrado. Funcionalidade de bases de conhecimento limitada. Erro: {e}")
            self.chroma_wrapper = None
    
    def query_knowledge_bases(self, knowledge_base_ids: List[str], query: str, n_results: int = 3, session_id: str = None) -> List[Dict[str, Any]]:
        """Consulta múltiplas bases de conhecimento e anexos de sessão, retorna conteúdo relevante"""
        if not self.chroma_wrapper:
            print("[WARN] ChromaDB wrapper não disponível")
            return []
        
        try:
            all_results = []
            
            # Consulta bases de conhecimento tradicionais
            if knowledge_base_ids:
                for kb_id in knowledge_base_ids:
                    try:
                        # Tenta consultar a base de conhecimento usando o método search
                        vector_db = self.chroma_wrapper(collection_name=f"kb_{kb_id}")
                        if vector_db.has_data():
                            # Usa o método search que retorna objetos Document
                            documents = vector_db.search(query=query, limit=n_results)
                            if documents:
                                for i, doc in enumerate(documents):
                                    all_results.append({
                                        'role': 'system',
                                        'content': f"Conteúdo da base de conhecimento '{kb_id}': {doc.content}",
                                        'metadata': {
                                            'kb_id': kb_id,
                                            'relevance_score': i,  # Ordenado por relevância (menor índice = mais relevante)
                                            'source': 'knowledge_base'
                                        }
                                    })
                                print(f"[INFO] Base de conhecimento '{kb_id}': {len(documents)} documentos encontrados")
                            else:
                                print(f"[INFO] Base de conhecimento '{kb_id}': nenhum documento relevante encontrado")
                        else:
                            print(f"[INFO] Base de conhecimento '{kb_id}': coleção vazia")
                    except Exception as e:
                        print(f"[WARN] Erro ao consultar base de conhecimento {kb_id}: {e}")
                        continue
            
            # Consulta anexos da sessão se session_id for fornecido
            if session_id:
                try:
                    session_collection_name = f"chat_session_{session_id}"
                    vector_db = self.chroma_wrapper(collection_name=session_collection_name)
                    if vector_db.has_data():
                        # Usa o método search que retorna objetos Document
                        documents = vector_db.search(query=query, limit=n_results)
                        if documents:
                            for i, doc in enumerate(documents):
                                all_results.append({
                                    'role': 'system',
                                    'content': f"Conteúdo do documento anexado à sessão: {doc.content}",
                                    'metadata': {
                                        'session_id': session_id,
                                        'relevance_score': i,
                                        'source': 'session_attachment'
                                    }
                                })
                            print(f"[INFO] Anexos da sessão {session_id}: {len(documents)} documentos encontrados")
                        else:
                            print(f"[INFO] Anexos da sessão {session_id}: nenhum documento relevante encontrado")
                    else:
                        print(f"[INFO] Anexos da sessão {session_id}: coleção vazia ou não existe")
                except Exception as e:
                    print(f"[WARN] Erro ao consultar anexos da sessão {session_id}: {e}")
            
            # Ordena por relevância (menor índice = mais relevante)
            all_results.sort(key=lambda x: x['metadata']['relevance_score'])
            print(f"[INFO] Total de resultados encontrados: {len(all_results)}")
            return all_results[:n_results]  # Retorna os mais relevantes
            
        except Exception as e:
            print(f"[ERROR] Erro ao consultar bases de conhecimento: {e}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return []


class IntegratedMemorySystem:
    """Sistema integrado de memória (MongoDB + ChromaDB + PostgreSQL)"""
    
    def __init__(self, db: Database, uid: str, pg_pool: Pool):
        self.db = db
        self.uid = uid
        self.pg_pool = pg_pool
        self.token_tracker = PostgreSQLTokenTracker(pg_pool)
        self.vector_memory = ChromaDBVectorMemory()
        self.chat_collection = db["memory_chat"]
        self.summaries_collection = db["chat_summaries"]
        
        # Cache de contexto
        self._context_cache = {}
        self._cache_timeout = 300  # 5 minutos
    
    async def add_message(self, session_id: str, role: str, content: str, model_id: str = "deepseek-chat", tokens_used: Dict[str, int] = None):
        """Adiciona mensagem ao sistema de memória"""
        try:
            # Salva no MongoDB
            message_doc = {
                "session_id": session_id,
                "uid": self.uid,
                "role": role,
                "content": content,
                "model_id": model_id,
                "tokens_used": tokens_used or {},
                "timestamp": datetime.now(timezone.utc)
            }
            self.chat_collection.insert_one(message_doc)
            
            # Adiciona à memória vetorial
            if role in ["user", "assistant"]:
                self.vector_memory.add_memory(
                    uid=self.uid,
                    session_id=session_id,
                    content=content,
                    metadata={"role": role, "model": model_id}
                )
            
            # Registra tokens
            if tokens_used and role == "assistant":
                await self.token_tracker.track_tokens(
                    uid=self.uid,
                    model=model_id,
                    session_id=session_id,
                    input_tokens=tokens_used.get('input', 0),
                    output_tokens=tokens_used.get('output', 0)
                )
            
            # Limpa cache
            self._clear_context_cache(session_id)
            
        except Exception as e:
            logger.error(f"Erro ao adicionar mensagem: {e}")
    
    def get_context_messages(self, session_id: str, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Obtém mensagens de contexto com cache"""
        cache_key = f"{session_id}_{limit}"
        current_time = time.time()
        
        # Verifica cache
        if cache_key in self._context_cache:
            cached_data, timestamp = self._context_cache[cache_key]
            if current_time - timestamp < self._cache_timeout:
                return cached_data
        
        try:
            context_messages = []
            
            # Obtém memórias vetoriais relevantes se houver query
            if query:
                vector_memories = self.vector_memory.query_memories(self.uid, query, n_results=3)
                context_messages.extend(vector_memories)
            
            # Obtém mensagens recentes da sessão
            recent_messages = list(
                self.chat_collection.find({"session_id": session_id})
                .sort("timestamp", -1)
                .limit(limit)
            )
            
            # Formata mensagens
            for msg in reversed(recent_messages):
                context_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Atualiza cache
            self._context_cache[cache_key] = (context_messages, current_time)
            
            return context_messages
            
        except Exception as e:
            logger.error(f"Erro ao obter contexto: {e}")
            return []
    
    def _clear_context_cache(self, session_id: str):
        """Limpa cache de contexto específico"""
        keys_to_remove = [key for key in self._context_cache.keys() if key.startswith(session_id)]
        for key in keys_to_remove:
            del self._context_cache[key]

class IntelligentCache:
    """Cache inteligente otimizado"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache: Dict[str, Dict] = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def _generate_key(self, data: Any) -> str:
        return hashlib.md5(str(data).encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            item = self.cache[key]
            if time.time() - item['timestamp'] < self.ttl:
                return item['data']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, data: Any):
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
        
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }

class MaestroOrchestrator:
    """
    MAESTRO ORCHESTRATOR - Versão Integrada
    Orquestrador principal com LLM real e memória avançada
    """
    
    def __init__(self, db: Database, pg_pool: Pool, provider_config: Dict[str, Any] = None):
        self.db = db
        self.pg_pool = pg_pool
        self.llm = DynamicLLM(provider_config)
        self.cache = IntelligentCache()
        self.execution_history: List[TaskResult] = []
        
        # Importar AgentConfigLoader para carregar configurações personalizadas
        from .agent_config_loader import AgentConfigLoader
        self.agent_config_loader = AgentConfigLoader()
        
        # Configurações padrão dos agentes especializados (fallback)
        self.default_agent_configs = {
            AgentType.GENERAL: AgentConfig(
                agent_id="general_001",
                agent_type=AgentType.GENERAL,
                personality="Assistente versátil e eficiente, seu nome é Saphi",
                temperature=0.7,
                max_tokens=2000,
                tools=["web_search", "calculator"],
                knowledge_bases=["general_kb"],
                specialization="Tarefas gerais e consultas básicas",
                system_prompt="Você é um assistente inteligente e versátil. Responda de forma clara, útil e precisa. Não mencione qual modelo de LLM você está usando a menos que seja especificamente perguntado."
            ),
            AgentType.ANALYST: AgentConfig(
                agent_id="analyst_001",
                agent_type=AgentType.ANALYST,
                personality="Analista detalhista e metodológico",
                temperature=0.3,
                max_tokens=4000,
                tools=["data_analysis", "statistics", "charts"],
                knowledge_bases=["business_kb", "data_kb"],
                specialization="Análise de dados e relatórios",
                system_prompt="Você é um analista especializado. Forneça análises detalhadas, estruturadas e baseadas em dados. Use metodologias analíticas apropriadas."
            ),
            AgentType.CREATIVE: AgentConfig(
                agent_id="creative_001",
                agent_type=AgentType.CREATIVE,
                personality="Criativo e inspirador",
                temperature=0.9,
                max_tokens=3000,
                tools=["image_gen", "content_creation"],
                knowledge_bases=["creative_kb", "marketing_kb"],
                specialization="Conteúdo criativo e marketing",
                system_prompt="Você é um especialista em criatividade e marketing. Crie conteúdo original, envolvente e inovador. Pense fora da caixa."
            ),
            AgentType.TECHNICAL: AgentConfig(
                agent_id="technical_001",
                agent_type=AgentType.TECHNICAL,
                personality="Especialista técnico preciso",
                temperature=0.2,
                max_tokens=5000,
                tools=["code_executor", "api_caller", "database_query"],
                knowledge_bases=["tech_kb", "api_kb"],
                specialization="Desenvolvimento e soluções técnicas",
                system_prompt="Você é um especialista técnico. Forneça soluções precisas, código funcional e explicações técnicas detalhadas."
            ),
            AgentType.RESEARCH: AgentConfig(
                agent_id="research_001",
                agent_type=AgentType.RESEARCH,
                personality="Pesquisador meticuloso",
                temperature=0.4,
                max_tokens=4000,
                tools=["web_search", "academic_search", "fact_checker"],
                knowledge_bases=["research_kb", "academic_kb"],
                specialization="Pesquisa e verificação de informações",
                system_prompt="Você é um pesquisador especializado. Forneça informações precisas, bem fundamentadas e cite fontes quando apropriado."
            ),
            AgentType.PROBLEM_SOLVER: AgentConfig(
                agent_id="solver_001",
                agent_type=AgentType.PROBLEM_SOLVER,
                personality="Solucionador estratégico",
                temperature=0.5,
                max_tokens=3500,
                tools=["logic_engine", "decision_tree", "optimization"],
                knowledge_bases=["strategy_kb", "solutions_kb"],
                specialization="Resolução de problemas complexos",
                system_prompt="Você é um especialista em resolução de problemas. Analise sistematicamente, identifique soluções práticas e forneça planos de ação claros."
            )
        }
        
        # Cache para configurações de agentes personalizados
        self._agent_config_cache = {}
    
    async def orchestrate(self, user_prompt: str, uid: str, session_id: str, context: Dict = None, knowledge_bases: List[str] = None, agent_id: str = None) -> Dict[str, Any]:
        """Método principal de orquestração com LLM real e suporte a agentes personalizados"""
        start_time = time.time()
        task_id = self._generate_task_id(user_prompt)
        
        logger.info(f"Iniciando orquestração para task: {task_id}, agente: {agent_id}")
        
        try:
            # Inicializa sistema de memória
            memory_system = IntegratedMemorySystem(self.db, uid, self.pg_pool)
            
            # Adiciona mensagem do usuário
            await memory_system.add_message(session_id, "user", user_prompt)
            
            # Análise da tarefa
            analysis = await self._analyze_prompt(user_prompt, context)

            # Gera plano de execução com bases de conhecimento dinâmicas
            execution_plan = await self._generate_execution_plan(analysis, knowledge_bases, agent_id)
            
            # Obtém contexto da conversa
            context_messages = memory_system.get_context_messages(session_id, user_prompt, limit=15)
            
            # Executa baseado na complexidade
            if execution_plan.complexity == TaskComplexity.SIMPLE:
                result = await self._execute_simple_task(execution_plan, user_prompt, context_messages, agent_id)
            elif execution_plan.complexity == TaskComplexity.MEDIUM:
                result = await self._execute_planned_task(execution_plan, user_prompt, context_messages, agent_id)
            else:
                result = await self._execute_team_orchestration(execution_plan, user_prompt, context_messages, agent_id)
            
            # Adiciona resposta à memória
            await memory_system.add_message(
                session_id,
                "assistant",
                result['content'],
                tokens_used=result.get('tokens_used', {})
            )
            
            execution_time = time.time() - start_time
            
            # Registra resultado
            task_result = TaskResult(
                task_id=task_id,
                success=result['success'],
                result=result['content'],
                execution_time=execution_time,
                agent_used=str(execution_plan.required_agents),
                tokens_used=result.get('tokens_used', {}),
                metadata={
                    'complexity': execution_plan.complexity.value,
                    'steps_executed': len(execution_plan.steps),
                    'tools_used': execution_plan.tools_needed,
                    'knowledge_bases_used': execution_plan.kb_sources,
                    'agent_id': agent_id
                }
            )
            self.execution_history.append(task_result)
            
            logger.info(f"Orquestração concluída em {execution_time:.2f}s")
            logger.info(f"Bases de conhecimento utilizadas: {execution_plan.kb_sources}")
            logger.info(f"Agente utilizado: {agent_id}")
            
            return {
                'success': True,
                'task_id': task_id,
                'result': result['content'],
                'execution_time': execution_time,
                'tokens_used': result.get('tokens_used', {}),
                'metadata': task_result.metadata
            }
            
        except Exception as e:
            logger.error(f"Erro na orquestração: {str(e)}")
            return {
                'success': False,
                'task_id': task_id,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    async def _analyze_prompt(self, prompt: str, context: Dict = None) -> Dict[str, Any]:
        """Análise inteligente do prompt usando cache"""
        
        cache_key = self.cache._generate_key(f"analysis_{prompt}")
        cached_analysis = self.cache.get(cache_key)
        if cached_analysis:
            logger.info("Análise recuperada do cache")
            return cached_analysis
        
        # Palavras-chave para classificação
        keywords = {
            'creative': ['criar', 'gerar', 'design', 'arte', 'criativo', 'campanha', 'logo', 'visual'],
            'technical': ['código', 'programar', 'api', 'sistema', 'desenvolver', 'implementar'],
            'analytical': ['analisar', 'dados', 'relatório', 'estatística', 'métricas', 'gráficos'],
            'research': ['pesquisar', 'estudar', 'investigar', 'informações', 'fontes'],
            'problem_solving': ['resolver', 'problema', 'solução', 'estratégia', 'otimizar']
        }
        
        complexity_indicators = {
            'medium': ['relatório', 'análise', 'criar', 'desenvolver', 'plano'],
            'complex': ['completa', 'detalhada', 'cronograma', 'integração', 'arquitetura'],
            'expert': ['framework', 'metodologia avançada', 'machine learning', 'blockchain']
        }
        
        prompt_lower = prompt.lower()
        word_count = len(prompt.split())
        
        # Determina complexidade
        complexity = TaskComplexity.SIMPLE
        
        if word_count >= 100:
            complexity = TaskComplexity.EXPERT
        elif word_count >= 30:
            complexity = TaskComplexity.COMPLEX
        elif word_count >= 10:
            complexity = TaskComplexity.MEDIUM
        
        # Ajusta por palavras-chave semânticas
        for level, indicators in complexity_indicators.items():
            if any(indicator in prompt_lower for indicator in indicators):
                if level == 'expert':
                    complexity = TaskComplexity.EXPERT
                    break
                elif level == 'complex' and complexity.value in ['simple', 'medium']:
                    complexity = TaskComplexity.COMPLEX
                elif level == 'medium' and complexity == TaskComplexity.SIMPLE:
                    complexity = TaskComplexity.MEDIUM
        
        # Determina agentes necessários
        required_agents = [AgentType.GENERAL]
        
        for category, words in keywords.items():
            if any(word in prompt_lower for word in words):
                if category == 'creative' and AgentType.CREATIVE not in required_agents:
                    required_agents.append(AgentType.CREATIVE)
                elif category == 'technical' and AgentType.TECHNICAL not in required_agents:
                    required_agents.append(AgentType.TECHNICAL)
                elif category == 'analytical' and AgentType.ANALYST not in required_agents:
                    required_agents.append(AgentType.ANALYST)
                elif category == 'research' and AgentType.RESEARCH not in required_agents:
                    required_agents.append(AgentType.RESEARCH)
                elif category == 'problem_solving' and AgentType.PROBLEM_SOLVER not in required_agents:
                    required_agents.append(AgentType.PROBLEM_SOLVER)
        
        analysis = {
            'prompt': prompt,
            'complexity': complexity,
            'required_agents': required_agents,
            'estimated_tokens': word_count * 3,
            'context_available': context is not None,
            'priority': self._calculate_priority(prompt, complexity)
        }
        
        self.cache.set(cache_key, analysis)
        return analysis
    
    async def _get_agent_config(self, agent_type: AgentType, agent_id: str = None) -> AgentConfig:
        """Obtém configuração do agente, priorizando configurações personalizadas do MongoDB"""
        cache_key = f"{agent_type.value}_{agent_id}"
        
        # Verifica cache
        if cache_key in self._agent_config_cache:
            return self._agent_config_cache[cache_key]
        
        # Tenta carregar configuração personalizada se agent_id for fornecido
        if agent_id and agent_id != "maestro":
            try:
                agent_config = self.agent_config_loader.load_agent_config(agent_id)
                if agent_config:
                    # Constrói o system prompt personalizado
                    system_prompt = self.agent_config_loader.build_agent_system_prompt(agent_config)
                    
                    # Converte para AgentConfig do Maestro
                    config = AgentConfig(
                        agent_id=agent_id,
                        agent_type=agent_type,
                        personality=agent_config.get('personalityInstructions', ''),
                        temperature=agent_config.get('temperature', 0.7),
                        max_tokens=agent_config.get('maxTokens', 2000),
                        tools=agent_config.get('tools', []),
                        knowledge_bases=agent_config.get('knowledgeBase', []),
                        specialization=agent_config.get('roleDefinition', ''),
                        system_prompt=system_prompt
                    )
                    self._agent_config_cache[cache_key] = config
                    logger.info(f"Configuração personalizada carregada para agente: {agent_id}")
                    logger.info(f"System prompt personalizado criado: {len(system_prompt)} caracteres")
                    return config
            except Exception as e:
                logger.warning(f"Erro ao carregar configuração personalizada para {agent_id}: {e}")
        
        # Fallback para configuração padrão
        if agent_type in self.default_agent_configs:
            config = self.default_agent_configs[agent_type]
            self._agent_config_cache[cache_key] = config
            return config
        
        # Fallback final para agente geral
        return self.default_agent_configs[AgentType.GENERAL]
    
    async def _generate_execution_plan(self, analysis: Dict[str, Any], knowledge_bases: List[str] = None, agent_id: str = None) -> ExecutionPlan:
        """Gera plano detalhado de execução com bases de conhecimento dinâmicas e suporte a agentes personalizados"""
        
        complexity = analysis['complexity']
        required_agents = analysis['required_agents']
        
        # Determina ferramentas
        tools_needed = []
        kb_sources = []
        
        # Usa bases de conhecimento dinâmicas se fornecidas, senão usa as padrões dos agentes
        if knowledge_bases:
            kb_sources = knowledge_bases
        else:
            for agent_type in required_agents:
                config = await self._get_agent_config(agent_type, agent_id)
                tools_needed.extend(config.tools)
                kb_sources.extend(config.knowledge_bases)
        
        tools_needed = list(set(tools_needed))
        kb_sources = list(set(kb_sources))
        
        # Gera steps
        steps = self._generate_execution_steps(complexity, required_agents)
        
        # Estima tempo
        base_time = 2.0
        complexity_multiplier = {
            TaskComplexity.SIMPLE: 1,
            TaskComplexity.MEDIUM: 2,
            TaskComplexity.COMPLEX: 4,
            TaskComplexity.EXPERT: 8
        }
        
        estimated_time = base_time * complexity_multiplier[complexity] * len(required_agents)
        
        return ExecutionPlan(
            task_id=self._generate_task_id(analysis['prompt']),
            complexity=complexity,
            required_agents=required_agents,
            tools_needed=tools_needed,
            kb_sources=kb_sources,
            steps=steps,
            estimated_time=estimated_time,
            priority=analysis['priority']
        )
    
    def _generate_execution_steps(self, complexity: TaskComplexity, agents: List[AgentType]) -> List[Dict[str, Any]]:
        """Gera steps baseados na complexidade"""
        
        if complexity == TaskComplexity.SIMPLE:
            return [{"step": 1, "action": "execute_direct", "agent": agents[0].value}]
        elif complexity == TaskComplexity.MEDIUM:
            return [
                {"step": 1, "action": "prepare_context", "agent": "orchestrator"},
                {"step": 2, "action": "execute_planned", "agent": agents[0].value},
                {"step": 3, "action": "validate_result", "agent": "orchestrator"}
            ]
        else:
            return [
                {"step": 1, "action": "analyze_requirements", "agent": "orchestrator"},
                {"step": 2, "action": "instantiate_specialists", "agent": "orchestrator"},
                {"step": 3, "action": "parallel_execution", "agent": "team"},
                {"step": 4, "action": "consolidate_results", "agent": "orchestrator"}
            ]
    
    async def _execute_simple_task(self, plan: ExecutionPlan, prompt: str, context_messages: List[Dict[str, Any]], agent_id: str = None) -> Dict[str, Any]:
        """Execução de tarefa simples com LLM real e consulta a bases de conhecimento"""
        
        logger.info("Executando tarefa simples")
        
        agent_type = plan.required_agents[0]
        config = await self._get_agent_config(agent_type, agent_id)
        
        # Prepara mensagens para o LLM
        messages = [{"role": "system", "content": config.system_prompt}]
        
        # Consulta bases de conhecimento se disponíveis
        if plan.kb_sources:
            kb_system = KnowledgeBaseQuerySystem()
            kb_results = kb_system.query_knowledge_bases(plan.kb_sources, prompt, n_results=3)
            if kb_results:
                messages.extend(kb_results)
                logger.info(f"Adicionadas {len(kb_results)} consultas de bases de conhecimento")
        
        # Adiciona contexto se disponível
        if context_messages:
            messages.extend(context_messages[-5:])  # Últimas 5 mensagens
        
        # Adiciona prompt do usuário
        messages.append({"role": "user", "content": prompt})
        
        # Gera resposta real usando DeepSeek
        response = self.llm.generate_response(
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        
        return response
    
    async def _execute_planned_task(self, plan: ExecutionPlan, prompt: str, context_messages: List[Dict[str, Any]], agent_id: str = None) -> Dict[str, Any]:
        """Execução de tarefa planejada com múltiplos steps e consulta a bases de conhecimento"""
        
        logger.info("Executando tarefa planejada")
        
        agent_type = plan.required_agents[0]
        config = await self._get_agent_config(agent_type, agent_id)
        
        # Step 1: Análise dos requisitos
        analysis_messages = [
            {"role": "system", "content": f"{config.system_prompt}\n\nPrimeiro, analise os requisitos da tarefa e identifique os pontos principais."},
            {"role": "user", "content": f"Analise esta tarefa: {prompt}"}
        ]
        
        # Consulta bases de conhecimento para análise
        if plan.kb_sources:
            kb_system = KnowledgeBaseQuerySystem()
            kb_results = kb_system.query_knowledge_bases(plan.kb_sources, prompt, n_results=2)
            if kb_results:
                analysis_messages.extend(kb_results)
        
        analysis_response = self.llm.generate_response(
            messages=analysis_messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        # Step 2: Execução principal com contexto
        main_messages = [{"role": "system", "content": config.system_prompt}]
        
        # Consulta bases de conhecimento para execução principal
        if plan.kb_sources:
            kb_system = KnowledgeBaseQuerySystem()
            kb_results = kb_system.query_knowledge_bases(plan.kb_sources, prompt, n_results=3)
            if kb_results:
                main_messages.extend(kb_results)
        
        # Adiciona contexto
        if context_messages:
            main_messages.extend(context_messages[-8:])
        
        # Adiciona análise anterior
        main_messages.append({"role": "assistant", "content": f"Análise dos requisitos: {analysis_response['content']}"})
        
        # Adiciona tarefa principal
        main_messages.append({"role": "user", "content": f"Baseado na análise anterior, execute: {prompt}"})
        
        # Gera resposta final
        final_response = self.llm.generate_response(
            messages=main_messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        
        # Combina tokens usados
        combined_tokens = {
            'input': analysis_response['tokens_used']['input'] + final_response['tokens_used']['input'],
            'output': analysis_response['tokens_used']['output'] + final_response['tokens_used']['output'],
            'total': analysis_response['tokens_used']['total'] + final_response['tokens_used']['total']
        }
        
        return {
            'content': final_response['content'],
            'tokens_used': combined_tokens,
            'success': final_response['success'],
            'model': final_response['model'],
            'analysis': analysis_response['content']
        }
    
    async def _execute_team_orchestration(self, plan: ExecutionPlan, prompt: str, context_messages: List[Dict[str, Any]], agent_id: str = None) -> Dict[str, Any]:
        """Execução com orquestração de equipe usando LLMs reais e bases de conhecimento"""
        
        logger.info("Executando orquestração de equipe")
        
        # Executa especialistas em paralelo
        specialist_tasks = []
        for agent_type in plan.required_agents:
            task = self._execute_specialist_real(agent_type, prompt, context_messages, plan.kb_sources, agent_id)
            specialist_tasks.append(task)
        
        # Aguarda todas as execuções
        specialist_results = await asyncio.gather(*specialist_tasks, return_exceptions=True)
        
        # Filtra resultados bem-sucedidos
        successful_results = [r for r in specialist_results if isinstance(r, dict) and r.get('success', False)]
        
        if not successful_results:
            return {
                'content': 'Erro: Nenhum especialista conseguiu executar a tarefa.',
                'tokens_used': {'input': 0, 'output': 0, 'total': 0},
                'success': False,
                'model': 'deepseek-chat'
            }
        
        # Consolida resultados usando LLM
        consolidation_response = await self._consolidate_team_results_real(successful_results, prompt)
        
        return consolidation_response
    
    async def _execute_specialist_real(self, agent_type: AgentType, prompt: str, context_messages: List[Dict[str, Any]], knowledge_bases: List[str] = None, agent_id: str = None) -> Dict[str, Any]:
        """Executa especialista real usando DeepSeek com consulta a bases de conhecimento"""
        
        config = await self._get_agent_config(agent_type, agent_id)
        
        # Prepara mensagens especializadas
        messages = [{"role": "system", "content": config.system_prompt}]
        
        # Consulta bases de conhecimento se disponíveis
        if knowledge_bases:
            kb_system = KnowledgeBaseQuerySystem()
            kb_results = kb_system.query_knowledge_bases(knowledge_bases, prompt, n_results=2)
            if kb_results:
                messages.extend(kb_results)
                logger.info(f"Especialista {agent_type.value} usando {len(kb_results)} consultas de bases de conhecimento")
        
        # Adiciona contexto relevante
        if context_messages:
            messages.extend(context_messages[-5:])
        
        # Instrução específica para o especialista
        specialist_instruction = f"""
        Como {config.specialization.lower()}, responda à seguinte tarefa usando sua expertise:
        
        Tarefa: {prompt}
        
        Forneça uma resposta especializada na sua área de conhecimento.
        """
        
        messages.append({"role": "user", "content": specialist_instruction})
        
        # Gera resposta
        response = self.llm.generate_response(
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        
        # Adiciona metadados do especialista
        if response['success']:
            response['specialist_type'] = agent_type.value
            response['specialization'] = config.specialization
        
        return response
    
    async def _consolidate_team_results_real(self, results: List[Dict[str, Any]], original_prompt: str) -> Dict[str, Any]:
        """Consolida resultados da equipe usando LLM real"""
        
        # Prepara prompt de consolidação
        consolidation_prompt = f"""
        Você é um coordenador que deve consolidar as respostas de diferentes especialistas em uma resposta única e coerente.

        Tarefa original: {original_prompt}

        Respostas dos especialistas:
        """
        
        total_input_tokens = 0
        total_output_tokens = 0
        
        for i, result in enumerate(results, 1):
            specialist_type = result.get('specialist_type', f'especialista_{i}')
            content = result.get('content', '')
            tokens = result.get('tokens_used', {})
            
            total_input_tokens += tokens.get('input', 0)
            total_output_tokens += tokens.get('output', 0)
            
            consolidation_prompt += f"""
            
            {i}. {specialist_type.upper()}:
            {content}
            """
        
        consolidation_prompt += """
        
        Sua tarefa é:
        1. Analisar todas as respostas dos especialistas
        2. Identificar os pontos principais e complementares
        3. Criar uma resposta única, coerente e completa
        4. Manter a qualidade e profundidade das respostas originais
        5. Estruturar de forma clara e organizada
        
        Resposta consolidada:
        """
        
        # Gera consolidação
        consolidation_messages = [
            {"role": "system", "content": "Você é um coordenador especialista em consolidar informações de múltiplas fontes em uma resposta clara e completa."},
            {"role": "user", "content": consolidation_prompt}
        ]
        
        consolidation_response = self.llm.generate_response(
            messages=consolidation_messages,
            temperature=0.5,
            max_tokens=4000
        )
        
        # Combina tokens de todos os especialistas + consolidação
        if consolidation_response['success']:
            consolidation_response['tokens_used'] = {
                'input': total_input_tokens + consolidation_response['tokens_used']['input'],
                'output': total_output_tokens + consolidation_response['tokens_used']['output'],
                'total': total_input_tokens + total_output_tokens + consolidation_response['tokens_used']['total']
            }
            consolidation_response['specialists_count'] = len(results)
        
        return consolidation_response
    
    def _generate_task_id(self, prompt: str) -> str:
        """Gera ID único para a tarefa"""
        return f"task_{int(time.time())}_{hash(prompt) % 10000}"
    
    def _calculate_priority(self, prompt: str, complexity: TaskComplexity) -> int:
        """Calcula prioridade da tarefa"""
        urgency_words = ['urgente', 'rápido', 'imediato', 'agora', 'hoje']
        has_urgency = any(word in prompt.lower() for word in urgency_words)
        
        base_priority = {
            TaskComplexity.SIMPLE: 1,
            TaskComplexity.MEDIUM: 2,
            TaskComplexity.COMPLEX: 3,
            TaskComplexity.EXPERT: 4
        }
        
        return base_priority[complexity] + (2 if has_urgency else 0)
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de execução"""
        if not self.execution_history:
            return {'message': 'Nenhuma execução realizada ainda'}
        
        successful = sum(1 for task in self.execution_history if task.success)
        total = len(self.execution_history)
        avg_time = sum(task.execution_time for task in self.execution_history) / total
        total_tokens = sum(task.tokens_used.get('total', 0) for task in self.execution_history)
        
        return {
            'total_executions': total,
            'successful_executions': successful,
            'success_rate': successful / total,
            'average_execution_time': avg_time,
            'total_tokens_used': total_tokens,
            'cache_size': len(self.cache.cache)
        }

class DatabaseManager:
    """Gerenciador de conexões de banco"""
    
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.pg_pool = None
    
    async def initialize(self):
        """Inicializa conexões com os bancos"""
        try:
            # MongoDB
            self.mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.mongo_client.admin.command('ping')
            self.mongo_db = self.mongo_client[os.getenv("MONGO_DB_NAME", "saphien")]
            logger.info("MongoDB conectado")
            
            # PostgreSQL
            pg_url = POSTGRES_URL.replace("postgresql+asyncpg://", "postgres://")
            self.pg_pool = await asyncpg.create_pool(
                dsn=pg_url, 
                min_size=1, 
                max_size=10, 
                command_timeout=60
            )
            logger.info("PostgreSQL conectado")
            
            # Inicializa tabelas
            token_tracker = PostgreSQLTokenTracker(self.pg_pool)
            await token_tracker.initialize_tables()
            
        except Exception as e:
            logger.error(f"Erro na inicialização dos bancos: {e}")
            raise
    
    async def close(self):
        """Fecha conexões"""
        try:
            if self.pg_pool:
                await self.pg_pool.close()
            if self.mongo_client:
                self.mongo_client.close()
            logger.info("Conexões de banco fechadas")
        except Exception as e:
            logger.error(f"Erro ao fechar conexões: {e}")

class ExecutionContextManager:
    """Gerenciador de contexto de execução"""
    
    def __init__(self, db: Database):
        self.db = db
        self.chat_sessions = db["chat_sessions"]
        self.user_id = None
        self.session_id = None
    
    def initialize_context(self, user_id: str, session_id: str = None):
        """Inicializa contexto da sessão"""
        self.user_id = user_id
        
        if session_id:
            # Verifica se sessão existe
            session = self.chat_sessions.find_one({
                "_id": session_id,
                "user_id": user_id
            })
            if session:
                self.session_id = session_id
                logger.info(f"Sessão encontrada: {session_id}")
                return
        
        # Busca sessão mais recente
        latest_session = self.chat_sessions.find_one(
            {"user_id": user_id},
            sort=[("last_updated", -1)]
        )
        
        if latest_session:
            self.session_id = str(latest_session["_id"])
            logger.info(f"Usando sessão mais recente: {self.session_id}")
        else:
            # Cria nova sessão
            self.session_id = self._create_new_session()
    
    def _create_new_session(self) -> str:
        """Cria nova sessão"""
        session_doc = {
            "_id": str(uuid4()),
            "user_id": self.user_id,
            "title": f"Nova Sessão - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "created_at": datetime.now(timezone.utc),
            "last_updated": datetime.now(timezone.utc)
        }
        
        self.chat_sessions.insert_one(session_doc)
        session_id = session_doc["_id"]
        logger.info(f"Nova sessão criada: {session_id}")
        return session_id

# Função principal de demonstração
async def main():
    """Demonstração do Maestro Orchestrator integrado"""
    
    if len(sys.argv) < 3:
        print("Uso: python maestro.py <user_id> \"<mensagem>\" [session_id]")
        return
    
    user_id = sys.argv[1]
    user_prompt = sys.argv[2]
    session_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    print("="*80)
    print("MAESTRO AI ORCHESTRATOR - VERSÃO INTEGRADA")
    print("="*80)
    
    db_manager = None
    
    try:
        # Inicializa bancos de dados
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        # Configura contexto
        context_manager = ExecutionContextManager(db_manager.mongo_db)
        context_manager.initialize_context(user_id, session_id)
        
        # Inicializa orquestrador
        maestro = MaestroOrchestrator(db_manager.mongo_db, db_manager.pg_pool)
        
        print(f"\nUsuário: {context_manager.user_id}")
        print(f"Sessão: {context_manager.session_id}")
        print(f"Prompt: {user_prompt}")
        print("\n" + "-"*50)
        
        # Executa orquestração
        result = await maestro.orchestrate(
            user_prompt=user_prompt,
            uid=context_manager.user_id,
            session_id=context_manager.session_id
        )
        
        if result['success']:
            print(f"\n✅ RESPOSTA (Tempo: {result['execution_time']:.2f}s)")
            print(f"Tokens utilizados: {result.get('tokens_used', {})}")
            print(f"\n{result['result']}")
            
            # Estatísticas
            stats = maestro.get_execution_stats()
            print(f"\n📊 ESTATÍSTICAS:")
            print(f"- Execuções totais: {stats['total_executions']}")
            print(f"- Taxa de sucesso: {stats['success_rate']:.2%}")
            print(f"- Tokens totais: {stats['total_tokens_used']}")
            
        else:
            print(f"\n❌ ERRO: {result['error']}")
        
    except Exception as e:
        logger.error(f"Erro na execução principal: {e}", exc_info=True)
        print(f"Erro: {e}")
    
    finally:
        if db_manager:
            await db_manager.close()


# Função pública para uso via backend
def run_maestro_agent(user_id: str, prompt: str, session_id: str = None, knowledge_bases: List[str] = None, agent_id: str = None, provider_config: Dict[str, Any] = None) -> str:
    """
    Executa o Maestro Orchestrator e retorna a resposta do assistente.
    
    :param user_id: ID do usuário
    :param prompt: Mensagem do usuário
    :param session_id: ID da sessão (opcional)
    :param knowledge_bases: Lista de IDs de bases de conhecimento (opcional)
    :param agent_id: ID do agente personalizado (opcional)
    :param provider_config: Configuração do provedor LLM (opcional)
    :return: Resposta do Maestro Orchestrator
    """
    async def _runner():
        db_manager = None
        try:
            # Inicializa bancos
            db_manager = DatabaseManager()
            await db_manager.initialize()

            # Configura contexto
            context_manager = ExecutionContextManager(db_manager.mongo_db)
            context_manager.initialize_context(user_id, session_id)

            # Inicializa orquestrador com configuração do provedor
            maestro = MaestroOrchestrator(db_manager.mongo_db, db_manager.pg_pool, provider_config)

            # Executa orquestração com bases de conhecimento e agente personalizado
            result = await maestro.orchestrate(
                user_prompt=prompt,
                uid=context_manager.user_id,
                session_id=context_manager.session_id,
                knowledge_bases=knowledge_bases,
                agent_id=agent_id
            )

            if result["success"]:
                return str(result["result"]).strip()
            else:
                return f"[ERRO] {result.get('error', 'Falha desconhecida no Maestro')}"
        except Exception as e:
            return f"[MAESTRO ERRO] {e}"
        finally:
            if db_manager:
                await db_manager.close()

    return asyncio.run(_runner())


# Função compatível com o serviço Agno
async def run_maestro_task(user_id: str, user_prompt: str, session_id: str = None, knowledge_bases: List[str] = None, agent_id: str = None, provider_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Função compatível com o serviço Agno que executa o Maestro Orchestrator.
    
    :param user_id: ID do usuário
    :param user_prompt: Mensagem do usuário
    :param session_id: ID da sessão (opcional)
    :param knowledge_bases: Lista de IDs de bases de conhecimento (opcional)
    :param agent_id: ID do agente personalizado (opcional)
    :param provider_config: Configuração do provedor LLM (opcional)
    :return: Dicionário com resultado da execução
    """
    db_manager = None
    try:
        # Inicializa bancos
        db_manager = DatabaseManager()
        await db_manager.initialize()

        # Configura contexto
        context_manager = ExecutionContextManager(db_manager.mongo_db)
        context_manager.initialize_context(user_id, session_id)

        # Inicializa orquestrador com configuração do provedor
        maestro = MaestroOrchestrator(db_manager.mongo_db, db_manager.pg_pool, provider_config)

        # Executa orquestração com bases de conhecimento e agente personalizado
        result = await maestro.orchestrate(
            user_prompt=user_prompt,
            uid=context_manager.user_id,
            session_id=context_manager.session_id,
            knowledge_bases=knowledge_bases,
            agent_id=agent_id
        )

        return result
    except Exception as e:
        logger.error(f"Erro em run_maestro_task: {e}")
        return {
            'success': False,
            'error': str(e),
            'execution_time': 0
        }
    finally:
        if db_manager:
            await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())