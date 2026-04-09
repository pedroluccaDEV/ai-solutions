from typing import List

def chunk_text_document(text: str, max_chars: int = 1000) -> List[str]:
    """
    Chunk básico de documentos grandes, usado para PDFs, textos crawleados etc.
    Pode ser substituído por lógica com NLTK ou SpaCy.
    """
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]