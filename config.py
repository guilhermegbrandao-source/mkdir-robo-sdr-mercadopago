# Target ICP configuration
ICP_MIN_REVENUE = 300_000  # R$ 300k/month

# Cargo-alvo para busca no LinkedIn
LINKEDIN_CARGOS = [
    "Gerente de E-commerce",
    "CFO",
    "Diretor Comercial",
    "Head de E-commerce",
    "CEO",
    "Diretor Financeiro",
    "VP Comercial",
]

# Plataformas de e-commerce e seus indicadores HTML
ECOMMERCE_PLATFORMS = {
    "VTEX": ["vtex.com", "vtexcommercestable", "vteximg.com.br", "__RUNTIME__"],
    "Shopify": ["shopify.com", "cdn.shopify.com", "Shopify.theme", "myshopify.com"],
    "Nuvemshop": ["nuvemshop.com.br", "tiendanube.com", "lojavirtualnuvem", "d26lpennugtm8s.cloudfront.net"],
    "Magento": ["Magento", "mage/", "requirejs/require.js", "magento"],
    "Tray": ["tray.com.br", "tcdn.com.br", "loja.tray"],
    "WooCommerce": ["woocommerce", "wp-content/plugins/woocommerce", "wc-ajax"],
    "LGPD/Wake": ["wake.com", "wakecommerce"],
    "Linx": ["linx.com.br", "linxcommerce"],
    "Salesforce Commerce": ["demandware", "salesforce", "sfcc"],
}

# Marcas gigantes a evitar (filtro negativo)
GIGANTES_BLACKLIST = [
    "amaro", "arezzo", "lojas renner", "riachuelo", "c&a", "hering",
    "centauro", "netshoes", "zattini", "submarino", "americanas",
    "magazine luiza", "casas bahia", "ponto frio", "extra",
    "mercado livre", "shopee", "amazon", "aliexpress",
    "dafiti", "kanui", "tricae", "nike", "adidas", "puma",
    "samsung", "apple", "dell", "lenovo", "hp",
    "carrefour", "walmart", "grupo soma", "grupo iguatemi",
]

# Plataformas de entrada (low-cost, geralmente faturamento baixo)
PLATAFORMAS_ENTRADA = ["wix", "webnode", "jimdo", "godaddy website", "uol host"]

# Indicadores de checkout profissional (filtro positivo)
CHECKOUT_INDICATORS = [
    "checkout", "carrinho", "cart", "frete", "parcelamento",
    "pix", "boleto", "cartão", "entrega", "rastreio", "rastreamento",
]

# User agents para rotação
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

OUTPUT_FILE = "leads_mercado_pago.csv"
REQUEST_TIMEOUT = 15
REQUEST_DELAY_MIN = 2.0
REQUEST_DELAY_MAX = 5.0
