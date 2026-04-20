import os
import re
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# ============================================================
# ✅ Configuração inicial
# ============================================================
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

# ============================================================
# 🔧 Utilitários Simplificados
# ============================================================
def clean_message_for_title(message: str) -> str:
    """
    Limpa a mensagem removendo caracteres especiais e excessos.
    """
    # Remove URLs
    message = re.sub(r'http\S+', '', message)
    # Remove múltiplos espaços
    message = re.sub(r'\s+', ' ', message)
    # Remove caracteres especiais, mantendo pontuação básica
    message = re.sub(r'[^\w\s.,!?\-]', '', message)
    return message.strip()

def extract_keywords(message: str) -> str:
    """
    Extrai palavras-chave relevantes para o título.
    """
    STOPWORDS = {
        "de", "do", "da", "os", "as", "um", "uma", "para", "em", "no", "na",
        "sobre", "com", "que", "por", "dos", "das", "nos", "nas", "fale",
        "me", "diga", "conte", "explique", "mostre", "qual", "quais", "como",
        "pode", "poder", "ser", "está", "estou", "tem", "tenho", "quero",
        "gostaria", "por favor", "obrigado", "obrigada", "ok", "oi", "olá"
    }
    
    clean_text = re.sub(r'[^\w\s]', ' ', message.lower())
    words = clean_text.split()
    keywords = [word for word in words if word not in STOPWORDS and len(word) > 2]
    
    return " ".join(keywords[:5])  # Limita a 5 palavras-chave

# ============================================================
# 🧠 Função Principal para Gerar Título
# ============================================================
def generate_session_title(
    user_message: str,
    model_id: str = "deepseek-chat"
) -> str:
    """
    Gera um título curto e descritivo para a sessão baseado na mensagem do usuário.
    
    Args:
        user_message: Mensagem inicial do usuário
        model_id: Modelo DeepSeek a usar
        
    Returns:
        Título gerado para a sessão
    """
    
    # Limpa e prepara a mensagem
    clean_message = clean_message_for_title(user_message)
    keywords = extract_keywords(clean_message)
    
    # Se a mensagem for muito curta, usa ela mesma como título
    if len(clean_message) <= 30:
        return clean_message
    
    # Prompt específico para geração de títulos
    system_prompt = """Você é um assistente especializado em criar títulos curtos e descritivos para conversas.

SEU OBJETIVO:
- Criar um título de 3 a 7 palavras que resuma o assunto principal
- Ser claro, conciso e informativo
- Usar linguagem natural e amigável
- Manter o foco no tópico principal da mensagem

DIRETRIZES:
- NÃO incluir saudações como "Olá", "Oi", etc.
- NÃO usar aspas ou pontuação excessiva
- NÃO inventar informações que não estão na mensagem
- Focar no conteúdo substantivo da solicitação

EXEMPLOS:
- "Como configurar rede Wi-Fi" → "Configuração de rede Wi-Fi"
- "Preciso de ajuda com planilhas Excel" → "Ajuda com planilhas Excel" 
- "Explique conceitos de machine learning" → "Conceitos de machine learning"
- "Quero aprender programação Python" → "Aprendendo programação Python"

Retorne APENAS o título, sem explicações adicionais."""

    user_prompt = f"""
MENSAGEM DO USUÁRIO:
{clean_message}

PALAVRAS-CHAVE IDENTIFICADAS:
{keywords}

Crie um título curto e descritivo baseado na mensagem acima.
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "max_tokens": 50,  # Títulos são curtos
        "temperature": 0.3,  # Mais criativo mas consistente
        "stop": ["\n", ".", "!"]  # Para evitar frases longas
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"[TITLE SERVICE] Erro API: {response.status_code}")
            # Fallback: usa as primeiras palavras da mensagem
            return clean_message[:40] + "..." if len(clean_message) > 40 else clean_message

        data = response.json()
        title = data["choices"][0]["message"]["content"].strip()
        
        # Limpa possíveis caracteres estranhos no título
        title = re.sub(r'^["\']|["\']$', '', title)  # Remove aspas no início/fim
        title = title.split('\n')[0]  # Pega apenas a primeira linha
        
        # Garante que o título tenha um tamanho razoável
        if len(title) > 60:
            title = title[:57] + "..."
        elif len(title) < 3:
            # Fallback se o título for muito curto
            title = clean_message[:40] + "..." if len(clean_message) > 40 else clean_message
            
        print(f"[TITLE SERVICE] Título gerado: '{title}'")
        return title

    except Exception as e:
        print(f"[TITLE SERVICE] Erro: {e}")
        # Fallback robusto
        if len(clean_message) <= 50:
            return clean_message
        else:
            # Tenta criar um título das primeiras palavras significativas
            words = clean_message.split()
            if len(words) > 5:
                return " ".join(words[:5]) + "..."
            else:
                return clean_message[:47] + "..." if len(clean_message) > 50 else clean_message

# ============================================================
# 🔧 Função Auxiliar para Uso no DAO
# ============================================================
def generate_title_from_message(message: str) -> str:
    """
    Função simplificada para ser usada diretamente no DAO.
    Inclui fallbacks robustos para caso a API falhe.
    """
    if not message or not message.strip():
        return "Nova Conversa"
    
    message = message.strip()
    
    # Para mensagens muito curtas, usa diretamente
    if len(message) <= 30:
        return message
    
    # Tenta gerar título com IA
    try:
        title = generate_session_title(message)
        return title
    except Exception as e:
        print(f"[TITLE SERVICE] Fallback para título automático: {e}")
        # Fallback: primeiras palavras da mensagem
        words = message.split()
        if len(words) > 4:
            return " ".join(words[:4]) + "..."
        else:
            return message[:47] + "..." if len(message) > 50 else message