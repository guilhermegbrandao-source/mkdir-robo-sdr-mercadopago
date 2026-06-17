import re
import logging
import urllib.parse
from config import (
    ICP_MIN_REVENUE, GIGANTES_BLACKLIST, PLATAFORMAS_ENTRADA,
    LINKEDIN_CARGOS,
)

logger = logging.getLogger(__name__)


def _is_giant(company_name: str, website: str) -> bool:
    combined = (company_name + " " + website).lower()
    return any(g in combined for g in GIGANTES_BLACKLIST)


def _is_low_tier_platform(platform: str, website: str) -> bool:
    plat_lower = platform.lower()
    web_lower = website.lower()
    return any(p in plat_lower or p in web_lower for p in PLATAFORMAS_ENTRADA)


def score_lead(scraped: dict) -> dict:
    """
    Applies ICP scoring to scraped data.
    Returns enriched dict with Status_ICP and Justificativa_Score.
    """
    score = 0
    justificativas = []
    reprovado_motivo = ""

    company_name = _extract_company_name(scraped.get("website", ""))
    website = scraped.get("website", "")

    # --- Filtros Negativos Imediatos ---
    if _is_giant(company_name, website):
        return _build_output(scraped, company_name, "Reprovado", 0,
                             "Empresa gigante/hiperconhecida — fora do ICP Middle Market")

    platform = scraped.get("plataforma", "Desconhecida")
    if _is_low_tier_platform(platform, website):
        return _build_output(scraped, company_name, "Reprovado", 0,
                             f"Plataforma de entrada ({platform}) — provavelmente abaixo do faturamento mínimo")

    if not scraped.get("has_checkout"):
        reprovado_motivo = "Nenhum indicador de checkout/compra encontrado no site"

    # --- Filtros Positivos (Pontuação) ---
    if scraped.get("has_checkout"):
        score += 30
        justificativas.append("checkout/compra detectado")

    if scraped.get("has_multiple_shipping"):
        score += 25
        justificativas.append("múltiplos métodos de envio")

    if scraped.get("has_security_seals"):
        score += 15
        justificativas.append("selos de segurança presentes")

    hints = scraped.get("num_products_hint", 0)
    if hints >= 20:
        score += 20
        justificativas.append(f"catálogo amplo detectado ({hints} elementos de produto/categoria)")
    elif hints >= 5:
        score += 10
        justificativas.append(f"catálogo moderado ({hints} elementos)")

    if platform not in ("Desconhecida", "") and platform not in [p.title() for p in PLATAFORMAS_ENTRADA]:
        score += 10
        justificativas.append(f"plataforma profissional: {platform}")

    if scraped.get("cnpj"):
        score += 5
        justificativas.append("CNPJ público exposto (empresa regularizada)")

    # --- Decisão Final ---
    if reprovado_motivo and score < 20:
        status = "Reprovado"
        justificativa = reprovado_motivo
    elif score >= 50:
        status = "Aprovado"
        justificativa = "Score alto: " + "; ".join(justificativas) + f" (score={score}/100)"
    elif score >= 25:
        status = "Aprovado"
        justificativa = "Score moderado: " + "; ".join(justificativas) + f" (score={score}/100) — validar manualmente"
    else:
        status = "Reprovado"
        justificativa = "Score insuficiente: " + ("; ".join(justificativas) or "poucos indicadores de e-commerce profissional") + f" (score={score}/100)"

    return _build_output(scraped, company_name, status, score, justificativa)


def _extract_company_name(website: str) -> str:
    """Extracts a clean company name from the domain."""
    from urllib.parse import urlparse
    parsed = urlparse(website)
    domain = parsed.netloc or website
    # Remove www. e TLDs
    name = re.sub(r'^www\.', '', domain)
    name = re.sub(r'\.(com\.br|com|net|org|br)$', '', name)
    return name.strip().title()


def _build_linkedin_url(company_name: str) -> str:
    cargos_query = " OR ".join(f'"{c}"' for c in LINKEDIN_CARGOS)
    query = f"{company_name} {cargos_query}"
    encoded = urllib.parse.quote_plus(query)
    return f"https://www.linkedin.com/search/results/people/?keywords={encoded}"


def _predict_email_patterns(company_name: str, website: str) -> str:
    """Generates likely corporate email patterns."""
    from urllib.parse import urlparse
    parsed = urlparse(website)
    domain = parsed.netloc or website
    domain = re.sub(r'^www\.', '', domain)

    first_name_placeholder = "primeironome"
    patterns = [
        f"{first_name_placeholder}@{domain}",
        f"contato@{domain}",
        f"comercial@{domain}",
        f"financeiro@{domain}",
    ]
    return " | ".join(patterns)


def _build_output(scraped: dict, company_name: str, status: str, score: int, justificativa: str) -> dict:
    website = scraped.get("website", "")
    email = scraped.get("email", "")
    if not email:
        email = _predict_email_patterns(company_name, website)

    return {
        "Status_ICP": status,
        "Nome_Empresa": company_name,
        "Website": website,
        "CNPJ": scraped.get("cnpj", ""),
        "Plataforma_Ecommerce": scraped.get("plataforma", "Desconhecida"),
        "Telefone_WhatsApp": scraped.get("telefone", ""),
        "Email_Corporativo": email,
        "Link_Busca_LinkedIn_Decisores": _build_linkedin_url(company_name),
        "Justificativa_Score": justificativa,
    }
