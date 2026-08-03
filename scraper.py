import re
import time
import random
import logging
import urllib.parse
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import (
    USER_AGENTS, REQUEST_TIMEOUT, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX,
    ECOMMERCE_PLATFORMS, CHECKOUT_INDICATORS
)

logger = logging.getLogger(__name__)

CNPJ_PATTERN = re.compile(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}')
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
PHONE_PATTERN = re.compile(
    r'(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[-\s]?\d{4}'
)


def _random_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }


def _get(url: str, timeout: int = REQUEST_TIMEOUT) -> Optional[requests.Response]:
    """Safe GET with error handling."""
    try:
        resp = requests.get(url, headers=_random_headers(), timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout: {url}")
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP {e.response.status_code}: {url}")
    except requests.exceptions.ConnectionError:
        logger.warning(f"Conexão falhou: {url}")
    except Exception as e:
        logger.warning(f"Erro inesperado em {url}: {e}")
    return None


def search_ecommerces(nicho: str, limite: int) -> list[str]:
    """
    Busca e-commerces brasileiros via DuckDuckGo HTML (sem API key).
    Retorna lista de URLs únicas.
    """
    queries = [
        f'site:*.com.br "{nicho}" loja online comprar',
        f'"{nicho}" e-commerce brasil checkout frete',
        f'"{nicho}" loja virtual brasil comprar online',
        f'"{nicho}" site:*.com.br -site:mercadolivre.com.br -site:shopee.com.br',
    ]

    found_urls: set[str] = set()

    for query in queries:
        if len(found_urls) >= limite * 4:
            break

        encoded = urllib.parse.quote_plus(query)
        ddg_url = f"https://html.duckduckgo.com/html/?q={encoded}"

        time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
        resp = _get(ddg_url)
        if not resp:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.select("a.result__url"):
            href = a.get("href", "").strip()
            if href and not href.startswith("http"):
                href = "https://" + href
            parsed = urlparse(href)
            if parsed.netloc and ".com.br" in parsed.netloc:
                clean = f"{parsed.scheme}://{parsed.netloc}"
                found_urls.add(clean)

        # Fallback: pegar links do resultado
        for a in soup.select("a[href*='uddg=']"):
            href = a.get("href", "")
            match = re.search(r'uddg=([^&]+)', href)
            if match:
                decoded = urllib.parse.unquote(match.group(1))
                parsed = urlparse(decoded)
                if parsed.netloc and ".com.br" in parsed.netloc:
                    clean = f"{parsed.scheme}://{parsed.netloc}"
                    found_urls.add(clean)

    # Filtrar domínios de plataformas e marketplaces
    blacklist_domains = [
        "mercadolivre", "shopee", "amazon", "americanas", "submarino",
        "magazineluiza", "casasbahia", "pontofrio", "extra.com",
        "google", "facebook", "instagram", "youtube", "twitter",
        "linkedin", "wikipedia", "blogspot", "wordpress.com",
        "duckduckgo", "bing", "uol", "globo", "ig.com",
    ]
    filtered = [
        u for u in found_urls
        if not any(b in u.lower() for b in blacklist_domains)
    ]

    # Fallback: se DDG bloqueou, usar seed list curada por nicho
    if not filtered:
        logger.warning("DDG retornou 0 resultados (possível bloqueio 403). Usando seed list de fallback.")
        SEED_LISTS = {
            "suplementos": [
                "https://www.integralmedica.com.br",
                "https://www.growth.com.br",
                "https://www.bodybuilders.com.br",
                "https://www.probiotica.com.br",
                "https://www.darkness.com.br",
                "https://www.atlhetica.com.br",
                "https://www.nitroproteinas.com.br",
                "https://www.maxinutrition.com.br",
            ],
            "moda": [
                "https://www.animale.com.br",
                "https://www.farm21.com.br",
                "https://www.morena-rosa.com.br",
                "https://www.dzarm.com.br",
            ],
            "pet": [
                "https://www.petlove.com.br",
                "https://www.cobasi.com.br",
                "https://www.petz.com.br",
            ],
            "cosmeticos": [
                "https://www.beleza-na-web.com.br",
                "https://www.beautifulshop.com.br",
                "https://www.lojasrede.com.br",
            ],
            "autopecas": [
                "https://www.mercadocar.com.br",
                "https://www.jocar.com.br",
                "https://www.canaldapeca.com.br",
                "https://hipervarejo.com.br",
                "https://www.pitstop.com.br",
                "https://www.autozone.com.br",
                "https://goparts.com.br",
                "https://www.allpartsnet.com.br",
                "https://www.brondaniautopecas.com.br",
                "https://www.virtualautopecas.com.br",
                "https://www.kepecas.com.br",
                "https://www.bproautopecas.com.br",
                "https://www.brasilautopecas.com.br",
                "https://www.procurapecas.com.br",
                "https://www.maxparts.com.br",
                "https://www.conexaobrasilautopecas.com.br",
                "https://www.rsautoparts.com.br",
                "https://www.autopecasmax.com.br",
                "https://www.gamapecas.com.br",
                "https://www.kdapeca.com.br",
            ],
        }
        nicho_lower = nicho.lower()
        matched_seed = []
        for key, urls in SEED_LISTS.items():
            if key in nicho_lower or nicho_lower in key:
                matched_seed = urls
                break
        if not matched_seed:
            # Usar suplementos como padrão se nicho não mapeado
            matched_seed = SEED_LISTS["suplementos"]
        filtered = matched_seed
        logger.info(f"Seed list de fallback: {len(filtered)} URLs para nicho '{nicho}'")

    logger.info(f"Encontradas {len(filtered)} URLs candidatas para nicho '{nicho}'")
    return filtered[:limite * 4]


def _fetch_page_text(base_url: str, path: str) -> str:
    """Fetches a subpage and returns its text content."""
    url = urljoin(base_url, path)
    resp = _get(url)
    if resp:
        return resp.text
    return ""


def scrape_lead(url: str) -> dict:
    """
    Scrapes a single e-commerce URL and extracts all available data.
    Returns a dict with raw scraped fields.
    """
    result = {
        "website": url,
        "cnpj": "",
        "plataforma": "",
        "telefone": "",
        "email": "",
        "html_snippets": [],
        "page_texts": [],
        "num_products_hint": 0,
        "has_checkout": False,
        "has_multiple_shipping": False,
        "has_security_seals": False,
        "raw_html": "",
    }

    # Páginas a visitar
    paths_to_check = [
        "/", "/contato", "/quem-somos", "/sobre", "/sobre-nos",
        "/politica-de-privacidade", "/termos-de-uso", "/termos",
        "/fale-conosco",
    ]

    all_text = ""
    main_html = ""

    for i, path in enumerate(paths_to_check):
        if i > 0:
            time.sleep(random.uniform(1.0, 2.5))
        text = _fetch_page_text(url, path)
        if not text:
            continue
        all_text += text
        if path == "/":
            main_html = text
            result["raw_html"] = text[:5000]

    if not all_text:
        logger.warning(f"Sem conteúdo em {url}")
        return result

    soup_main = BeautifulSoup(main_html or all_text[:50000], "html.parser")

    # --- CNPJ ---
    cnpj_matches = CNPJ_PATTERN.findall(all_text)
    if cnpj_matches:
        result["cnpj"] = cnpj_matches[0]

    # --- E-mails ---
    emails = EMAIL_PATTERN.findall(all_text)
    # Filtrar e-mails genéricos de sistemas
    email_blacklist = ["sentry", "noreply", "no-reply", "example", "test", "@shopify", "@vtex", "@nuvemshop"]
    clean_emails = [e for e in emails if not any(b in e.lower() for b in email_blacklist)]
    if clean_emails:
        result["email"] = clean_emails[0]

    # --- Telefone ---
    phones = PHONE_PATTERN.findall(all_text)
    if phones:
        phone = phones[0].strip()
        # Limpar formatação
        phone = re.sub(r'[^\d+\s()-]', '', phone).strip()
        result["telefone"] = phone

    # --- Plataforma ---
    result["plataforma"] = _detect_platform(all_text, soup_main)

    # --- Indicadores de ICP ---
    text_lower = all_text.lower()

    result["has_checkout"] = any(ind in text_lower for ind in CHECKOUT_INDICATORS)

    shipping_keywords = ["sedex", "pac", "transportadora", "frete grátis", "jadlog", "correios", "transportes", "loggi"]
    shipping_count = sum(1 for kw in shipping_keywords if kw in text_lower)
    result["has_multiple_shipping"] = shipping_count >= 2

    security_keywords = ["ssl", "site seguro", "compra segura", "256-bit", "norton", "mcafee", "ebit", "reclame aqui"]
    result["has_security_seals"] = any(kw in text_lower for kw in security_keywords)

    # Estimar catálogo (heurística: número de itens ou categorias no menu)
    product_hints = len(soup_main.select("[class*='product'], [class*='produto'], [class*='item'], [id*='product']"))
    category_links = len([a for a in soup_main.select("a") if any(
        kw in a.get("href", "").lower() for kw in ["/categoria", "/category", "/produto", "/product", "/colecao", "/colecção"]
    )])
    result["num_products_hint"] = product_hints + category_links

    return result


def _detect_platform(html_text: str, soup: BeautifulSoup) -> str:
    """Identify e-commerce platform from HTML content."""
    html_lower = html_text.lower()
    for platform, indicators in ECOMMERCE_PLATFORMS.items():
        for indicator in indicators:
            if indicator.lower() in html_lower:
                return platform
    # Checar meta generator
    meta_gen = soup.find("meta", {"name": "generator"})
    if meta_gen:
        content = meta_gen.get("content", "").lower()
        for platform in ECOMMERCE_PLATFORMS:
            if platform.lower() in content:
                return platform
    return "Desconhecida"
