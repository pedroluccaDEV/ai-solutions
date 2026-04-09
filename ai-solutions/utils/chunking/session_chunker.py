from typing import List, Dict

def chunk_text_session(text: str, max_chars: int = 500) -> List[str]:
    """Chunk simples por caractere para mensagens curtas"""
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]

def chunk_messages_session(messages: List[Dict], max_chars: int = 500) -> List[Dict]:
    """Divide mensagens da sessão LLM em chunks preservando metadados"""
    chunked = []
    for msg in messages:
        content = msg.get("content")
        if not content:
            continue

        chunks = chunk_text_session(content, max_chars=max_chars)
        for i, chunk in enumerate(chunks):
            chunked.append({
                "content": chunk,
                "role": msg.get("role", "user"),
                "timestamp": msg.get("timestamp"),
                "chunk_index": i
            })
    return chunked