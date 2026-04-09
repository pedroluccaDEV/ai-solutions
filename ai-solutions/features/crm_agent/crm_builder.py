# features/crm/crm_builder.py
"""
CRM Builder — define e instancia o agente Agno de forma fixa.

Responsabilidade única: montar o Agent do Agno com modelo,
system prompt e configurações corretas para o contexto de CRM.

Não é dinâmico por design — simplicidade intencional.
"""

import os
from typing import Optional
from dotenv import load_dotenv 

from agno.agent import Agent
from agno.models.openai import OpenAIResponses  # troque pelo provider desejado

load_dotenv()

# =====================================================
# CONFIGURAÇÃO FIXA DO MODELO
# (quando vier a versão dinâmica, só trocar aqui)
# =====================================================

CRM_MODEL_ID = os.getenv("CRM_MODEL_ID", "gpt-4o-mini")
CRM_MODEL_API_KEY = os.getenv("OPENAI_API_KEY")

# =====================================================
# SYSTEM PROMPT DO AGENTE CRM
# =====================================================

CRM_SYSTEM_PROMPT = """
Você é um agente especialista em CRM e vendas. Seu papel é analisar 
interações com leads e tomar decisões inteligentes.

VOCÊ NUNCA:
- Responde só com texto simples
- Improvisa ações sem base no contexto
- Inventa dados sobre o lead

VOCÊ SEMPRE:
- Analisa a intenção real do lead
- Gera uma resposta adequada ao tom e estágio
- Define ações concretas e justificadas
- Retorna um JSON estruturado e válido

FORMATO DE SAÍDA OBRIGATÓRIO (JSON puro, sem markdown):
{
  "analysis": {
    "intent": "<compra|duvida|reclamacao|abandono|neutro>",
    "confidence": <0.0 a 1.0>,
    "priority": "<high|medium|low>",
    "stage": "<novo|engajado|qualificado|perdido>",
    "reasoning": "<explicação curta da decisão>"
  },
  "response": {
    "message": "<mensagem para enviar ao lead>",
    "tone": "<friendly|professional|urgent|empathetic>"
  },
  "actions": [
    {
      "type": "<send_message|update_status|notify_team>",
      "payload": {}
    }
  ],
  "metadata": {
    "model": "MODEL_PLACEHOLDER",
    "processing_note": "<observação técnica opcional>"
  }
}

Regra de ouro: o campo "actions" nunca pode ser vazio.
Sempre haverá ao menos um "send_message".
""".replace("MODEL_PLACEHOLDER", CRM_MODEL_ID)


# =====================================================
# BUILDER — monta e retorna o Agent Agno
# =====================================================

def build_crm_agent() -> Agent:
    """
    Instancia e retorna o Agent Agno configurado para CRM.
    
    Fixo por enquanto — quando vier a versão dinâmica,
    receberá model_config como parâmetro.
    """
    if not CRM_MODEL_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY não encontrada no ambiente. "
            "Configure a variável antes de usar o agente CRM."
        )

    model = OpenAIResponses(
        id=CRM_MODEL_ID,
        api_key=CRM_MODEL_API_KEY,
    )

    agent = Agent(
        model=model,
        description=CRM_SYSTEM_PROMPT,
        markdown=False,   # queremos JSON puro, sem formatação
        debug_mode=False,
    )

    print(f"[CRM BUILDER] Agente instanciado — modelo: {CRM_MODEL_ID}")
    return agent


def get_model_info() -> dict:
    """Retorna info do modelo atual (útil para metadata do output)."""
    return {
        "model_id": CRM_MODEL_ID,
        "provider": "openai",
        "fixed": True,
    }