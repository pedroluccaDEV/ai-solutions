#!/usr/bin/env python3
"""
Teste do Agent Builder simulando uma request real da API
Execute dentro de: features/chat/
"""

import asyncio
import sys
from pathlib import Path
import pprint

# -----------------------------------------------------------------------------
# Setup de path (simples e direto)
# -----------------------------------------------------------------------------

CURRENT_DIR = Path(__file__).parent.absolute()
SERVER_ROOT = CURRENT_DIR.parent.parent

sys.path.insert(0, str(SERVER_ROOT))

# -----------------------------------------------------------------------------
# Import do builder
# -----------------------------------------------------------------------------

from features.chat.agent_builder import build_agent_from_request

# -----------------------------------------------------------------------------
# TESTE PRINCIPAL
# -----------------------------------------------------------------------------

async def test_build_agent_from_api_request():
    print("\n🧪 TESTE: build_agent_from_request (simulação de API)")
    print("=" * 80)

    # Payload exatamente como viria da API
    request_data = {
        "agent_id": "6936e3cf35eb8d6b17150e6b",
        "user_id": "pQTwXbRfVEPvp1K8QrH38BGAduA2",
        "message": "Estou testando o serviço de cobrança...",
        "agent_overrides": {
            "model": "5",               # override vazio → NÃO deve quebrar
            "tools": [],
            "mcps": [],
            "knowledgeBase": []
        }
    }

    print("📨 Payload da request:")
    pprint.pprint(request_data, indent=2)

    # -------------------------------------------------------------------------
    # Execução
    # -------------------------------------------------------------------------

    result = await build_agent_from_request(request_data)

    print("\n📦 RESULTADO FINAL DO BUILDER")
    print("=" * 80)

    agent = result.get("agent", {})
    resources = result.get("resources", {})
    context = result.get("context", {})

    print("\n🤖 AGENTE FINAL:")
    pprint.pprint(agent, indent=2)

    # -------------------------------------------------------------------------
    # Validações críticas (o motivo real do teste)
    # -------------------------------------------------------------------------

    print("\n🔍 VALIDAÇÕES CRÍTICAS")
    print("-" * 80)

    model_id = agent.get("model")

    if not model_id:
        raise AssertionError(
            "❌ ERRO CRÍTICO: model está vazio no agente final.\n"
            "Billing e execução irão falhar."
        )

    print(f"✅ Model definido corretamente: {model_id}")

    print(f"✅ Tools carregadas: {len(resources.get('tools', []))}")
    print(f"✅ MCPs carregados: {len(resources.get('mcps', []))}")
    print(f"✅ KnowledgeBases carregadas: {len(resources.get('knowledgeBase', []))}")

    print(f"✅ Memória ativa: {context.get('has_memory', False)}")
    print(f"✅ Histórico: {len(context.get('conversation_history', []))} mensagens")

    print("\n🎉 TESTE PASSOU — AGENTE PRONTO PARA EXECUÇÃO E BILLING")
    print("=" * 80)

# -----------------------------------------------------------------------------
# ENTRYPOINT
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(test_build_agent_from_api_request())
