from sentence_transformers import SentenceTransformer
import uuid
import logging
import re

logger = logging.getLogger(__name__)

# Modelo de embedding desabilitado temporariamente para evitar problemas de conexão
model = None

# Função placeholder para embeddings
def generate_dummy_embeddings(text_chunks: list[str]) -> list[list[float]]:
    """Gera embeddings dummy para desenvolvimento local"""
    return [[0.1] * 384 for _ in text_chunks]  # Dummy embeddings de 384 dimensões

def chunk_text(text: str, max_tokens: int = 500, overlap: int = 50) -> list[str]:
    """
    Divide o texto em chunks com sobreposição para manter contexto.
    """
    if not text or not text.strip():
        return []
    
    # Limpa o texto removendo espaços excessivos
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Se o texto for muito pequeno, retorna como único chunk
    if len(text) <= max_tokens:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Encontra o final do chunk, tentando quebrar em pontuação
        end = start + max_tokens
        
        if end < len(text):
            # Tenta quebrar em pontuação para manter contexto
            for break_char in ['. ', '! ', '? ', '\n\n', '\n', ' ']:
                break_pos = text.rfind(break_char, start, end)
                if break_pos != -1 and break_pos > start + max_tokens // 2:
                    end = break_pos + len(break_char)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move para o próximo chunk com sobreposição
        start = end - overlap if end - overlap > start else end
    
    logger.info(f"Texto dividido em {len(chunks)} chunks")
    return chunks

def generate_embeddings(text_chunks: list[str]) -> list[list[float]]:
    if model is None:
        return generate_dummy_embeddings(text_chunks)
    return model.encode(text_chunks).tolist()

def process_document(content: str, metadata: dict, collection) -> int:
    """
    Processa um documento, divide em chunks e salva no ChromaDB.
    Retorna o número de chunks processados.
    """
    try:
        if not content or not content.strip():
            logger.warning("Conteúdo vazio recebido para processamento")
            return 0
        
        chunks = chunk_text(content)
        
        if not chunks:
            logger.warning("Nenhum chunk gerado do conteúdo")
            return 0
        
        logger.info(f"Processando {len(chunks)} chunks para documento: {metadata.get('title', 'Unknown')}")
        
        embeddings = generate_embeddings(chunks)
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [metadata | {"chunk_index": i, "total_chunks": len(chunks)} for i in range(len(chunks))]

        # Adiciona chunks ao ChromaDB em lotes para evitar problemas de memória
        batch_size = 100
        total_added = 0
        
        for i in range(0, len(chunks), batch_size):
            batch_end = min(i + batch_size, len(chunks))
            batch_chunks = chunks[i:batch_end]
            batch_embeddings = embeddings[i:batch_end]
            batch_metadatas = metadatas[i:batch_end]
            batch_ids = ids[i:batch_end]
            
            try:
                collection.add(
                    documents=batch_chunks,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                total_added += len(batch_chunks)
                logger.info(f"Lote {i//batch_size + 1} adicionado: {len(batch_chunks)} chunks")
            except Exception as batch_error:
                logger.error(f"Erro ao adicionar lote {i//batch_size + 1} ao ChromaDB: {batch_error}")
                # Continua com os próximos lotes mesmo se um falhar
        
        logger.info(f"Documento processado com sucesso: {total_added} chunks salvos no ChromaDB")
        return total_added
        
    except Exception as e:
        logger.error(f"Erro ao processar documento: {e}")
        return 0