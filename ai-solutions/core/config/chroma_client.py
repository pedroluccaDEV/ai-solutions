import os
import chromadb
import logging

logger = logging.getLogger(__name__)

# URL do servidor Chroma (pode ser pública ou privada)
CHROMA_URL = os.getenv("CHROMA_URL")
CHROMA_AUTH = os.getenv("CHROMA_AUTH")

# Cliente ChromaDB com tratamento de erro
chroma_client = None
chroma_available = False

try:
    if CHROMA_URL:
        chroma_client = chromadb.HttpClient(
            host=CHROMA_URL,
            headers={"Authorization": f"Bearer {CHROMA_AUTH}"} if CHROMA_AUTH else None
        )
        # Testar conexão
        chroma_client.heartbeat()
        chroma_available = True
        logger.info(f"Conexão ChromaDB estabelecida com sucesso: {CHROMA_URL}")
    else:
        logger.warning("CHROMA_URL não configurada - ChromaDB não disponível")
except Exception as e:
    logger.error(f"Falha ao conectar com ChromaDB: {e}")
    chroma_available = False

def get_or_create_collection(name: str):
    """Obtém ou cria uma coleção no ChromaDB com tratamento de erro"""
    if not chroma_available or not chroma_client:
        logger.error(f"ChromaDB não disponível - não foi possível acessar coleção: {name}")
        return None
    
    try:
        return chroma_client.get_or_create_collection(name=name)
    except Exception as e:
        logger.error(f"Erro ao acessar coleção ChromaDB {name}: {e}")
        return None

def is_chroma_available():
    """Verifica se o ChromaDB está disponível"""
    return chroma_available