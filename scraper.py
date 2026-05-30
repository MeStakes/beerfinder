"""
Scraper multi-sorgente per offerte birra nei supermercati italiani.
Fonti: promoqui.it (JSON embedded), tiendeo.it (__NEXT_DATA__), volantino.it, offerte.it
"""
import httpx
import asyncio
import re
import random
import json as _json
from typing import Optional
from bs4 import BeautifulSoup
from database import log_scrape

# --- Supermercati noti con logo emoji e colore brand ---
SUPERMARKET_META = {
    "lidl": {"logo": "🔵", "color": "#0050aa", "full_name": "Lidl"},
    "esselunga": {"logo": "🟢", "color": "#006b2b", "full_name": "Esselunga"},
    "conad": {"logo": "🔴", "color": "#e30613", "full_name": "Conad"},
    "carrefour": {"logo": "🔵", "color": "#004899", "full_name": "Carrefour"},
    "eurospin": {"logo": "🟡", "color": "#ffcc00", "full_name": "Eurospin"},
    "penny": {"logo": "🔴", "color": "#e30613", "full_name": "Penny Market"},
    "aldi": {"logo": "🔵", "color": "#00539f", "full_name": "Aldi"},
    "in's": {"logo": "🟠", "color": "#f47920", "full_name": "IN'S Mercato"},
    "md": {"logo": "🟡", "color": "#f5a200", "full_name": "MD Discount"},
    "coop": {"logo": "🔵", "color": "#0072bc", "full_name": "Coop"},
    "ipercoop": {"logo": "🔵", "color": "#0072bc", "full_name": "Ipercoop"},
    "iper": {"logo": "🟣", "color": "#6a0dad", "full_name": "Iper"},
    "sigma": {"logo": "🔴", "color": "#e52330", "full_name": "Sigma"},
    "despar": {"logo": "🟢", "color": "#007a33", "full_name": "Despar"},
    "interspar": {"logo": "🟢", "color": "#007a33", "full_name": "Interspar"},
    "pam": {"logo": "🔴", "color": "#da291c", "full_name": "Pam"},
    "u2": {"logo": "🟠", "color": "#ff6600", "full_name": "U2 Supermercato"},
    "famila": {"logo": "🔵", "color": "#004b87", "full_name": "Famila"},
    "simply": {"logo": "🟢", "color": "#00843d", "full_name": "Simply"},
    "tigros": {"logo": "🟠", "color": "#ff6f00", "full_name": "Tigros"},
    "italmark": {"logo": "🔵", "color": "#003f8a", "full_name": "Italmark"},
    "unes": {"logo": "🟠", "color": "#e05c00", "full_name": "Unes"},
    "gigante": {"logo": "🟢", "color": "#007a33", "full_name": "Il Gigante"},
    "bricocenter": {"logo": "🔴", "color": "#cc0000", "full_name": "Bricocenter"},
    "maxi zoo": {"logo": "🔵", "color": "#0060a9", "full_name": "Maxi Zoo"},
}

# Parole chiave per riconoscere prodotti birra
BEER_KEYWORDS = [
    "birra", "beer", "lager", "ale", "ipa", "weiss", "bock", "pils", "pilsner",
    "stout", "porter", "radler", "shandy", "corona", "heineken", "peroni",
    "moretti", "nastro azzurro", "ichnusa", "dreher", "beck", "carlsberg",
    "stella artois", "tuborg", "leffe", "hoegaarden", "desperados", "tennent",
    "menabrea", "forst", "tourtel", "amstel", "budweiser", "ceres", "grolsch",
    "spaten", "paulaner", "erdinger", "franziskaner", "warsteiner",
]

# ── Lookup volume singolo (litri) per brand/SKU birra italiani noti ──
# Usato quando il titolo NON contiene un formato esplicito né una parola-contenitore.
# Chiave = sottostringa cercata nel titolo (lowercase); la chiave più lunga vince.
BEER_VOLUME_LOOKUP = {
    # Lattine / bottigliette standard 33cl
    "ceres": 0.33, "corona": 0.33, "desperados": 0.33,
    "leffe": 0.33, "hoegaarden": 0.33, "chouffe": 0.33, "duvel": 0.33,
    "bud": 0.33, "budweiser": 0.33,
    # 50cl
    "ichnusa": 0.50, "messina": 0.50, "kozel": 0.50, "warsteiner": 0.50,
    "paulaner": 0.50, "erdinger": 0.50, "franziskaner": 0.50,
    "weihenstephan": 0.50, "kaiserdom": 0.50,
    "8.6": 0.50, "8,6": 0.50, "86 original": 0.50,
    "guinness": 0.44,
    # Bottiglia 66cl (formato volantino tipico al pezzo)
    "nastro azzurro": 0.66, "peroni": 0.66, "moretti": 0.66,
    "menabrea": 0.66, "forst": 0.66, "raffo": 0.66, "dreher": 0.66,
    "heineken": 0.66, "tuborg": 0.66, "bavaria": 0.66,
    "angelo poretti": 0.66, "castello": 0.66,
}

