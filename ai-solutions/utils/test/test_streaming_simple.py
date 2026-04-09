import asyncio
import os
import sys
from dotenv import load_dotenv

# Ajusta o sys.path para permitir imports locais
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

async def test_streaming():
    try:
        from utils.agent.executor_agent_streaming import run_executor_streaming
        
        agent_data = {
            "name": "Test Agent",
            "description": "Agente de teste com streaming",
            "model": {"temperature": 0.7, "maxTokens": 2000},
            "tools": [],
            "personalityInstructions": "Responda de forma clara e concisa em português"
        }
        
        print("Testando streaming com Agno...")
        
        async for chunk in run_executor_streaming(
            agent_data=agent_data,
            prompt="Olá, como você está?",
            user_token="test-token",
            user_id="test-user",
            knowledge_collection_name=None,
            api_base_url="http://localhost:8080",
            mcp_server_id=None
        ):
            if chunk.get("complete"):
                print("\nStream completo")
                break
            elif chunk.get("error"):
                print(f"\nErro: {chunk.get('error')}")
                break
            else:
                token = chunk.get("token", "")
                try:
                    # Forçar encoding UTF-8 para o terminal Windows
                    print(token.encode('utf-8', errors='ignore').decode('utf-8'), end="", flush=True)
                except Exception:
                    # Fallback seguro
                    safe_token = token.encode('ascii', errors='ignore').decode('ascii')
                    print(safe_token, end="", flush=True)
                
    except Exception as e:
        print(f"\nErro durante importacao/execucao: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming())