# services/v1/firecrawl_agent_service.py

from dotenv import load_dotenv
import os
import re
import html
import unicodedata
import trafilatura
import asyncio
import sys
from playwright.async_api import async_playwright

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def clean_extracted_text(text: str) -> str:
    """
    Limpa o texto extraído pelo crawler removendo caracteres de escape,
    códigos Unicode malformados e outros artefatos de scraping.
    """
    if not text or not isinstance(text, str):
        return ""

    try:
        # Normaliza códigos Unicode
        text = re.sub(r'\\{1,}u([0-9a-fA-F]{4})', r'\\u\1', text)
        try:
            text = text.encode().decode('unicode_escape')
        except (UnicodeDecodeError, UnicodeEncodeError):
            text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)

        # Remove escapes excessivos
        text = re.sub(r'\\{3,}', r'\\', text)
        text = re.sub(r'\\{2}', '', text)

        # Corrige acentos portugueses
        text = re.sub(r'\\([çáàâãéêíóôõúüÇÁÀÂÃÉÊÍÓÔÕÚÜ])', r'\1', text)

        # Substituições específicas
        escape_replacements = [
            ('\\\\ç', 'ç'), ('\\\\Ç', 'Ç'),
            ('\\\\á', 'á'), ('\\\\à', 'à'), ('\\\\â', 'â'), ('\\\\ã', 'ã'),
            ('\\\\é', 'é'), ('\\\\ê', 'ê'), ('\\\\í', 'í'),
            ('\\\\ó', 'ó'), ('\\\\ô', 'ô'), ('\\\\õ', 'õ'),
            ('\\\\ú', 'ú'), ('\\\\ü', 'ü'),
            ('\\\ç', 'ç'), ('\\\á', 'á'), ('\\\é', 'é'), ('\\\í', 'í'),
            ('\\\ó', 'ó'), ('\\\ú', 'ú'), ('\\\ã', 'ã'), ('\\\õ', 'õ')
        ]
        for escaped, normal in escape_replacements:
            text = text.replace(escaped, normal)

        # Corrige pontuação escapada
        text = re.sub(r'\\([.,;:!?()[\]{}"])', r'\1', text)

        # Normaliza quebras de linha e tabs
        text = text.replace('\\\\n', '\n').replace('\\n', '\n')
        text = text.replace('\\\\r', '\r').replace('\\r', '\r')
        text = text.replace('\\\\t', '\t').replace('\\t', '\t')
        text = text.replace('\\/', '/')

        # Decodifica entidades HTML
        text = html.unescape(text)

        # Normaliza espaços e quebras de linha
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()

        # Normalização Unicode final
        text = unicodedata.normalize('NFC', text)

        return text

    except Exception as e:
        print(f"[ERROR] Erro na limpeza do texto: {e}")
        return text if isinstance(text, str) else ""


def crawl_with_trafilatura(url: str) -> str:
    """
    Tenta extrair conteúdo de páginas HTML estáticas usando Trafilatura.
    """
    print(f"[LOG] Executando Trafilatura com URL: {url}")
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            print(f"[WARN] Não foi possível baixar o conteúdo de {url}")
            return ""

        extracted = trafilatura.extract(downloaded)
        if not extracted:
            print(f"[WARN] Trafilatura não extraiu conteúdo útil de {url}")
            return ""

        return clean_extracted_text(extracted)

    except Exception as e:
        print(f"[ERROR] Erro no Trafilatura: {e}")
        return ""


async def crawl_with_playwright_async(url: str) -> str:
    """
    Extrai conteúdo de páginas dinâmicas (JS-heavy) usando Playwright headless async.
    """
    print(f"[LOG] Executando Playwright (async) com URL: {url}")

    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run',
                    '--disable-extensions',
                    '--disable-default-apps'
                ]
            )

            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )

            page = await context.new_page()
            page.set_default_timeout(30000)

            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(2000)
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    pass
                content = await page.content()
            except Exception as nav_error:
                print(f"[ERROR] Erro de navegação: {nav_error}")
                content = ""
            finally:
                await browser.close()

            if not content:
                print(f"[WARN] Playwright não conseguiu extrair conteúdo de {url}")
                return ""

            try:
                extracted = trafilatura.extract(content)
                if extracted:
                    return clean_extracted_text(extracted)
            except:
                pass

            return clean_extracted_text(content)

    except Exception as e:
        print(f"[ERROR] Playwright falhou: {e}")
        return ""


async def robust_crawl_async(url: str) -> str:
    """
    Crawler robusto com fallback:
    1. Tenta Trafilatura (rápido, barato)
    2. Se falhar ou extrair pouco conteúdo, usa Playwright
    """
    if not url or not url.startswith(('http://', 'https://')):
        print(f"[ERROR] URL inválida: {url}")
        return ""

    try:
        text = crawl_with_trafilatura(url)
        if text and len(text.strip()) > 500:
            print(f"[SUCCESS] Trafilatura extraiu {len(text)} caracteres")
            return text

        print("[FALLBACK] Usando Playwright async")
        playwright_text = await crawl_with_playwright_async(url)
        if playwright_text and len(playwright_text.strip()) > 100:
            print(f"[SUCCESS] Playwright extraiu {len(playwright_text)} caracteres")
            return playwright_text

        print("[WARN] Ambos métodos falharam, retornando parcial")
        return text if text else ""

    except Exception as e:
        print(f"[ERROR] Erro geral no robust_crawl_async: {e}")
        return ""


def clean_existing_chunks(chunks: list) -> list:
    """
    Limpa uma lista de chunks já extraídos anteriormente.
    """
    if not chunks or not isinstance(chunks, list):
        return []

    print(f"[LOG] Limpando {len(chunks)} chunks existentes...")
    cleaned_chunks = []

    for i, chunk in enumerate(chunks):
        if chunk and isinstance(chunk, str):
            cleaned_chunk = clean_extracted_text(chunk)
            if cleaned_chunk.strip():
                cleaned_chunks.append(cleaned_chunk)

        if i > 0 and i % 100 == 0:
            print(f"[LOG] Processados {i+1}/{len(chunks)} chunks")

    print(f"[LOG] Limpeza concluída. {len(cleaned_chunks)} chunks limpos de {len(chunks)} originais.")
    return cleaned_chunks


async def test_crawler():
    """
    Função de teste do crawler
    """
    test_urls = [
        "https://g1.globo.com",
        "https://www.example.com",
        "https://httpbin.org/html"
    ]

    for url in test_urls:
        print(f"\n[TEST] Iniciando teste do crawler com URL: {url}")
        try:
            content = await robust_crawl_async(url)
            if content:
                print(f"[TEST] ✅ Conteúdo extraído com sucesso!")
                print(f"[TEST] Tamanho: {len(content)} caracteres")
                print(f"[TEST] Preview: {content[:500]}...")
            else:
                print("[TEST] ❌ Nenhum conteúdo foi extraído.")
        except Exception as e:
            print(f"[TEST] ❌ Erro durante o teste: {e}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(test_crawler())
