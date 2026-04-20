# features/chat/executor_agent.py
import os
import asyncio
import traceback
from typing import Optional, List, AsyncGenerator, Dict, Any
from datetime import datetime
import tiktoken
import importlib
from dotenv import load_dotenv

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.tools.mcp import MultiMCPTools

from features.agent.fetch_data import fetch_agent_resources
from dao.mongo.v1.tool_config_dao import ToolConfigDAO

try:
    from features.tests.agents.agent_knowledge.chroma_client_wrapper import ChromaDbWrapper
except ImportError:
    ChromaDbWrapper = None

load_dotenv()

# =====================================================
# FUNÇÕES AUXILIARES - CONTAGEM DE TOKENS
# =====================================================

def _count_tokens(text: str, model: str = "gpt-4") -> int:
    """Conta tokens no texto usando tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback para encoding cl100k_base
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            # Estimativa simples como último recurso
            return len(text.split()) * 1.3


def _extract_token_usage_from_response(response) -> Dict[str, int]:
    """Extrai uso de tokens da resposta do modelo."""
    token_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    
    try:
        # Tenta extrair de diferentes formatos de resposta
        if hasattr(response, 'usage'):
            usage = response.usage
            if hasattr(usage, 'prompt_tokens'):
                token_usage["input_tokens"] = usage.prompt_tokens
            if hasattr(usage, 'completion_tokens'):
                token_usage["output_tokens"] = usage.completion_tokens
            if hasattr(usage, 'total_tokens'):
                token_usage["total_tokens"] = usage.total_tokens
                
        # Se não encontrou, tenta calcular
        if token_usage["total_tokens"] == 0:
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    output_text = choice.message.content
                    token_usage["output_tokens"] = _count_tokens(output_text)
                    
    except Exception as e:
        print(f"[TOKENS] Erro ao extrair uso de tokens: {e}")
    
    return token_usage


def _emit_token_event(input_tokens: int, output_tokens: int, stage: str, model_used: str = None) -> Dict[str, Any]:
    """Cria evento de uso de tokens."""
    return {
        "type": "token_usage",
        "data": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "stage": stage,
            "timestamp": datetime.now().isoformat(),
            "model_used": model_used
        }
    }


# =====================================================
# FUNÇÕES AUXILIARES - DEBUG MODEL CONFIG
# =====================================================

def _debug_model_config(model_config: Dict[str, Any]):
    """Debug detalhado da configuração do modelo"""
    print(f"\n{'='*60}")
    print(f"🔍 DEBUG MODEL CONFIG")
    print(f"{'='*60}")
    
    if not model_config:
        print("❌ model_config é None")
        return
    
    print(f"Model Name: {model_config.get('model_name', 'N/A')}")
    print(f"Model Type: {model_config.get('model_type', 'N/A')}")
    print(f"Max Tokens: {model_config.get('max_tokens', 'N/A')}")
    
    provider = model_config.get('provider', {})
    print(f"\nProvider Info:")
    print(f"  • Name: {provider.get('name', 'N/A')}")
    print(f"  • Module: {provider.get('module_path', 'N/A')}")
    print(f"  • Class: {provider.get('class_name', 'N/A')}")
    print(f"  • Config Key: {provider.get('config_key', 'N/A')}")
    
    # Verificar se a chave existe no ambiente
    config_key = provider.get('config_key')
    if config_key and config_key != "NONE":
        env_value = os.getenv(config_key)
        if env_value:
            masked = '*' * 8 + env_value[-4:] if len(env_value) > 4 else '********'
            print(f"  • Env Value: {masked} (presente)")
        else:
            print(f"  • Env Value: ❌ NÃO ENCONTRADO")
    
    print(f"{'='*60}")


# =====================================================
# FUNÇÃO PRINCIPAL - LOAD LLM FROM BUILDER MODEL
# =====================================================

def load_llm_from_builder_model(model_config: Dict[str, Any]):
    """
    Instancia dinamicamente um modelo Agno a partir do contrato do builder.
    Totalmente genérico e compatível com qualquer provider.
    """
    if not model_config:
        raise RuntimeError("Model config não fornecido pelo builder")

    provider = model_config.get("provider")
    if not provider:
        raise RuntimeError("Provider ausente no model_config")

    module_path = provider.get("module_path")
    class_name = provider.get("class_name")
    config_key = provider.get("config_key")
    base_url = provider.get("api_base_url")
    model_name = model_config.get("model_name")

    if not module_path or not class_name:
        raise RuntimeError("module_path ou class_name ausente no provider")

    if not model_name:
        raise RuntimeError("model_name ausente no model_config")

    print(f"\n[LLM LOADER] Instanciando LLM")
    print(f"  • Provider: {provider.get('name')}")
    print(f"  • Module: {module_path}")
    print(f"  • Class: {class_name}")
    print(f"  • Model ID: {model_name}")

    # Import dinâmico
    try:
        module = importlib.import_module(module_path)
        ProviderClass = getattr(module, class_name)
    except Exception as e:
        raise RuntimeError(f"Erro ao importar {module_path}.{class_name}: {e}")

    # kwargs mínimos e corretos segundo Agno
    kwargs = {
        "id": model_name
    }

    # API key (se existir)
    if config_key and config_key != "NONE":
        api_key = os.getenv(config_key)
        if not api_key:
            raise RuntimeError(f"API key não encontrada no env: {config_key}")
        kwargs["api_key"] = api_key

    # Base URL (opcional, só se o provider suportar)
    if base_url:
        kwargs["base_url"] = base_url

    print(f"[LLM LOADER] Parâmetros finais:")
    for k, v in kwargs.items():
        if k == "api_key":
            print(f"  • {k}: ********{v[-4:]}")
        else:
            print(f"  • {k}: {v}")

    try:
        instance = ProviderClass(**kwargs)
        print(f"  ✅ LLM instanciado com sucesso")
        return instance
    except Exception as e:
        raise RuntimeError(
            f"Falha ao instanciar {class_name} com kwargs {list(kwargs.keys())}: {e}"
        )
        
# =====================================================
# FUNÇÕES AUXILIARES - MEMÓRIA
# =====================================================

def build_context_with_memory(conversation_history: List[Dict], max_messages: int = 8) -> str:
    """Constrói contexto a partir do histórico da memória."""
    if not conversation_history or len(conversation_history) < 2:
        return ""
    
    recent_messages = conversation_history[-max_messages:-1] if len(conversation_history) > max_messages else conversation_history[:-1]
    
    if not recent_messages:
        return ""
    
    context_lines = ["## 📜 Histórico da Conversa:"]
    
    for msg in recent_messages:
        sender = msg.get("sender", "unknown")
        content = msg.get("content", "")
        message_number = msg.get("message_number", 0)
        
        role = "👤 USUÁRIO" if sender == "user" else "🤖 ASSISTENTE"
        content_preview = content[:150] + "..." if len(content) > 150 else content
        
        context_lines.append(f"\n{role} (Mensagem #{message_number}):")
        context_lines.append(f"{content_preview}")
    
    context_lines.append(f"\n📊 Total de mensagens no histórico: {len(conversation_history)}")
    
    return "\n".join(context_lines)


def build_system_prompt_with_memory(
    agent_data: Dict[str, Any],
    planner_response: str,
    conversation_history: List[Dict],
    session_id: Optional[str] = None
) -> str:
    """Constrói o prompt do sistema considerando o contexto da memória."""
    
    # Base do prompt do agente
    role_definition = agent_data.get("roleDefinition", "")
    goal = agent_data.get("goal", "")
    rules = agent_data.get("agentRules", "")
    
    context = ""
    if role_definition:
        context += f"**Seu Papel:**\n{role_definition}\n\n"
    if goal:
        context += f"**Seu Objetivo:**\n{goal}\n\n"
    if rules:
        context += f"**Suas Regras:**\n{rules}\n\n"
    
    # Adicionar contexto da memória se houver histórico
    if conversation_history:
        memory_context = build_context_with_memory(conversation_history)
        context += f"{memory_context}\n\n"
        context += "**IMPORTANTE - Você está em uma conversa contínua:**\n"
        context += "- Considere o histórico acima para fornecer respostas contextuais\n"
        context += "- Evite repetir informações já fornecidas\n"
        context += "- Referencie conversas anteriores quando relevante\n"
        context += "- Mantenha consistência com a conversa\n\n"
    
    # Adicionar informações da sessão se disponível
    if session_id:
        context += f"**ID da Sessão:** {session_id}\n\n"
    
    # Adicionar instruções do planner
    context += f"**Instruções do Planner:**\n{planner_response}"
    
    return context


# =====================================================
# FUNÇÕES AUXILIARES - RECURSOS
# =====================================================

def init_knowledge_base_hybrid(collection_name: str, enable_hybrid: bool = True) -> Optional[Knowledge]:
    """Inicializa a knowledge base."""
    if not collection_name or not ChromaDbWrapper:
        return None

    try:
        print(f"[KB] Inicializando coleção: {collection_name}")
        vector_db = ChromaDbWrapper(
            collection_name=collection_name,
            enable_hybrid_search=enable_hybrid,
            min_similarity_threshold=0.05
        )

        if not vector_db.has_data():
            print(f"[AVISO] Coleção '{collection_name}' está vazia")
            return None

        # ✅ CORREÇÃO: Removido embedding_model (agora é acessado via vector_db.embedder)
        return Knowledge(vector_db=vector_db)
    except Exception as e:
        print(f"[ERRO] Erro ao inicializar KB: {e}")
        return None


async def init_mcp_tools(mcp_data: List[dict]) -> Optional[List[MultiMCPTools]]:
    """Inicializa conexões MCP."""
    if not mcp_data:
        print("[MCP] Nenhuma conexão MCP disponível")
        return None

    active_connections = []
    for mcp in mcp_data:
        name = mcp.get("server_name", "Unknown")
        connection_url = mcp.get("connection")
        transport = mcp.get("transport")

        if not connection_url or not transport:
            print(f"[AVISO] [MCP] Dados incompletos para {name}")
            continue

        try:
            print(f"[MCP] Conectando a {name} via {transport}...")
            tool = MultiMCPTools(urls=[connection_url], urls_transports=[transport])
            await tool.connect()
            active_connections.append(tool)
            print(f"[OK] [MCP] Conectado com sucesso a {name}")
        except Exception as e:
            print(f"[ERRO] [MCP] Falha ao conectar {name}: {e}")

    if not active_connections:
        print("[AVISO] [MCP] Nenhuma conexão MCP ativa")
        return None

    print(f"[OK] [MCP] Total de conexões ativas: {len(active_connections)}")
    return active_connections


def get_user_tool_config(user_id: str) -> Dict[str, Any]:
    """Obtém configuração de ferramentas do usuário."""
    try:
        doc = ToolConfigDAO.get_dict_by_user_id(user_id)
        if not doc:
            print(f"[AVISO] Nenhum tool_config encontrado para user {user_id}")
            return {}
        config = doc.get("config", {})
        print(f"[OK] {len(config)} tools configuradas para user {user_id}")
        return config
    except Exception as e:
        print(f"[ERRO] Erro ao buscar tool_config: {e}")
        return {}


def build_tool_instances(tools_data: list, user_tool_config: Dict[str, Any]) -> List:
    """Constrói instâncias de ferramentas."""
    import importlib
    instances = []

    for tool in tools_data:
        if not isinstance(tool, dict):
            continue
            
        name = tool.get("name", "Unknown")
        module_path = tool.get("module_path", "")
        class_name = tool.get("class_name", "")
        
        if not module_path or not class_name:
            print(f"[AVISO] Tool '{name}' sem module_path ou class_name")
            continue
        
        # Verifica se a tool está ativa e configurada
        if not tool.get("active", True):
            print(f"[AVISO] Tool '{name}' desativada")
            continue
        
        # Verifica configuração do usuário
        config_enabled = False
        user_config = tool.get("user_config", {})
        if user_config:
            for tool_key, config in user_config.items():
                if config.get("enabled", False):
                    config_enabled = True
                    break
        
        if tool.get("requires_auth", False) and not config_enabled:
            print(f"[AVISO] Tool '{name}' requer auth mas não configurada")
            continue
        
        try:
            # Importa e instancia a ferramenta
            module = importlib.import_module(module_path)
            tool_class = getattr(module, class_name)
            
            # Prepara parâmetros
            kwargs = {}
            tool_param = tool.get("tool_param", {})
            if tool_param and isinstance(tool_param, dict):
                kwargs.update(tool_param)
            
            # Aplica API key se disponível
            api_key = tool.get("api_key")
            if api_key and tool.get("requires_auth", False):
                # Tenta determinar o nome do parâmetro
                param_name = "api_key"
                if "api_key" not in kwargs:
                    kwargs[param_name] = api_key
            
            # Instancia a ferramenta
            if kwargs:
                instance = tool_class(**kwargs)
            else:
                instance = tool_class()
            
            instances.append(instance)
            print(f"[OK] Tool '{name}' instanciada")
            
        except ImportError as e:
            print(f"[ERRO] Não foi possível importar {module_path}.{class_name}: {e}")
            continue
        except Exception as e:
            print(f"[ERRO] Falha ao instanciar {name}: {e}")
            continue

    return instances


# =====================================================
# FUNÇÃO AUXILIAR - ARQUIVOS
# =====================================================

def extract_files_context(files_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Extrai contexto dos arquivos interpretados.
    Formato esperado (do FileInterpretationEngine):
    {
        "text_blocks": [{"content": "...", "metadata": {...}}],
        "combined_context": "texto combinado...",
        "table_blocks": [...],
        "metadata": {...}
    }
    """
    if not files_data:
        return ""

    try:
        # Formato direto do FileInterpretationEngine
        combined_context = files_data.get("combined_context", "")
        if combined_context:
            print(f"[FILES] combined_context encontrado: {len(combined_context)} chars")
            return f"\n\n**📁 Conteúdo dos Arquivos:**\n{combined_context}"

        # Fallback: monta a partir dos text_blocks
        text_blocks = files_data.get("text_blocks", [])
        if text_blocks:
            print(f"[FILES] Montando contexto de {len(text_blocks)} text_block(s)")
            contexts = []
            for block in text_blocks:
                content = block.get("content", "")
                metadata = block.get("metadata", {})
                filename = metadata.get("filename", "arquivo")

                if len(content) > 8000:
                    content = content[:7997] + "..."

                contexts.append(f"📄 **{filename}**:\n{content}")

            if contexts:
                return f"\n\n**📁 Conteúdo dos Arquivos:**\n\n" + "\n\n---\n\n".join(contexts)

        # Formato legado: lista de arquivos sem interpretação
        files_list = files_data.get("files", [])
        if files_list:
            print(f"[FILES] Formato legado: {len(files_list)} arquivo(s) sem texto extraído")
            descriptions = []
            for f in files_list:
                if isinstance(f, dict):
                    filename = f.get("filename", f.get("name", "arquivo"))
                    size = f.get("size", len(f.get("bytes", b"")))
                    descriptions.append(f"📄 {filename} ({size} bytes)")
            if descriptions:
                return f"\n\n**📁 Arquivos Anexados (sem texto extraído):**\n" + "\n".join(descriptions)

        print(f"[FILES] ⚠️ files_data sem conteúdo utilizável. Keys: {list(files_data.keys())}")

    except Exception as e:
        print(f"[FILES] Erro ao extrair contexto: {e}")

    return ""
# =====================================================
# EXECUTOR STREAMING - OTIMIZADO COM TOKEN TRACKING
# =====================================================

async def run_executor_streaming(
    agent_id: str,
    prompt: Any,
    user_id: str,
    original_keywords: Optional[str] = None,
    proper_nouns: Optional[List[str]] = None,
    resources: Optional[Dict[str, Any]] = None,
    resources_analyzed: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[Dict[str, Any], None]:

    full_response = ""
    chunks_received = 0

    total_input_tokens = 0
    total_output_tokens = 0

    model_used = None
    actual_model_used = None

    try:
        print(f"\n{'='*60}")
        print(f"[EXECUTOR STREAMING] Iniciando execução para agente {agent_id}")
        print(f"{'='*60}")

        # =================== CONTEXTO / MEMÓRIA ===================
        session_id = None
        conversation_history = []

        if resources and "context" in resources:
            context = resources.get("context", {})
            session_id = context.get("session_id")
            conversation_history = context.get("conversation_history", [])

            print("[MEMORY] Contexto recebido:")
            print(f"  • Sessão: {session_id or 'Nenhuma'}")
            print(f"  • Histórico: {len(conversation_history)} mensagens")

        # =================== RECURSOS ===================
        if resources:
            print("[EXECUTOR] Usando recursos fornecidos")
            agent_data = resources.get("agent", {})
            tool_data = resources.get("tools", [])
            mcp_data = resources.get("mcps", [])
            knowledge_data = resources.get("knowledge_bases", [])
            builder_model = resources.get("builder_model")
        else:
            print("[EXECUTOR] Buscando recursos do agente...")
            fetched = fetch_agent_resources(agent_id, user_id)
            agent_data = fetched.get("agent", {})
            tool_data = fetched.get("tools", [])
            mcp_data = fetched.get("mcps", [])
            knowledge_data = fetched.get("knowledge_bases", [])
            builder_model = None

        if not builder_model:
            # Tentar fallback: buscar model_data do nível raiz se disponível
            if resources and "model_data" in resources:
                builder_model = resources.get("model_data")
                print("[EXECUTOR] Usando model_data do nível raiz como fallback")
            
            if not builder_model:
                raise RuntimeError("builder_model não fornecido pelo builder")
        
        # DEBUG: Mostrar configuração do modelo
        _debug_model_config(builder_model)
        
        # Verificar capacidades do modelo
        capabilities = builder_model.get("capabilities", [])
        if "chat" not in capabilities:
            print(f"[AVISO] Modelo não tem capacidade 'chat' listada, continuando...")
            # Não bloqueia, apenas avisa
        
        actual_model_used = builder_model.get("model_name")
        model_used = actual_model_used

        # =================== KNOWLEDGE BASE ===================
        knowledge = None
        if knowledge_data:
            collection = knowledge_data[0].get("vector_collection_name")
            if collection:
                knowledge = init_knowledge_base_hybrid(collection)
                print(f"[KB] Knowledge base inicializada: {collection}")

        # =================== TOOLS ===================
        user_tool_config = get_user_tool_config(user_id)
        mcp_tools = await init_mcp_tools(mcp_data)
        tool_instances = build_tool_instances(tool_data, user_tool_config)

        all_tools = tool_instances + (mcp_tools or [])
        print(f"[TOOLS] Total de ferramentas disponíveis: {len(all_tools)}")

        # =================== METADATA ===================
        yield {
            "type": "metadata",
            "metadata": {
                "agent_id": agent_id,
                "model_used": model_used,
                "model_source": "builder",
                "tools_count": len(all_tools),
                "mcp_connections": len(mcp_tools) if mcp_tools else 0,
                "used_knowledge_base": bool(knowledge),
                "memory_context": {
                    "session_id": session_id,
                    "has_history": bool(conversation_history),
                    "history_count": len(conversation_history)
                },
                "builder_model_info": {
                    "provider": builder_model.get("provider", {}).get("name"),
                    "capabilities": capabilities
                }
            },
            "complete": False
        }

        # =================== PROMPT ===================
        base_prompt = build_system_prompt_with_memory(
            agent_data=agent_data,
            planner_response=prompt,
            conversation_history=conversation_history,
            session_id=session_id
        )

        files_context = ""
        if resources and "files" in resources:
            files_context = extract_files_context(resources.get("files"))
            print(f"[FILES] Contexto de arquivos extraído: {len(files_context)} caracteres")

        final_prompt = base_prompt + files_context

        total_input_tokens = _count_tokens(final_prompt)
        print(f"[PROMPT] Tokens de entrada: {total_input_tokens}")

        yield _emit_token_event(
            input_tokens=total_input_tokens,
            output_tokens=0,
            stage="prompt_input",
            model_used=model_used
        )

        # =================== LLM ===================
        print(f"\n{'='*60}")
        print(f"[EXECUTOR] Instanciando modelo LLM...")
        print(f"{'='*60}")
        
        model = load_llm_from_builder_model(builder_model)

        print(f"\n[EXECUTOR] Modelo instanciado: {actual_model_used}")
        print(f"[EXECUTOR] Provider: {builder_model['provider']['name']}")
        print(f"[EXECUTOR] Iniciando execução do agente...")

        # ✅ CORREÇÃO: Removido 'search_knowledge' e outros parâmetros obsoletos
        agent = Agent(
            model=model,
            tools=all_tools,
            knowledge=knowledge,
            description=agent_data.get("description", "Agente Executor"),
            markdown=True,
            debug_mode=False
        )

        # NÃO use await aqui! O método arun com stream=True retorna um async generator
        stream = agent.arun(final_prompt, stream=True)

        accumulated_response = ""
        output_token_batch = 0
        batch_size = 50

        print(f"\n[EXECUTOR] Streaming resposta...")
        
        async for chunk in stream:
            if hasattr(chunk, "content") and chunk.content:
                chunks_received += 1
                content = chunk.content

                full_response += content
                accumulated_response += content

                output_tokens = _count_tokens(accumulated_response)

                if output_tokens - output_token_batch >= batch_size:
                    new_tokens = output_tokens - output_token_batch
                    total_output_tokens += new_tokens
                    output_token_batch = output_tokens

                    yield _emit_token_event(
                        input_tokens=0,
                        output_tokens=new_tokens,
                        stage="streaming_output",
                        model_used=model_used
                    )

                yield {
                    "type": "chunk",
                    "content": content,
                    "chunk_number": chunks_received,
                    "model_used": model_used,
                    "complete": False
                }

        # Finalizar contagem de tokens
        remaining_tokens = _count_tokens(accumulated_response) - output_token_batch
        if remaining_tokens > 0:
            total_output_tokens += remaining_tokens
            yield _emit_token_event(
                input_tokens=0,
                output_tokens=remaining_tokens,
                stage="final_output",
                model_used=model_used
            )

        # Token summary final
        yield _emit_token_event(
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            stage="total_summary",
            model_used=model_used
        )

        print(f"\n{'='*60}")
        print(f"[EXECUTOR] Execução completada!")
        print(f"  • Chunks recebidos: {chunks_received}")
        print(f"  • Tokens entrada: {total_input_tokens}")
        print(f"  • Tokens saída: {total_output_tokens}")
        print(f"  • Modelo usado: {actual_model_used}")
        print(f"{'='*60}")

        yield {
            "type": "complete",
            "content": full_response,
            "total_chunks": chunks_received,
            "model_used": model_used,
            "model_actual": actual_model_used,
            "model_source": "builder",
            "tokens_used": {
                "input": total_input_tokens,
                "output": total_output_tokens,
                "total": total_input_tokens + total_output_tokens
            },
            "complete": True,
            "memory_context": {
                "session_id": session_id,
                "has_history": bool(conversation_history),
                "history_count": len(conversation_history)
            }
        }

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"[EXECUTOR] ERRO na execução:")
        print(f"  • Erro: {e}")
        print(f"  • Modelo: {model_used}")
        print(f"  • Tokens usados: {total_input_tokens} in, {total_output_tokens} out")
        print(f"{'='*60}")
        traceback.print_exc()

        yield {
            "type": "error",
            "stage": "executor",
            "error": str(e),
            "partial_response": full_response or None,
            "model_used": model_used,
            "tokens_used": {
                "input": total_input_tokens,
                "output": total_output_tokens,
                "total": total_input_tokens + total_output_tokens
            },
            "complete": True
        }


