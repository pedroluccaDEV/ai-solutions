# services/v1/origin_parser_service.py

import requests
import fitz  # PyMuPDF
import tempfile
import os
from pathlib import Path
from urllib.parse import urlparse
from utils.kb.firecrawl_agent_service import robust_crawl_async


def extract_pdf_text(url: str) -> str:
    """
    Extrai texto de um PDF baixado da URL.
    Versão com tratamento de erros e limpeza de arquivos temporários.
    """
    temp_file = None
    try:
        print(f"[LOG] Baixando PDF: {url}")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        if 'application/pdf' not in response.headers.get('content-type', ''):
            print(f"[WARN] URL não retornou um PDF válido: {url}")
            return ""

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name

        doc = fitz.open(temp_file_path)
        text_content = []
        for page_num, page in enumerate(doc):
            try:
                page_text = page.get_text()
                if page_text.strip():
                    text_content.append(page_text)
                if (page_num + 1) % 10 == 0:
                    print(f"[LOG] Processadas {page_num + 1} páginas...")
            except Exception as page_error:
                print(f"[WARN] Erro ao processar página {page_num + 1}: {page_error}")
        doc.close()

        final_text = "\n\n".join(text_content)
        print(f"[LOG] PDF processado: {len(final_text)} caracteres extraídos")
        return final_text

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Erro ao baixar PDF: {e}")
        return ""
    except Exception as e:
        print(f"[ERROR] Erro ao processar PDF: {e}")
        return ""
    finally:
        if temp_file and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass


def extract_title_from_url(url: str) -> str:
    """
    Gera um título amigável a partir da URL.
    """
    try:
        parsed = urlparse(url)
        if url.lower().endswith('.pdf'):
            return Path(parsed.path).stem or parsed.netloc
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.strip('/').replace('/', ' - ')
        return f"{domain}: {path}" if path else domain
    except:
        return url


async def extract_content_from_origin(origin: dict) -> tuple[str, str]:
    """
    Extrai conteúdo de uma origem (PDF ou URL).
    Retorna uma tupla: (conteúdo, título)
    """
    if not isinstance(origin, dict):
        raise ValueError("Origin deve ser um dicionário")

    url = origin.get("url")
    if not url or not isinstance(url, str):
        raise ValueError("Origin não possui campo 'url' válido")

    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        raise ValueError(f"URL deve começar com http:// ou https://: {url}")

    origin_type = origin.get("type", "").lower()

    try:
        if origin_type == "pdf" or url.lower().endswith('.pdf'):
            print(f"[LOG] Processando PDF: {url}")
            content = extract_pdf_text(url)
            title = extract_title_from_url(url)
            if not content or len(content.strip()) < 100:
                print(f"[WARN] PDF com pouco conteúdo ou vazio: {url}")
                return "", title
            return content, title

        elif origin_type in ("crawler", "crawler_ai", "url", ""):
            print(f"[LOG] Processando URL com crawler: {url}")
            content = await robust_crawl_async(url)
            title = extract_title_from_url(url)
            if not content or len(content.strip()) < 100:
                print(f"[WARN] URL com pouco conteúdo ou vazio: {url}")
                return "", title
            return content, title

        else:
            raise ValueError(f"Tipo de origem não suportado: {origin_type}")

    except Exception as e:
        print(f"[ERROR] Erro ao processar origem {url}: {e}")
        return "", extract_title_from_url(url)


# Função de teste rápido
async def test_origin_parser():
    test_origins = [
        {"url": "https://www.example.com", "type": "crawler"},
        {"url": "https://httpbin.org/html", "type": "crawler_ai"},
        # {"url": "https://example.com/test.pdf", "type": "pdf"},
    ]
    for origin in test_origins:
        print(f"\n[TEST] Testando origem: {origin}")
        try:
            content, title = await extract_content_from_origin(origin)
            print(f"[TEST] ✅ Título: {title}")
            if content:
                print(f"[TEST] ✅ Conteúdo extraído: {len(content)} caracteres")
                print(f"[TEST] Preview: {content[:300]}...")
            else:
                print("[TEST] ❌ Nenhum conteúdo extraído")
        except Exception as e:
            print(f"[TEST] ❌ Erro: {e}")


if __name__ == "__main__":
    import asyncio, sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(test_origin_parser())
