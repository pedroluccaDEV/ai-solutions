# CRM Agent — Arquitetura

Sistema de decisão inteligente para leads, construído sobre Agno.

---

## Estrutura

```
crm_agent/
├── crm_builder.py    → define e instancia o Agent Agno (fixo por enquanto)
├── crm_planner.py    → analisa o lead, monta prompt enriquecido (sem LLM)
├── crm_executor.py   → chama o LLM, parseia e valida o output JSON
├── crm_agent.py      → orquestrador: une os três acima
└── crm_simulator.py  → simula payloads de API REST para testes
```

---

## Fluxo

```
Input estruturado (lead + history + context + constraints)
        ↓
[Planner]  — lógica pura, detecta intenção, monta prompt rico
        ↓
[Executor] — chama o Agent Agno, parseia JSON, valida campos
        ↓
Output estruturado (analysis + response + actions + metadata)
```

---

## Input

```json
{
  "lead": {
    "id":      "lead_123",
    "name":    "João",
    "message": "quero saber o preço",
    "status":  "new",
    "source":  "landing_page"
  },
  "history": [],
  "context": {
    "company": "Minha Empresa",
    "product": "Sistema X",
    "tone":    "comercial"
  },
  "constraints": {
    "max_tokens":     500,
    "response_style": "short"
  }
}
```

## Output

```json
{
  "analysis": {
    "intent":     "buy_interest",
    "confidence": 0.92,
    "priority":   "high",
    "stage":      "novo",
    "reasoning":  "Lead perguntou diretamente sobre preço"
  },
  "response": {
    "message": "Olá João! Temos ótimas opções...",
    "tone":    "friendly"
  },
  "actions": [
    {
      "type": "send_message",
      "payload": { "channel": "whatsapp" }
    },
    {
      "type": "update_status",
      "payload": { "new_status": "qualified" }
    }
  ],
  "metadata": {
    "model":           "gpt-4o-mini",
    "total_time_ms":   1240,
    "lead_id":         "lead_123"
  }
}
```

---

## Configuração

```env
OPENAI_API_KEY=sk-...
CRM_MODEL_ID=gpt-4o-mini     # opcional, padrão: gpt-4o-mini
```

---

## Executar testes

```bash
# Todos os casos
python crm_simulator.py

# Caso específico
python crm_simulator.py --case buy
python crm_simulator.py --case complaint

# Com JSON completo
python crm_simulator.py --case buy --pretty

# Casos disponíveis: buy | doubt | complaint | abandon
```

---

## Próximos passos

1. **Modelo dinâmico** — `crm_builder.py` recebe `model_config` como parâmetro
2. **Endpoint real** — substituir `crm_simulator.py` pelo handler da API REST
3. **Ações externas** — o sistema (não o agente) executa `send_message`, `update_status`, `notify_team`
4. **Persistência do histórico** — salvar `history` no banco após cada interação

---

## Decisões de design

| Decisão | Motivo |
|---|---|
| Planner sem LLM | Rápido, previsível, sem custo de token |
| Output JSON puro | Sistema pode processar ações programaticamente |
| Agente fixo no builder | Simples agora, fácil de tornar dinâmico depois |
| Validação no executor | Output nunca quebra o fluxo downstream |