# Parole-contenitore nel titolo → volume singolo di default (litri)
CONTAINER_DEFAULTS = [
    (r'\blattin', 0.33),     # lattina / lattine → 33cl
    (r'\bcan\b', 0.33),
    (r'\bbottigli', 0.66),   # bottiglia / bottiglie → 66cl
    (r'\bfusto\b', 5.0),     # fusto → 5L
    (r'\bkeg\b', 5.0),
]

# Default generico: se è chiaramente una birra ma manca ogni altro segnale,
# si assume il formato bottiglia 66cl, il più comune nei volantini italiani.
GENERIC_BEER_DEFAULT = 0.66

# Lista di user-agent reali da ruotare per sembrare un browser normale
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

# Header HTTP di base per le richieste
# ATTENZIONE: Accept-Encoding va omesso — se impostato manualmente httpx non decomprime
# automaticamente la risposta gzip, e BeautifulSoup riceve dati binari illeggibili
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "DNT": "1",
}


def get_headers() -> dict:
    """Restituisce gli header con un user-agent casuale (evita blocchi anti-bot)."""
    h = HEADERS.copy()
    h["User-Agent"] = random.choice(USER_AGENTS)
    return h


def is_beer(text: str) -> bool:
    """Controlla se il testo del prodotto riguarda la birra."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in BEER_KEYWORDS)


def extract_price(text: str) -> Optional[float]:
    """Estrae il prezzo da una stringa (es. '4,99 €' → 4.99)."""
    match = re.search(r"(\d+[,\.]\d{2})", text)
    if match:
        return float(match.group(1).replace(",", "."))
    match = re.search(r"(\d+)\s*€", text)
    if match:
        return float(match.group(1))
    return None


def _liters_from_explicit_format(n: str) -> Optional[float]:
    """Estrae i litri da un formato VOLUME ESPLICITO nel testo
    (NxVOL, VOL cl/ml/l/lt). Restituisce None se nessun formato esplicito."""
    # N x VOL cl  →  es. "6x33cl", "24 x 33 cl"
    m = re.search(r'(\d+)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*cl\b', n)
    if m:
        return int(m.group(1)) * float(m.group(2).replace(',', '.')) / 100
    # N x VOL ml  →  es. "6x330ml"
    m = re.search(r'(\d+)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*ml\b', n)
    if m:
        return int(m.group(1)) * float(m.group(2).replace(',', '.')) / 1000
    # N x VOL l/lt  →  es. "4x1l", "6x0.5lt"
    m = re.search(r'(\d+)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*l(?:t)?\b', n)
    if m:
        return int(m.group(1)) * float(m.group(2).replace(',', '.'))
    # VOL cl singolo  →  es. "66cl", "33cl"
    m = re.search(r'\b(\d+(?:[.,]\d+)?)\s*cl\b', n)
    if m:
        return float(m.group(1).replace(',', '.')) / 100
    # VOL ml singolo  →  es. "330ml", "500ml"
    m = re.search(r'\b(\d+(?:[.,]\d+)?)\s*ml\b', n)
    if m:
        return float(m.group(1).replace(',', '.')) / 1000
    # VOL l/lt singolo  →  es. "1l", "1.5l", "2lt"
    m = re.search(r'\b(\d+(?:[.,]\d+)?)\s*l(?:t)?\b', n)
    if m:
        v = float(m.group(1).replace(',', '.'))
        if 0.1 <= v <= 50:
            return v
    return None


def infer_liters(name: str) -> Optional[float]:
    """Inferisce il volume (litri) di un'offerta birra dal nome.
    Priorità: 1) formato esplicito, 2) parola-contenitore, 3) lookup brand,
    4) default generico birra (bottiglia 66cl). Restituisce litri o None.
    Necessario perché promoqui.it espone titoli senza formato (es. 'Peroni - Birra')."""
    if not name:
        return None
    n = name.lower()

    # 1) Formato esplicito nel titolo (es. "6x33cl", "66cl", "1,5l")
    liters = _liters_from_explicit_format(n)
    if liters:
        return liters

    # 2) Parola-contenitore (lattina / bottiglia / fusto)
    for pat, vol in CONTAINER_DEFAULTS:
        if re.search(pat, n):
            return vol

    # 3) Lookup brand/SKU noto (la sottostringa più lunga vince)
    best = None
    for key, vol in BEER_VOLUME_LOOKUP.items():
        if key in n and (best is None or len(key) > best[0]):
            best = (len(key), vol)
    if best:
        return best[1]

    # 4) Default generico: birra senza altro segnale → bottiglia 66cl
    if is_beer(n):
        return GENERIC_BEER_DEFAULT

    return None


def calc_price_per_liter(name: str, price: float) -> Optional[float]:
    """Calcola il prezzo al litro dell'offerta.
    Estrae il volume dal nome (formato esplicito, contenitore, brand noto,
    o default birra) e divide il prezzo per i litri. Restituisce €/L o None.
    NB: il prezzo promoqui è quasi sempre per singolo pezzo; il sanity-cap
    scarta i casi in cui un prezzo multipack senza token formato sfori il range."""
    if not name or not price:
        return None
    liters = infer_liters(name)
    if liters and liters > 0:
        ppl = round(price / liters, 2)
        # Sanity check: birra italiana tipicamente 0.30–20 €/L
        if 0.30 <= ppl <= 20:
            return ppl
    return None


def get_supermarket_meta(name: str) -> dict:
    """Restituisce logo, colore e nome completo per un supermercato noto."""
    name_lower = name.lower()
    for key, meta in SUPERMARKET_META.items():
        if key in name_lower:
            return meta
    return {"logo": "🏪", "color": "#6b7280", "full_name": name.title()}


def calc_discount(original: float, sale: float) -> int:
    """Calcola la percentuale di sconto tra prezzo originale e prezzo scontato."""
    if original and sale and original > sale:
        return int(round((1 - sale / original) * 100))
    return 0


# ============================================================
# HELPER: estrazione JSON da pagine Next.js
# ============================================================

def _find_offer_objects(node, results=None) -> list:
    """Visita ricorsivamente il JSON e raccoglie oggetti che sembrano offerte
    (hanno almeno 'title' stringa e 'price' numero positivo)."""
    if results is None:
        results = []
    if isinstance(node, dict):
        if (isinstance(node.get("title"), str) and
                isinstance(node.get("price"), (int, float)) and
                node.get("price", 0) > 0):
            results.append(node)
        else:
            for v in node.values():
                _find_offer_objects(v, results)
    elif isinstance(node, list):
        for item in node:
            _find_offer_objects(item, results)
    return results


def _retailer_from_url(url_path: str) -> str:
    """Estrae il nome del supermercato dall'URL /volantino/{retailer}/..."""
    parts = [p for p in url_path.split("/") if p]
    if len(parts) >= 2 and parts[0] in ("volantino", "flyer", "catalogo"):
        return parts[1].replace("-", " ").title()
    return ""


