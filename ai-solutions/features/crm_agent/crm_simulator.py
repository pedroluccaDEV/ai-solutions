# features/crm/crm_simulator.py
"""
CRM Simulator — simula chamadas de API REST para testar o agente.

Como usar:
    python crm_simulator.py
    python crm_simulator.py --case buy      # só o caso de compra
    python crm_simulator.py --case all      # todos os casos
    python crm_simulator.py --pretty        # output formatado

Futuramente este arquivo será substituído pelo endpoint real da API.
"""

import asyncio
import json
import argparse
from datetime import datetime
from typing import Dict, Any

from crm_agent import run_crm_agent


# =====================================================
# CASOS DE TESTE — simulam payloads da API REST
# =====================================================

TEST_CASES: Dict[str, Dict[str, Any]] = {

    "buy": {
        "_description": "Lead interessado em comprar — primeira vez",
        "lead": {
            "id":      "lead_001",
            "name":    "João Silva",
            "message": "Quero saber o preço do plano profissional",
            "status":  "new",
            "source":  "landing_page",
        },
        "history": [],
        "context": {
            "company": "TechSolutions",
            "product": "Sistema de Gestão Pro",
            "tone":    "comercial",
        },
        "constraints": {
            "max_tokens":     400,
            "response_style": "short",
        },
    },

    "doubt": {
        "_description": "Lead com dúvida técnica — já interagiu antes",
        "lead": {
            "id":      "lead_002",
            "name":    "Maria Souza",
            "message": "Como funciona a integração com o meu sistema atual?",
            "status":  "engaged",
            "source":  "whatsapp",
        },
        "history": [
            {"sender": "lead",  "content": "Vi o produto na feira e me interessei"},
            {"sender": "agent", "content": "Que ótimo! Posso te enviar mais informações?"},
            {"sender": "lead",  "content": "Sim, pode enviar"},
        ],
        "context": {
            "company": "TechSolutions",
            "product": "Sistema de Gestão Pro",
            "tone":    "tecnico",
        },
        "constraints": {
            "max_tokens":     500,
            "response_style": "balanced",
        },
    },

    "complaint": {
        "_description": "Lead reclamando de problema — alta prioridade",
        "lead": {
            "id":      "lead_003",
            "name":    "Carlos Mendes",
            "message": "O sistema travou de novo e perdi dados importantes. Isso é inaceitável.",
            "status":  "engaged",
            "source":  "email",
        },
        "history": [
            {"sender": "lead",  "content": "O sistema está lento hoje"},
            {"sender": "agent", "content": "Já acionamos o suporte técnico"},
            {"sender": "lead",  "content": "Ninguém me retornou ainda"},
        ],
        "context": {
            "company": "TechSolutions",
            "product": "Sistema de Gestão Pro",
            "tone":    "suporte",
        },
        "constraints": {
            "max_tokens":     600,
            "response_style": "detailed",
        },
    },

    "abandon": {
        "_description": "Lead querendo cancelar",
        "lead": {
            "id":      "lead_004",
            "name":    "Ana Lima",
            "message": "Não preciso mais do produto. Pode cancelar.",
            "status":  "qualified",
            "source":  "whatsapp",
        },
        "history": [
            {"sender": "lead",  "content": "Assinei o plano anual mês passado"},
            {"sender": "agent", "content": "Ótimo! Como está sendo a experiência?"},
            {"sender": "lead",  "content": "Não estou usando muito"},
        ],
        "context": {
            "company": "TechSolutions",
            "product": "Sistema de Gestão Pro",
            "tone":    "comercial",
        },
        "constraints": {
            "max_tokens":     500,
            "response_style": "balanced",
        },
    },

}


# =====================================================
# FUNÇÕES DE OUTPUT
# =====================================================

def _print_separator(char: str = "=", width: int = 60):
    print(char * width)


