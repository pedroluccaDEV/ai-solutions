import requests
import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Validação das variáveis obrigatórias
def get_env_var(key: str, default: str = None) -> str:
    value = os.getenv(key, default)
    if not value:
        print(f"[ERRO] Variável de ambiente '{key}' não encontrada.")
        if default:
            print(f"[INFO] Usando valor padrão: {default}")
            return default
        sys.exit(1)
    return value


class DeepSeekTitleAgent:
    def __init__(self):
        self.api_key = get_env_var('DEEPSEEK_API_KEY')
        # CORREÇÃO: Padronizar com maestro.py - usar DEEPSEEK_BASE_URL ou valor padrão
        self.api_url = get_env_var('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
        
        # Se não encontrar DEEPSEEK_API_URL, tenta DEEPSEEK_BASE_URL
        if self.api_url == 'https://api.deepseek.com/v1/chat/completions':
            base_url = os.getenv('DEEPSEEK_BASE_URL')
            if base_url:
                self.api_url = f"{base_url}/chat/completions"
                print(f"[INFO] Usando DEEPSEEK_BASE_URL: {self.api_url}")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def generate_title(self, input_data, style="profissional", max_tokens=50):
        """
        Gera um título único baseado no texto de entrada
        """
        prompt = f"""
        Com base no seguinte texto, gere um título {style} e atraente.
        O título deve ter no máximo 6 palavras, ser claro e conciso,
        sem explicações ou aspas, apenas o título final.

        Texto: "{input_data}"
        Título:
        """
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "Você é um especialista em criação de títulos claros, concisos e impactantes."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                print(f"[ERRO API] {response.status_code} - {response.text}")
                return self._generate_fallback_title(input_data)
                
        except Exception as e:
            print(f"[ERRO CONEXÃO] {e}")
            return self._generate_fallback_title(input_data)
    
    def _generate_fallback_title(self, input_data):
        """
        Gera um título de fallback quando a API falha
        """
        # Pega as primeiras palavras do texto
        words = input_data.strip().split()[:4]
        if len(words) >= 2:
            return " ".join(words).capitalize()
        elif len(words) == 1:
            return f"Conversa sobre {words[0]}"
        else:
            return "Nova Conversa"


# --- Função pública para uso via backend ---
def gerar_titulo(texto: str, estilo: str = "profissional") -> str:
    """
    Função pública para gerar título a partir de texto.
    Pode ser usada diretamente em um backend.
    """
    try:
        agent = DeepSeekTitleAgent()
        return agent.generate_title(texto, estilo)
    except Exception as e:
        print(f"[BACKEND ERRO] {e}")
        # Fallback mais robusto
        words = texto.strip().split()[:3]
        if len(words) >= 2:
            return " ".join(words).capitalize()
        elif len(words) == 1:
            return f"Conversa sobre {words[0]}"
        else:
            return "Nova Conversa"


# Função de teste para verificar configuração
def test_title_generation():
    """
    Função para testar a geração de títulos
    """
    test_text = "Como posso aprender programação Python?"
    try:
        title = gerar_titulo(test_text)
        print(f"[TESTE] Texto: {test_text}")
        print(f"[TESTE] Título gerado: {title}")
        return True
    except Exception as e:
        print(f"[TESTE FALHOU] {e}")
        return False


if __name__ == "__main__":
    # Executa teste se chamado diretamente
    test_title_generation()