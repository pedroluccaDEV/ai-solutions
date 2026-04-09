import re
import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from features.tests.agents.agent_knowledge.chroma_client_wrapper import ChromaDbWrapper

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("A variável de ambiente OPENAI_API_KEY não foi definida.")

def limpar_ansi(texto: str) -> str:
    ansi_regex = r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])'
    return re.sub(ansi_regex, '', texto)

async def executar_base_conhecimento(collection_id: str, prompt_usuario: str) -> str:
    try:
        # Modelo
        model = OpenAIChat(
            id="gpt-3.5-turbo",
            api_key=OPENAI_API_KEY
        )

        # Agente 1 - Planejador
        agente_planejador = Agent(
            model=model,
            knowledge=None,
            search_knowledge=False,
            add_references=False,
            description=(
                "Você é um planejador técnico especializado em preparar instruções para geração de conteúdo "
                "com base em uma base vetorial interna. Sua tarefa é transformar solicitações do usuário em prompts "
                "altamente específicos para outro agente."
            ),
            instructions=(
                "Elabore um plano estruturado que contenha: objetivo da tarefa, tópicos para busca na base vetorial, "
                "tipo de conteúdo esperado e o prompt final para o agente executor."
            ),
            markdown=True,
            debug_mode=False
        )

        plano = await agente_planejador.arun(prompt_usuario)
        prompt_refinado = plano.content if hasattr(plano, "content") else plano

        # Agente 2 - Executor
        vector_db = ChromaDbWrapper(collection_name=collection_id)
        knowledge = Knowledge(
            vector_db=vector_db,
            embedding_model=vector_db.embedder
        )

        agente_executor = Agent(
            model=model,
            knowledge=knowledge,
            search_knowledge=True,
            add_references=True,
            description=(
                "Você é um assistente técnico que gera respostas precisas usando exclusivamente a base vetorial como fonte."
            ),
            instructions=(
                "Responda ao prompt com o máximo de profundidade e formato Markdown. Avise se base insuficiente."
            ),
            markdown=True,
            debug_mode=False
        )

        resposta = await agente_executor.arun(prompt_refinado)
        resposta_texto = resposta.content if hasattr(resposta, "content") else resposta
        resposta_limpa = limpar_ansi(resposta_texto).strip()

        return resposta_limpa or "⚠️ Nenhuma resposta encontrada."

    except Exception as e:
        return f"❌ Erro durante execução da base de conhecimento: {e}"
