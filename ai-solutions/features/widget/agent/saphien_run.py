# features\channels\telegram\agent\telegram_planner.py
import asyncio
from features.channels.telegram.agent.telegram_agent import execute_evolution_agent

async def test():
    result = await execute_evolution_agent(
        request_data={
            "user_id": "pQTwXbRfVEPvp1K8QrH38BGAduA2",
            "agent_id": "6926e9130d8100337e36252b",
            "message": "Qual é a capital do Brasil?"
        },
        user_jwt="test",
        user_id="pQTwXbRfVEPvp1K8QrH38BGAduA2"
    )
    
    print(f"✅ Sucesso: {result.get('success')}")
    print(f"📝 Resposta: {result.get('response')}")
    print(f"📊 Tokens: {result.get('tokens')}")

asyncio.run(test())