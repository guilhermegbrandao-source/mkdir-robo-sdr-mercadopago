#!/usr/bin/env python3
"""
SDR Agent — Autonomous Lead Sourcing for Mercado Pago Big Sellers

Uso normal (requer internet):
  python sdr_agent.py --nicho "moda feminina d2c" --limite 15

Modo demo (valida estrutura CSV sem internet):
  python sdr_agent.py --nicho "suplementos alimentares" --limite 2 --demo
"""
import argparse
import csv
import logging
import sys
import time
import random
from pathlib import Path

from config import OUTPUT_FILE, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX
from scraper import search_ecommerces, scrape_lead
from qualificador import score_lead

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

CSV_COLUMNS = [
    "Status_ICP",
    "Nome_Empresa",
    "Website",
    "CNPJ",
    "Plataforma_Ecommerce",
    "Telefone_WhatsApp",
    "Email_Corporativo",
    "Link_Busca_LinkedIn_Decisores",
    "Justificativa_Score",
]


def _init_csv(filepath: str) -> None:
    path = Path(filepath)
    if not path.exists():
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()


def _append_row(filepath: str, row: dict) -> None:
    with open(filepath, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow({col: row.get(col, "") for col in CSV_COLUMNS})


DEMO_LEADS = [
    {
        "website": "https://www.exemplo-suplementos.com.br",
        "cnpj": "12.345.678/0001-90",
        "plataforma": "VTEX",
        "telefone": "(11) 99999-1234",
        "email": "contato@exemplo-suplementos.com.br",
        "num_products_hint": 45,
        "has_checkout": True,
        "has_multiple_shipping": True,
        "has_security_seals": True,
        "raw_html": "",
    },
    {
        "website": "https://www.demo-suplementos2.com.br",
        "cnpj": "",
        "plataforma": "Nuvemshop",
        "telefone": "(21) 3333-5678",
        "email": "",
        "num_products_hint": 8,
        "has_checkout": True,
        "has_multiple_shipping": False,
        "has_security_seals": False,
        "raw_html": "",
    },
]


def run_demo(nicho: str, limite: int, output: str) -> None:
    logger.info(f"=== MODO DEMO | Nicho: '{nicho}' | Gerando {min(limite, len(DEMO_LEADS))} lead(s) fictício(s) ===")
    _init_csv(output)
    for scraped in DEMO_LEADS[:limite]:
        qualified = score_lead(scraped)
        _append_row(output, qualified)
        logger.info(f"  → {qualified['Status_ICP']} | {qualified['Nome_Empresa']} | {qualified['Plataforma_Ecommerce']}")
    logger.info(f"=== Demo concluído | Arquivo: {output} ===")


def run(nicho: str, limite: int, output: str = OUTPUT_FILE) -> None:
    logger.info(f"=== SDR Agent iniciado | Nicho: '{nicho}' | Meta: {limite} leads aprovados ===")
    _init_csv(output)

    urls = search_ecommerces(nicho, limite)
    if not urls:
        logger.error("Nenhuma URL encontrada. Verifique sua conexão ou ajuste o nicho.")
        sys.exit(1)

    logger.info(f"{len(urls)} URLs candidatas encontradas. Iniciando scraping...")

    aprovados = 0
    processados = 0

    for url in urls:
        if aprovados >= limite:
            logger.info(f"Meta de {limite} leads aprovados atingida!")
            break

        processados += 1
        logger.info(f"[{processados}/{len(urls)}] Processando: {url}")

        try:
            scraped = scrape_lead(url)
            qualified = score_lead(scraped)
            _append_row(output, qualified)

            status = qualified["Status_ICP"]
            empresa = qualified["Nome_Empresa"]
            plataforma = qualified["Plataforma_Ecommerce"]
            logger.info(f"  → {status} | {empresa} | {plataforma} | {qualified['Justificativa_Score'][:80]}")

            if status == "Aprovado":
                aprovados += 1

        except Exception as e:
            logger.error(f"Erro ao processar {url}: {e}")

        # Rate limiting
        if processados < len(urls):
            delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
            time.sleep(delay)

    logger.info(f"\n=== Concluído | {aprovados} aprovados | {processados} processados | Arquivo: {output} ===")


def main():
    parser = argparse.ArgumentParser(
        description="SDR Agent — Lead Sourcing para Mercado Pago Big Sellers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python sdr_agent.py --nicho "moda feminina d2c" --limite 15
  python sdr_agent.py --nicho "suplementos alimentares" --limite 5
  python sdr_agent.py --nicho "pet shop online" --limite 10 --output meus_leads.csv
        """,
    )
    parser.add_argument("--nicho", required=True, help='Segmento/nicho do e-commerce (ex: "moda feminina d2c")')
    parser.add_argument("--limite", type=int, default=10, help="Quantidade de leads APROVADOS desejada (default: 10)")
    parser.add_argument("--output", default=OUTPUT_FILE, help=f"Arquivo de saída (default: {OUTPUT_FILE})")
    parser.add_argument("--demo", action="store_true", help="Modo demo: gera leads fictícios sem acesso à internet (para validar estrutura CSV)")

    args = parser.parse_args()

    if args.limite < 1:
        parser.error("--limite deve ser >= 1")

    if args.demo:
        run_demo(nicho=args.nicho, limite=args.limite, output=args.output)
    else:
        run(nicho=args.nicho, limite=args.limite, output=args.output)


if __name__ == "__main__":
    main()
