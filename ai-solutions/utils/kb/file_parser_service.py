import fitz  # PyMuPDF
import docx
import json
import csv
import os
import tempfile
import logging
import chardet
from io import BytesIO
from typing import List, Dict, Union
from fastapi import UploadFile

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SUPPORTED_EXTENSIONS = {"pdf", "docx", "txt", "md", "json", "csv"}

# --- Utilitários ---

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r", "\n")
    text = text.replace("\t", " ")
    text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    text = " ".join(text.split())
    return text.strip()


def detect_encoding(raw_bytes: bytes) -> str:
    try:
        detection = chardet.detect(raw_bytes)
        encoding = detection.get("encoding", "utf-8")
        return encoding or "utf-8"
    except Exception:
        return "utf-8"


# --- Extratores individuais ---

async def extract_text_from_file(file: UploadFile) -> Dict[str, str]:
    filename = file.filename or "unknown"
    ext = filename.split(".")[-1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        logger.warning(f"Tipo de arquivo não suportado: {ext}")
        return {"filename": filename, "content": ""}

    try:
        contents = await file.read()
        if not contents:
            return {"filename": filename, "content": ""}

        if ext == "pdf":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(contents)
                tmp_path = tmp.name
            try:
                text_parts = []
                with fitz.open(tmp_path) as doc:
                    for page in doc:
                        page_text = page.get_text("text") or page.get_text("blocks")
                        if isinstance(page_text, list):
                            page_text = "\n".join([blk[4] for blk in page_text if blk[4].strip()])
                        if page_text:
                            text_parts.append(page_text)
                text = "\n".join(text_parts)
                return {"filename": filename, "content": clean_text(text)}
            finally:
                os.unlink(tmp_path)

        elif ext == "docx":
            doc = docx.Document(BytesIO(contents))
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            return {"filename": filename, "content": clean_text(text)}

        elif ext in {"txt", "md"}:
            encoding = detect_encoding(contents)
            text = contents.decode(encoding, errors="ignore")
            return {"filename": filename, "content": clean_text(text)}

        elif ext == "json":
            try:
                data = json.loads(contents)
                text = json.dumps(data, indent=2, ensure_ascii=False)
                return {"filename": filename, "content": clean_text(text)}
            except Exception as e:
                logger.error(f"Erro ao processar JSON {filename}: {e}")
                return {"filename": filename, "content": ""}

        elif ext == "csv":
            encoding = detect_encoding(contents)
            decoded = contents.decode(encoding, errors="ignore")
            reader = csv.reader(decoded.splitlines())
            rows = [" | ".join(row) for row in reader if any(cell.strip() for cell in row)]
            text = "\n".join(rows)
            return {"filename": filename, "content": clean_text(text)}

        else:
            logger.warning(f"Extensão não tratada explicitamente: {ext}")
            return {"filename": filename, "content": ""}

    except Exception as e:
        logger.error(f"Erro ao processar arquivo {filename}: {e}")
        return {"filename": filename, "content": ""}


# --- Função principal para múltiplos arquivos ---

async def parse_uploaded_files(files: Union[UploadFile, List[UploadFile]]) -> List[Dict[str, str]]:
    if not files:
        return []

    if not isinstance(files, list):
        files = [files]

    parsed = []
    for f in files:
        result = await extract_text_from_file(f)
        if result["content"].strip():
            parsed.append(result)

    logger.info(f"Arquivos processados: {len(parsed)}/{len(files)} com conteúdo válido.")
    return parsed


# --- Função MAIN para testes locais ---

def main(file_paths: List[str]):
    """
    Permite testar localmente o parser sem FastAPI.
    Recebe uma lista de paths de arquivos, simula UploadFile e imprime resultados.
    """
    import asyncio

    async def _run():
        uploads = []
        for path in file_paths:
            filename = os.path.basename(path)
            with open(path, "rb") as f:
                uploads.append(UploadFile(filename=filename, file=BytesIO(f.read())))
        results = await parse_uploaded_files(uploads)
        for r in results:
            print(f"\n--- {r['filename']} ---")
            print(r['content'][:500] + "..." if len(r['content']) > 500 else r['content'])
            print(f"--- Total chars: {len(r['content'])} ---")
    asyncio.run(_run())


# --- Execução direta ---

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)  # diretório do script atual
    files_to_test = [
        os.path.join(base_dir, "test_files", "test.pdf"),
        os.path.join(base_dir, "test_files", "download.pdf"),
    ]
    main(files_to_test)