def _promoqui_image(image_path: str) -> str:
    """Costruisce URL immagine completo da path relativo promoqui/shopfully."""
    if not image_path:
        return ""
    # Sostituisce il placeholder :FORMAT con dimensione concreta
    path = image_path.replace(":FORMAT_webp", "300").replace(":FORMAT", "300")
    if path.startswith("http"):
        return path
    # Base CDN di Shopfully (backend di promoqui.it)
    return f"https://img.promoqui.it/{path.lstrip('/')}"


def _extract_next_data(html: str) -> list:
    """Estrae oggetti offerta da __NEXT_DATA__ (script tag Next.js)."""
    m = re.search(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return []
    try:
        data = _json.loads(m.group(1))
        return _find_offer_objects(data)
    except Exception:
        return []


def _extract_inline_json_offers(html: str) -> list:
    """Fallback: cerca pattern JSON inline con campi title+price (senza __NEXT_DATA__)."""
    results = []
    # Cerca blocchi JSON abbastanza grandi da contenere un'offerta
    for raw in re.findall(r'\{[^<>]{40,800}\}', html):
        if '"title"' not in raw or '"price"' not in raw:
            continue
        try:
            obj = _json.loads(raw)
            if (isinstance(obj.get("title"), str) and
                    isinstance(obj.get("price"), (int, float)) and
                    obj["price"] > 0):
                results.append(obj)
        except Exception:
            pass
    return results


# ============================================================
# SORGENTE 1: promoqui.it (metodo primario: JSON embedded)
# ============================================================
async def scrape_promoqui(client: httpx.AsyncClient, zone: str) -> list:
    """Scrapa offerte birra da promoqui.it.
    Usa __NEXT_DATA__ JSON come metodo primario (più stabile dei selettori CSS),
    con fallback sui selettori BeautifulSoup se il JSON non è disponibile."""
    offers = []
    url = "https://www.promoqui.it/offerte/birra/"
    try:
        resp = await client.get(url, headers=get_headers(), timeout=20, follow_redirects=True)
        if resp.status_code != 200:
            await log_scrape(zone, "promoqui", "error", 0, f"HTTP {resp.status_code}")
            return []

        html = resp.text

        # ── Costruisce mappa titolo→img_url dalle img reali nell'HTML ──
        # Le img tags hanno già URL assoluti funzionanti; il JSON ha path relativi
        # con placeholder :FORMAT che richiedono il CDN corretto (ignoto).
        # Usare le img dall'HTML è più affidabile.
        soup_for_imgs = BeautifulSoup(html, "lxml")
        title_to_img: dict = {}
        for img in soup_for_imgs.find_all("img", src=True):
            src = img.get("src", "")
            if not src.startswith("http"):
                continue
            # Cerca il titolo nel contenitore più vicino (fino a 6 livelli su)
            node = img.parent
            for _ in range(6):
                if not node:
                    break
                title_el = node.find(lambda t: t.name and any(
                    "__title" in c or "title" in c.lower() for c in t.get("class", [])))
                if title_el:
                    key = title_el.get_text(strip=True).lower()
                    if key and key not in title_to_img:
                        title_to_img[key] = src
                    break
                node = node.parent

        # ── Metodo 1: __NEXT_DATA__ (Next.js embeds tutti i dati iniziali qui) ──
        json_items = _extract_next_data(html)

        # ── Metodo 2: JSON inline nel testo (fallback se __NEXT_DATA__ assente) ──
        if not json_items:
            json_items = _extract_inline_json_offers(html)

        if json_items:
            seen_ids = set()
            for item in json_items:
                title = item.get("title", "").strip()
                if not title or not is_beer(title):
                    continue

                sale_price = item.get("price")
                if not isinstance(sale_price, (int, float)) or sale_price <= 0:
                    continue

                # Evita duplicati dallo stesso ID offerta
                offer_id = item.get("id") or hash(title + str(sale_price))
                if offer_id in seen_ids:
                    continue
                seen_ids.add(offer_id)

                original_price = item.get("original_price") or item.get("originalPrice")
                if original_price and not isinstance(original_price, (int, float)):
                    original_price = None

                discount_pct = calc_discount(original_price, sale_price) if original_price else 0

                # Supermercato: dall'URL dell'offerta o da campo "retailer"
                item_url = item.get("url", "")
                supermarket = _retailer_from_url(item_url)
                if not supermarket:
                    retailer = item.get("retailer", {})
                    if isinstance(retailer, dict):
                        supermarket = retailer.get("name", "") or retailer.get("title", "")
                    elif isinstance(retailer, str):
                        supermarket = retailer
                if not supermarket:
                    supermarket = item.get("shop", "") or item.get("chain", "") or "Supermercato"

                # Immagine: usa prima la mappa HTML (URL assoluti certi),
                # poi prova a costruire l'URL dal path JSON come fallback
                img_url = title_to_img.get(title.lower(), "")
                if not img_url:
                    img_url = _promoqui_image(item.get("image", "") or item.get("imageUrl", ""))

                link_url = ""
                if item_url.startswith("/"):
                    link_url = f"https://www.promoqui.it{item_url}"
                elif item_url.startswith("http"):
                    link_url = item_url

                validity = item.get("validity") or item.get("validUntil") or item.get("end_date") or ""
                if validity and len(str(validity)) > 20:
                    validity = ""  # scarta timestamp troppo lunghi

                offers.append({
                    "id": f"promoqui_{offer_id}",
                    "name": title,
                    "supermarket": supermarket,
                    "supermarket_meta": get_supermarket_meta(supermarket),
                    "sale_price": float(sale_price),
                    "original_price": float(original_price) if original_price else None,
                    "discount_pct": discount_pct,
                    "on_sale": discount_pct > 0,
                    "image_url": img_url,
                    "validity": str(validity) if validity else "",
                    "link_url": link_url,
                    "price_per_liter": calc_price_per_liter(title, float(sale_price)),
                    "source": "promoqui.it",
                    "zone": zone,
                })

        # ── Metodo 3: CSS selectors BeautifulSoup (fallback finale) ──
        if not offers:
            soup = BeautifulSoup(html, "lxml")

            def has_offer_root(tag):
                return tag.name and any(
                    "OffersList_offer__" in c and "image" not in c and "information" not in c
                    and "title" not in c and "text" not in c
                    for c in tag.get("class", [])
                ) and tag.find("img")

            for card in soup.find_all(has_offer_root):
                title_el = card.find(lambda t: t.name and any("__title" in c for c in t.get("class", [])))
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                img_el = card.find("img", src=True)
                img_url = img_el["src"] if img_el else ""

                link_el = card.find("a", href=True)
                link_url = ""
                if link_el:
                    href = link_el["href"]
                    link_url = href if href.startswith("http") else f"https://www.promoqui.it{href}"

                price_label = card.find(lambda t: t.name and any(
                    "PriceLabel_price-label__" in c for c in t.get("class", [])))
                sale_price = None
                if price_label:
                    m2 = re.search(r"(\d+[,\.]\d+)", price_label.get_text(strip=True))
                    if m2:
                        try:
                            sale_price = float(m2.group(1).replace(",", "."))
                        except ValueError:
                            pass
                if not sale_price:
                    continue

                discount_el = card.find(lambda t: t.name and any("__discount" in c for c in t.get("class", [])))
                discount_pct = 0
                if discount_el:
                    m2 = re.search(r"(\d+)", discount_el.get_text(strip=True))
                    if m2:
                        discount_pct = int(m2.group(1))

                original_price = round(sale_price / (1 - discount_pct / 100), 2) if discount_pct > 0 else None
                retailer_el = card.find(lambda t: t.name and any("__retailer" in c for c in t.get("class", [])))
                supermarket = retailer_el.get_text(strip=True) if retailer_el else "Supermercato"

                offers.append({
                    "id": f"promoqui_{hash(title + supermarket)}",
                    "name": title,
                    "supermarket": supermarket,
                    "supermarket_meta": get_supermarket_meta(supermarket),
                    "sale_price": sale_price,
                    "original_price": original_price,
                    "discount_pct": discount_pct,
                    "on_sale": discount_pct > 0,
                    "image_url": img_url,
                    "validity": "",
                    "link_url": link_url,
                    "price_per_liter": calc_price_per_liter(title, float(sale_price)),
                    "source": "promoqui.it",
                    "zone": zone,
                })

        await log_scrape(zone, "promoqui", "ok", len(offers))

    except Exception as e:
        await log_scrape(zone, "promoqui", "error", 0, str(e))

    return offers


# ============================================================
# SORGENTE 2: tiendeo.it (__NEXT_DATA__ JSON)
# ============================================================
async def scrape_tiendeo(client: httpx.AsyncClient, zone: str) -> list:
    """Scrapa offerte birra da tiendeo.it usando __NEXT_DATA__ embedded nell'HTML.
    Tiendeo è un aggregatore internazionale di volantini supermercati, presente in Italia.
    I prodotti vivono in apiResources.offersTable.flyerGibs e apiResources.flyerGibsData.flyerGibs:
    ogni 'flyerGib' ha title, retailerName, image e settings.{price, starting_price, sale} con
    prezzi come STRINGHE (es. '€ 1.09') — per questo il vecchio parser title+price numerico falliva."""
    offers = []

    def _price(d) -> float:
        # Estrae un float da settings.price_extended/starting_price ('digits' è una stringa)
        if isinstance(d, dict):
            digits = d.get("digits")
            if isinstance(digits, str) and digits.strip():
                try:
                    return float(digits.replace(",", "."))
                except ValueError:
                    pass
        return 0.0

    # URL corretto: la vecchia /ricerca?query= redirige alla home, /cat e /Modena danno 404.
    # /Offerte/birra è la pagina categoria-prodotto nazionale (pageType PRODUCTCATEGORY_NATIONAL).
    urls_to_try = [
        "https://www.tiendeo.it/Offerte/birra",
        "https://www.tiendeo.it/search?q=birra",
    ]
    try:
        seen_ids = set()
        for url in urls_to_try:
            try:
                resp = await client.get(url, headers=get_headers(), timeout=15, follow_redirects=True)
            except Exception:
                continue
            if resp.status_code != 200:
                continue

            html = resp.text
            m = re.search(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html, re.DOTALL)
            if not m:
                continue
            try:
                data = _json.loads(m.group(1))
            except Exception:
                continue

            api = (data.get("props", {}) or {}).get("pageProps", {}).get("apiResources", {}) or {}
            gibs = []
            for container in ("offersTable", "flyerGibsData"):
                block = api.get(container)
                if isinstance(block, dict) and isinstance(block.get("flyerGibs"), list):
                    gibs.extend(block["flyerGibs"])

            for item in gibs:
                if not isinstance(item, dict):
                    continue
                title = (item.get("title") or "").strip()
                if not title or not is_beer(title):
                    continue

                settings = item.get("settings", {})
                if not isinstance(settings, dict):
                    settings = {}

                sale_price = _price(settings.get("price_extended"))
                if sale_price <= 0:
                    continue

                original_price = _price(settings.get("starting_price"))
                if original_price <= sale_price:
                    original_price = None

                # Sconto: usa il campo 'discount' (negativo, es. -30) o calcola dai prezzi
                discount_pct = 0
                raw_disc = item.get("discount")
                if isinstance(raw_disc, (int, float)) and raw_disc:
                    discount_pct = abs(int(raw_disc))
                elif original_price:
                    discount_pct = calc_discount(original_price, sale_price)
                # Ricostruisci l'originale se manca starting_price ma c'è uno sconto
                if original_price is None and discount_pct > 0:
                    original_price = round(sale_price / (1 - discount_pct / 100), 2)

                offer_id = item.get("id") or hash(title + str(sale_price))
                if offer_id in seen_ids:
                    continue
                seen_ids.add(offer_id)

                supermarket = (item.get("retailerName") or settings.get("brand") or "Supermercato").strip()

                img_url = item.get("image") or settings.get("image_url") or item.get("retailerLogo") or ""
                if isinstance(img_url, str) and img_url and not img_url.startswith("http"):
                    img_url = f"https://www.tiendeo.it{img_url}"
                else:
                    img_url = img_url if isinstance(img_url, str) else ""

                item_url = item.get("href") or ""
                link_url = ""
                if isinstance(item_url, str) and item_url:
                    link_url = item_url if item_url.startswith("http") else f"https://www.tiendeo.it{item_url}"

                # Validità dalla data di fine del volantino
                validity = ""
                flyer = item.get("flyer", {})
                if isinstance(flyer, dict) and flyer.get("end_date"):
                    validity = f"Fino al {flyer['end_date']}"

                offers.append({
                    "id": f"tiendeo_{offer_id}",
                    "name": title,
                    "supermarket": supermarket,
                    "supermarket_meta": get_supermarket_meta(supermarket),
                    "sale_price": float(sale_price),
                    "original_price": float(original_price) if original_price else None,
                    "discount_pct": discount_pct,
                    "on_sale": discount_pct > 0,
                    "image_url": img_url,
                    "validity": validity,
                    "link_url": link_url,
                    "price_per_liter": calc_price_per_liter(title, float(sale_price)),
                    "source": "tiendeo.it",
                    "zone": zone,
                })

            if offers:
                break  # se un URL ha funzionato, non proviamo gli altri

        await log_scrape(zone, "tiendeo", "ok", len(offers))

    except Exception as e:
        try:
            await log_scrape(zone, "tiendeo", "error", 0, str(e))
        except Exception:
            pass
    return offers


# ============================================================
# SORGENTE 3: volantino.it  — DISMESSA (dominio ora print-shop SumUp, niente volantini)
# Funzione mantenuta come riferimento ma NON più chiamata da scrape_all().
# ============================================================
async def scrape_volantino(client: httpx.AsyncClient, zone: str) -> list:
    """Scrapa offerte birra da volantino.it, prima con __NEXT_DATA__ poi con CSS."""
    offers = []
    url = f"https://www.volantino.it/cerca/?q=birra&comune={zone}"
    try:
        resp = await client.get(url, headers=get_headers(), timeout=15, follow_redirects=True)
        if resp.status_code != 200:
            return []

        html = resp.text

        # Prova prima JSON embedded
        json_items = _extract_next_data(html)
        if json_items:
            for item in json_items:
                title = (item.get("title") or item.get("name") or "").strip()
                if not title or not is_beer(title):
                    continue
                sale_price = item.get("price") or item.get("salePrice")
                if not isinstance(sale_price, (int, float)) or sale_price <= 0:
                    continue
                original_price = item.get("original_price") or item.get("originalPrice")
                if original_price and not isinstance(original_price, (int, float)):
                    original_price = None
                discount_pct = calc_discount(original_price, sale_price) if original_price else 0
                supermarket = ""
                for field in ("retailer", "shop", "store", "brand"):
                    v = item.get(field, "")
                    supermarket = (v.get("name", "") if isinstance(v, dict) else str(v)).strip()
                    if supermarket:
                        break
                supermarket = supermarket or "Supermercato"
                img_url = item.get("image", "") or item.get("imageUrl", "")
                item_url = item.get("url", "")
                link_url = item_url if item_url.startswith("http") else f"https://www.volantino.it{item_url}"
                offers.append({
                    "id": f"volantino_{item.get('id', hash(title + supermarket))}",
                    "name": title, "supermarket": supermarket,
                    "supermarket_meta": get_supermarket_meta(supermarket),
                    "sale_price": float(sale_price),
                    "original_price": float(original_price) if original_price else None,
                    "discount_pct": discount_pct, "on_sale": discount_pct > 0,
                    "image_url": img_url, "validity": "",
                    "link_url": link_url, "price_per_liter": calc_price_per_liter(title, sale_price), "source": "volantino.it", "zone": zone,
                })

        # Fallback CSS
        if not offers:
            soup = BeautifulSoup(html, "lxml")
            cards = soup.select(".product, .offerta, .promo-item, [class*='product'], [class*='offer']")
            for card in cards:
                title_el = card.select_one("h2, h3, .name, .title, p strong")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not is_beer(title):
                    continue
                price_text = card.get_text(" ", strip=True)
                prices = re.findall(r"(\d+[,\.]\d{2})\s*€?", price_text)
                price_vals = sorted([float(p.replace(",", ".")) for p in prices
                                     if 0.5 < float(p.replace(",", ".")) < 100])
                sale_price = price_vals[0] if price_vals else None
                orig_price = price_vals[1] if len(price_vals) > 1 else None
                if not sale_price:
                    continue
                store_el = card.select_one(".store, .market, .supermarket, .brand")
                supermarket = store_el.get_text(strip=True) if store_el else "Supermercato"
                img = card.select_one("img")
                img_url = img.get("src", "") or img.get("data-src", "") if img else ""
                link_el = card.select_one("a[href]")
                link_url = ""
                if link_el:
                    href = link_el.get("href", "")
                    link_url = href if href.startswith("http") else f"https://www.volantino.it{href}"
                offers.append({
                    "id": f"volantino_{hash(title + supermarket)}",
                    "name": title, "supermarket": supermarket,
                    "supermarket_meta": get_supermarket_meta(supermarket),
                    "sale_price": sale_price, "original_price": orig_price,
                    "discount_pct": calc_discount(orig_price, sale_price),
                    "on_sale": bool(orig_price and orig_price > sale_price),
                    "image_url": img_url, "validity": "",
                    "link_url": link_url, "price_per_liter": calc_price_per_liter(title, sale_price), "source": "volantino.it", "zone": zone,
                })

        await log_scrape(zone, "volantino", "ok", len(offers))

    except Exception as e:
        await log_scrape(zone, "volantino", "error", 0, str(e))

    return offers


# ============================================================
# SORGENTE 4: offerte.it  — DISMESSA (dominio parcheggiato in vendita su Sedo)
# Funzione mantenuta come riferimento ma NON più chiamata da scrape_all().
# ============================================================
async def scrape_offerte(client: httpx.AsyncClient, zone: str) -> list:
    """Scrapa offerte birra da offerte.it, prima con __NEXT_DATA__ poi con CSS."""
    offers = []
    url = f"https://www.offerte.it/cerca/birra/{zone}/"
    try:
        resp = await client.get(url, headers=get_headers(), timeout=15, follow_redirects=True)
        if resp.status_code != 200:
            return []

        html = resp.text
        json_items = _extract_next_data(html)

        if json_items:
            for item in json_items:
                title = (item.get("title") or item.get("name") or "").strip()
                if not title or not is_beer(title):
                    continue
                sale_price = item.get("price") or item.get("salePrice")
                if not isinstance(sale_price, (int, float)) or sale_price <= 0:
                    continue
                original_price = item.get("original_price") or item.get("originalPrice")
                if original_price and not isinstance(original_price, (int, float)):
                    original_price = None
                discount_pct = calc_discount(original_price, sale_price) if original_price else 0
                supermarket = ""
                for field in ("retailer", "shop", "store"):
                    v = item.get(field, "")
                    supermarket = (v.get("name", "") if isinstance(v, dict) else str(v)).strip()
                    if supermarket:
                        break
                supermarket = supermarket or "Supermercato"
                img_url = item.get("image", "") or ""
                item_url = item.get("url", "")
                link_url = item_url if item_url.startswith("http") else f"https://www.offerte.it{item_url}"
                offers.append({
                    "id": f"offerte_{item.get('id', hash(title + supermarket))}",
                    "name": title, "supermarket": supermarket,
                    "supermarket_meta": get_supermarket_meta(supermarket),
                    "sale_price": float(sale_price),
                    "original_price": float(original_price) if original_price else None,
                    "discount_pct": discount_pct, "on_sale": discount_pct > 0,
                    "image_url": img_url, "validity": "",
                    "link_url": link_url, "price_per_liter": calc_price_per_liter(title, sale_price), "source": "offerte.it", "zone": zone,
                })
        else:
            # Fallback CSS
            soup = BeautifulSoup(html, "lxml")
            cards = soup.select(".product-item, .offer-item, article, .promo")
            for card in cards:
                title_el = card.select_one("h2, h3, .product-title, .name")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not is_beer(title):
                    continue
                price_text = card.get_text(" ", strip=True)
                prices = re.findall(r"(\d+[,\.]\d{2})\s*€?", price_text)
                price_vals = sorted([float(p.replace(",", ".")) for p in prices
                                     if 0.5 < float(p.replace(",", ".")) < 100])
                sale_price = price_vals[0] if price_vals else None
                if not sale_price:
                    continue
                orig_price = price_vals[1] if len(price_vals) > 1 else None
                store_el = card.select_one(".store, .retailer, .chain")
                supermarket = store_el.get_text(strip=True) if store_el else "Supermercato"
                img = card.select_one("img")
                img_url = img.get("src", "") or img.get("data-src", "") if img else ""
                link_el = card.select_one("a[href]")
                link_url = ""
                if link_el:
                    href = link_el.get("href", "")
                    link_url = href if href.startswith("http") else f"https://www.offerte.it{href}"
                offers.append({
                    "id": f"offerte_{hash(title + supermarket)}",
                    "name": title, "supermarket": supermarket,
                    "supermarket_meta": get_supermarket_meta(supermarket),
                    "sale_price": sale_price, "original_price": orig_price,
                    "discount_pct": calc_discount(orig_price, sale_price),
                    "on_sale": bool(orig_price and orig_price > sale_price),
                    "image_url": img_url, "validity": "",
                    "link_url": link_url, "price_per_liter": calc_price_per_liter(title, sale_price), "source": "offerte.it", "zone": zone,
                })

        await log_scrape(zone, "offerte", "ok", len(offers))

    except Exception as e:
        await log_scrape(zone, "offerte", "error", 0, str(e))

    return offers


# ============================================================
# DEMO DATA (fallback se nessuna fonte risponde)
# ============================================================
def get_demo_data(zone: str) -> list:
    """Dati di esempio usati come fallback quando tutte le fonti sono irraggiungibili."""
    beers = [
        {"name": "Birra Moretti 6x33cl", "supermarket": "Esselunga", "sale_price": 4.49, "original_price": 5.99, "on_sale": True},
        {"name": "Heineken 24x33cl", "supermarket": "Conad", "sale_price": 14.99, "original_price": 19.99, "on_sale": True},
        {"name": "Peroni Nastro Azzurro 6x66cl", "supermarket": "Carrefour", "sale_price": 6.29, "original_price": 7.49, "on_sale": True},
        {"name": "Corona Extra 6x35cl", "supermarket": "Esselunga", "sale_price": 7.99, "original_price": 9.49, "on_sale": True},
        {"name": "Carlsberg 12x33cl", "supermarket": "Lidl", "sale_price": 8.99, "original_price": None, "on_sale": False},
        {"name": "Birra Ichnusa Non Filtrata 4x50cl", "supermarket": "Coop", "sale_price": 5.49, "original_price": 6.99, "on_sale": True},
        {"name": "Dreher 6x33cl", "supermarket": "Eurospin", "sale_price": 2.99, "original_price": None, "on_sale": False},
        {"name": "Birra Moretti Baffo d'Oro 6x33cl", "supermarket": "Iper", "sale_price": 5.99, "original_price": 7.49, "on_sale": True},
        {"name": "Leffe Blonde 6x33cl", "supermarket": "Conad", "sale_price": 6.99, "original_price": 8.49, "on_sale": True},
        {"name": "Beck's 8x33cl", "supermarket": "Carrefour", "sale_price": 5.49, "original_price": 6.99, "on_sale": True},
        {"name": "Stella Artois 6x33cl", "supermarket": "Esselunga", "sale_price": 5.29, "original_price": None, "on_sale": False},
        {"name": "Desperados 6x33cl", "supermarket": "Conad", "sale_price": 5.99, "original_price": 7.29, "on_sale": True},
        {"name": "Tuborg Green 24x33cl", "supermarket": "Lidl", "sale_price": 13.99, "original_price": 17.99, "on_sale": True},
        {"name": "Hoegaarden 6x33cl", "supermarket": "Esselunga", "sale_price": 7.49, "original_price": 8.99, "on_sale": True},
        {"name": "Tennent's Lager 24x33cl", "supermarket": "Carrefour", "sale_price": 15.99, "original_price": 19.99, "on_sale": True},
        {"name": "Guinness Draught 4x50cl", "supermarket": "Conad", "sale_price": 6.29, "original_price": 7.49, "on_sale": True},
    ]
    result = []
    for i, b in enumerate(beers):
        disc = calc_discount(b["original_price"], b["sale_price"])
        result.append({
            "id": f"demo_{i}", "name": b["name"], "supermarket": b["supermarket"],
            "supermarket_meta": get_supermarket_meta(b["supermarket"]),
            "sale_price": b["sale_price"], "original_price": b["original_price"],
            "discount_pct": disc, "on_sale": b["on_sale"],
            "image_url": "", "validity": "Fino a domenica",
            "link_url": "", "price_per_liter": calc_price_per_liter(b["name"], b["sale_price"]), "source": "demo", "zone": zone,
        })
    return result


# ============================================================
# ENTRY POINT PRINCIPALE
# ============================================================
async def scrape_all(zone: str) -> list:
    """Scrapa tutte le fonti in parallelo e unifica i risultati.
    Se nessuna fonte restituisce dati reali, usa il fallback demo."""
    async with httpx.AsyncClient(
        limits=httpx.Limits(max_connections=8),
        timeout=httpx.Timeout(20.0)
    ) as client:
        # NB: volantino.it e offerte.it rimossi — domini non più attivi come aggregatori
        # volantini (volantino.it = print-shop SumUp, offerte.it = dominio parcheggiato su Sedo).
        # Fonti attive: promoqui.it + tiendeo.it. Le funzioni dismesse restano sotto come riferimento.
        results = await asyncio.gather(
            scrape_promoqui(client, zone),
            scrape_tiendeo(client, zone),
            return_exceptions=True
        )

    # Raccoglie solo risultati validi (scarta eccezioni)
    all_offers = []
    for r in results:
        if isinstance(r, list):
            all_offers.extend(r)

    # Deduplica: stessa birra nello stesso supermercato conta una volta sola
    seen = set()
    unique = []
    for offer in all_offers:
        key = f"{offer['name'].lower()[:35]}_{offer['supermarket'].lower()}"
        if key not in seen:
            seen.add(key)
            unique.append(offer)

    # Se tutto fallisce usa dati demo
    if not unique:
        unique = get_demo_data(zone)

    # Rimuovi supermercati esclusi — controllo sottostringa (cattura anche "Bennet Italia" ecc.)
    ESCLUSI = ["bennet"]
    unique = [o for o in unique if not any(e in o["supermarket"].lower() for e in ESCLUSI)]

    # Ordina: prima le offerte in sconto, poi per % sconto decrescente, poi prezzo
    unique.sort(key=lambda x: (-x["on_sale"], -x["discount_pct"], x["sale_price"]))

    return unique