def _print_result(case_name: str, description: str, result: Dict, pretty: bool = False):
    """Imprime o resultado de forma legível."""
    _print_separator()
    print(f"CASO: {case_name.upper()}")
    print(f"Descrição: {description}")
    _print_separator("-")

    analysis = result.get("analysis", {})
    response = result.get("response", {})
    actions  = result.get("actions", [])
    metadata = result.get("metadata", {})

    print(f"\n📊 ANÁLISE:")
    print(f"  Intent:     {analysis.get('intent')} (confiança: {analysis.get('confidence', 0):.0%})")
    print(f"  Priority:   {analysis.get('priority')}")
    print(f"  Stage:      {analysis.get('stage')}")
    print(f"  Reasoning:  {analysis.get('reasoning')}")

    print(f"\n💬 RESPOSTA AO LEAD:")
    print(f"  Tom: {response.get('tone')}")
    print(f"  Mensagem: \"{response.get('message')}\"")

    print(f"\n⚙️  AÇÕES:")
    for action in actions:
        payload_str = json.dumps(action.get("payload", {}), ensure_ascii=False)
        print(f"  [{action.get('type')}] {payload_str}")

    print(f"\n🔧 METADATA:")
    print(f"  Modelo:   {metadata.get('model')}")
    print(f"  Tempo:    {metadata.get('total_time_ms')}ms")

    if pretty:
        print(f"\n📄 JSON COMPLETO:")
        # Remove _meta do output exibido
        clean = {k: v for k, v in result.items() if k != "_meta"}
        print(json.dumps(clean, ensure_ascii=False, indent=2))

    _print_separator()
    print()


def _print_error(case_name: str, error: Exception):
    _print_separator("!")
    print(f"❌ ERRO no caso '{case_name}': {type(error).__name__}: {error}")
    _print_separator("!")
    print()


# =====================================================
# RUNNER DOS TESTES
# =====================================================

async def run_single_case(case_name: str, pretty: bool = False):
    """Executa um único caso de teste."""
    if case_name not in TEST_CASES:
        print(f"Caso '{case_name}' não encontrado. Disponíveis: {list(TEST_CASES.keys())}")
        return

    case = TEST_CASES[case_name]
    description = case.pop("_description", "")

    print(f"\n🚀 Executando caso: {case_name}")
    started = datetime.utcnow()

    try:
        result = await run_crm_agent(case)
        _print_result(case_name, description, result, pretty)
    except Exception as e:
        _print_error(case_name, e)
    finally:
        case["_description"] = description  # restaura para próximas execuções


async def run_all_cases(pretty: bool = False):
    """Executa todos os casos de teste em sequência."""
    print(f"\n{'='*60}")
    print(f"CRM AGENT SIMULATOR — {len(TEST_CASES)} casos de teste")
    print(f"Iniciado em: {datetime.utcnow().isoformat()}")
    print(f"{'='*60}\n")

    results = {"success": 0, "error": 0}

    for case_name in TEST_CASES:
        case = dict(TEST_CASES[case_name])  # cópia para não modificar o original
        description = case.pop("_description", "")

        try:
            result = await run_crm_agent(case)
            _print_result(case_name, description, result, pretty)
            results["success"] += 1
        except Exception as e:
            _print_error(case_name, e)
            results["error"] += 1

    print(f"\n{'='*60}")
    print(f"RESULTADO FINAL: {results['success']} ok | {results['error']} erro(s)")
    print(f"{'='*60}\n")


# =====================================================
# ENTRYPOINT
# =====================================================

def main():
    parser = argparse.ArgumentParser(description="CRM Agent Simulator")
    parser.add_argument(
        "--case",
        type=str,
        default="all",
        help=f"Caso a executar: {list(TEST_CASES.keys())} ou 'all'"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Exibe o JSON completo do output"
    )
    args = parser.parse_args()

    if args.case == "all":
        asyncio.run(run_all_cases(pretty=args.pretty))
    else:
        asyncio.run(run_single_case(args.case, pretty=args.pretty))


if __name__ == "__main__":
    main()