# =====================================================
# EXECUTOR SEM STREAMING (com tracking de tokens básico)
# =====================================================

async def run_executor(
    agent_id: str, 
    prompt: Any, 
    user_id: str,
    original_keywords: Optional[str] = None,
    proper_nouns: Optional[List[str]] = None,
    resources: Optional[Dict[str, Any]] = None
) -> str:
    """Versão sem streaming do executor com tracking básico de tokens."""
    response = ""
    model_used = None
    
    # Extrair modelo dos recursos
    if resources and "builder_model" in resources:
        builder_model = resources.get("builder_model")
        model_used = builder_model.get("model_name", "unknown")
        print(f"[EXECUTOR-NO-STREAM] Modelo recebido: {model_used}")
    
    # Acumuladores de tokens
    total_input_tokens = 0
    total_output_tokens = 0
    
    try:
        # Contar tokens de entrada
        final_prompt = prompt if isinstance(prompt, str) else str(prompt)
        input_tokens = _count_tokens(final_prompt)
        total_input_tokens = input_tokens
        
        print(f"[EXECUTOR-NO-STREAM] Executando...")
        print(f"  • Tokens entrada: {input_tokens}")
        print(f"  • Modelo: {model_used}")
        
        async for event in run_executor_streaming(
            agent_id, prompt, user_id, original_keywords, proper_nouns, resources
        ):
            if event["type"] == "chunk":
                response += event["content"]
            elif event["type"] == "token_usage":
                # Acumular tokens se o evento for de token_usage
                token_data = event.get("data", {})
                total_input_tokens += token_data.get("input_tokens", 0)
                total_output_tokens += token_data.get("output_tokens", 0)
            elif event["type"] == "complete":
                # Log do modelo e tokens usados
                tokens_info = event.get("tokens_used", {})
                print(f"[EXECUTOR-NO-STREAM] Execução concluída!")
                print(f"  • Modelo: {model_used}")
                print(f"  • Tokens: Input={tokens_info.get('input', 0)}, Output={tokens_info.get('output', 0)}")
                print(f"  • Resposta: {len(response)} caracteres")
                return response
            elif event["type"] == "error":
                error_msg = event.get("error", "Unknown error")
                tokens_used = event.get("tokens_used", {})
                model_info = f" (Modelo: {model_used})" if model_used else ""
                tokens_info = f" [Tokens: I={tokens_used.get('input', 0)}, O={tokens_used.get('output', 0)}]" if tokens_used else ""
                return f"Erro no executor{model_info}{tokens_info}: {error_msg}"
    
    except Exception as e:
        print(f"[EXECUTOR-NO-STREAM] ERRO: {e}")
        model_info = f" (Modelo: {model_used})" if model_used else ""
        tokens_info = f" [Tokens usados: I={total_input_tokens}, O={total_output_tokens}]"
        return f"Erro no executor{model_info}{tokens_info}: {str(e)}"
    
    return response