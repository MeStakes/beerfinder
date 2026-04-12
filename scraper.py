"""
Scraper multi-sorgente per offerte birra nei supermercati italiani.
Fonti: promoqui.it, volantino.it, offerte.it
"""
import httpx
import asyncio
import re
import random
import time
from typing import Optional
from bs4 import BeautifulSoup
from database import log_scrape

# --- Supermercati noti con logo emoji ---
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
    "bennet": {"logo": "🟢", "color": "#009639", "full_name": "Bennet"},
    "sigma": {"logo": "🔴", "color": "#e52330", "full_name": "Sigma"},
    "despar": {"logo": "🟢", "color": "#007a33", "full_name": "Despar"},
    "interspar": {"logo": "🟢", "color": "#007a33", "full_name": "Interspar"},
    "pam": {"logo": "🔴", "color": "#da291c", "full_name": "Pam"},
    "u2": {"logo": "🟠", "color": "#ff6600", "full_name": "U2 Supermercato"},
    "famila": {"logo": "🔵", "color": "#004b87", "full_name": "Famila"},
    "simply": {"logo": "🟢", "color": "#00843d", "full_name": "Simply"},
}

BEER_KEYWORDS = [
    "birra", "beer", "lager", "ale", "ipa", "weiss", "bock", "pils", "pilsner",
    "stout", "porter", "radler", "shandy", "corona", "heineken", "peroni",
    "moretti", "nastro azzurro", "ichnusa", "dreher", "beck", "carlsberg",
    "stella artois", "tuborg", "leffe", "hoegaarden", "desperados", "tennent"
]

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    # Accept-Encoding omesso: httpx non decomprime automaticamente se impostato manualmente
    "Connection": "keep-alive",
    "DNT": "1",
}


def get_headers() -> dict:
    h = HEADERS.copy()
    h["User-Agent"] = random.choice(USER_AGENTS)
    return h


def is_beer(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in BEER_KEYWORDS)


def extract_price(text: str) -> Optional[float]:
    match = re.search(r"(\d+[,\.]\d{2})", text)
    if match:
        return float(match.group(1).replace(",", "."))
    match = re.search(r"(\d+)\s*€", text)
    if match:
        return float(match.group(1))
    return None


def get_supermarket_meta(name: str) -> dict:
    name_lower = name.lower()
    for key, meta in SUPERMARKET_META.items():
        if key in name_lower:
            return meta
    return {"logo": "🏪", "color": "#6b7280", "full_name": name.title()}


def calc_discount(original: float, sale: float) -> int:
    if original and sale and original > sale:
        return int(round((1 - sale / original) * 100))
    return 0


# ============================================================
# SORGENTE 1: promoqui.it
# ============================================================
async def scrape_promoqui(client: httpx.AsyncClient, zone: str) -> list:
    """Scrapa offerte birra da promoqui.it (risultati nazionali)."""
    offers = []
    url = "https://www.promoqui.it/offerte/birra/"
    try:
        resp = await client.get(url, headers=get_headers(), timeout=20, follow_redirects=True)
        if resp.status_code != 200:
            await log_scrape(zone, "promoqui", "error", 0, f"HTTP {resp.status_code}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")

        # Trova le card offerta: usa find_all con filtro classe (più affidabile di select CSS)
        def has_offer_root(tag):
            return tag.name and any(
                "OffersList_offer__" in c and "image" not in c and "information" not in c
                and "title" not in c and "text" not in c
                for c in tag.get("class", [])
            ) and tag.find("img")  # solo card con immagine (esclude wrapper vuoti)

        cards = soup.find_all(has_offer_root)

        for card in cards:
            # Titolo
            title_el = card.find(lambda t: t.name and any("__title" in c for c in t.get("class", [])))
            if not title_el:
                continue
            title = title_el.get_text(strip=True)

            # Immagine
            img_el = card.find("img", src=True)
            img_url = img_el["src"] if img_el else ""

            # Link al volantino (primo link della card)
            link_el = card.find("a", href=True)
            link_url = ""
            if link_el:
                href = link_el["href"]
                link_url = href if href.startswith("http") else f"https://www.promoqui.it{href}"

            # Prezzo: cerchiamo il div PriceLabel e prendiamo il suo testo grezzo
            price_label = card.find(lambda t: t.name and any("PriceLabel_price-label__" in c for c in t.get("class", [])))
            sale_price = None
            if price_label:
                # Il testo del div è tipo "0.99€" — estraiamo il numero
                m = re.search(r"(\d+[,\.]\d+)", price_label.get_text(strip=True))
                if m:
                    try:
                        sale_price = float(m.group(1).replace(",", "."))
                    except ValueError:
                        pass

            if not sale_price:
                continue

            # Percentuale sconto
            discount_el = card.find(lambda t: t.name and any("__discount" in c for c in t.get("class", [])))
            discount_pct = 0
            if discount_el:
                m = re.search(r"(\d+)", discount_el.get_text(strip=True))
                if m:
                    discount_pct = int(m.group(1))

            # Prezzo originale calcolato dallo sconto
            original_price = None
            if discount_pct > 0:
                original_price = round(sale_price / (1 - discount_pct / 100), 2)

            # Supermercato
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
                "source": "promoqui.it",
                "zone": zone,
            })

        await log_scrape(zone, "promoqui", "ok", len(offers))

    except Exception as e:
        await log_scrape(zone, "promoqui", "error", 0, str(e))

    return offers
    return offers


# ============================================================
# SORGENTE 2: volantino.it
# ============================================================
async def scrape_volantino(client: httpx.AsyncClient, zone: str) -> list:
    offers = []
    url = f"https://www.volantino.it/cerca/?q=birra&comune={zone}"
    try:
        resp = await client.get(url, headers=get_headers(), timeout=15, follow_redirects=True)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "lxml")

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
            price_vals = sorted([float(p.replace(",", ".")) for p in prices if 0.5 < float(p.replace(",", ".")) < 100])

            sale_price = price_vals[0] if price_vals else None
            orig_price = price_vals[1] if len(price_vals) > 1 else None

            store_el = card.select_one(".store, .market, .supermarket, .brand")
            supermarket = store_el.get_text(strip=True) if store_el else ""

            img = card.select_one("img")
            img_url = img.get("src", "") or img.get("data-src", "") if img else ""

            link_el = card.select_one("a[href]")
            link_url = ""
            if link_el:
                href = link_el.get("href", "")
                link_url = href if href.startswith("http") else f"https://www.volantino.it{href}"

            if sale_price:
                offers.append({
                    "id": f"volantino_{hash(title + supermarket)}",
                    "name": title,
                    "supermarket": supermarket or "Supermercato",
                    "supermarket_meta": get_supermarket_meta(supermarket),
                    "sale_price": sale_price,
                    "original_price": orig_price,
                    "discount_pct": calc_discount(orig_price, sale_price),
                    "on_sale": bool(orig_price and orig_price > sale_price),
                    "image_url": img_url,
                    "validity": "",
                    "link_url": link_url,
                    "source": "volantino.it",
                    "zone": zone,
                })

        await log_scrape(zone, "volantino", "ok", len(offers))

    except Exception as e:
        await log_scrape(zone, "volantino", "error", 0, str(e))

    return offers


# ============================================================
# SORGENTE 3: offerte.it
# ============================================================
async def scrape_offerte(client: httpx.AsyncClient, zone: str) -> list:
    offers = []
    url = f"https://www.offerte.it/cerca/birra/{zone}/"
    try:
        resp = await client.get(url, headers=get_headers(), timeout=15, follow_redirects=True)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "lxml")

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
            price_vals = sorted([float(p.replace(",", ".")) for p in prices if 0.5 < float(p.replace(",", ".")) < 100])

            sale_price = price_vals[0] if price_vals else None
            orig_price = price_vals[1] if len(price_vals) > 1 else None

            store_el = card.select_one(".store, .retailer, .chain")
            supermarket = store_el.get_text(strip=True) if store_el else ""

            img = card.select_one("img")
            img_url = img.get("src", "") or img.get("data-src", "") if img else ""

            link_el = card.select_one("a[href]")
            link_url = ""
            if link_el:
                href = link_el.get("href", "")
                link_url = href if href.startswith("http") else f"https://www.offerte.it{href}"

            if sale_price:
                offers.append({
                    "id": f"offerte_{hash(title + supermarket)}",
                    "name": title,
                    "supermarket": supermarket or "Supermercato",
                    "supermarket_meta": get_supermarket_meta(supermarket),
                    "sale_price": sale_price,
                    "original_price": orig_price,
                    "discount_pct": calc_discount(orig_price, sale_price),
                    "on_sale": bool(orig_price and orig_price > sale_price),
                    "image_url": img_url,
                    "validity": "",
                    "link_url": link_url,
                    "source": "offerte.it",
                    "zone": zone,
                })

        await log_scrape(zone, "offerte", "ok", len(offers))

    except Exception as e:
        await log_scrape(zone, "offerte", "error", 0, str(e))

    return offers


# ============================================================
# DEMO DATA (fallback se nessuna fonte risponde)
# ============================================================
def get_demo_data(zone: str) -> list:
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
        {"name": "Birra del Borgo ReAle 33cl", "supermarket": "Iper", "sale_price": 2.49, "original_price": 2.99, "on_sale": True},
        {"name": "Desperados 6x33cl", "supermarket": "Conad", "sale_price": 5.99, "original_price": 7.29, "on_sale": True},
        {"name": "Tuborg Green 24x33cl", "supermarket": "Lidl", "sale_price": 13.99, "original_price": 17.99, "on_sale": True},
        {"name": "Birra Raffo 12x33cl", "supermarket": "Penny", "sale_price": 6.49, "original_price": None, "on_sale": False},
        {"name": "Hoegaarden 6x33cl", "supermarket": "Esselunga", "sale_price": 7.49, "original_price": 8.99, "on_sale": True},
        {"name": "Tennent's Lager 24x33cl", "supermarket": "Carrefour", "sale_price": 15.99, "original_price": 19.99, "on_sale": True},
        {"name": "Guinness Draught 4x50cl", "supermarket": "Conad", "sale_price": 6.29, "original_price": 7.49, "on_sale": True},
    ]

    result = []
    for i, b in enumerate(beers):
        disc = calc_discount(b["original_price"], b["sale_price"])
        result.append({
            "id": f"demo_{i}",
            "name": b["name"],
            "supermarket": b["supermarket"],
            "supermarket_meta": get_supermarket_meta(b["supermarket"]),
            "sale_price": b["sale_price"],
            "original_price": b["original_price"],
            "discount_pct": disc,
            "on_sale": b["on_sale"],
            "image_url": "",
            "validity": "Fino a domenica",
            "link_url": "",
            "source": "demo",
            "zone": zone,
        })
    return result


# ============================================================
# ENTRY POINT PRINCIPALE
# ============================================================
async def scrape_all(zone: str) -> list:
    """Scrapa tutte le fonti in parallelo e unifica i risultati."""
    async with httpx.AsyncClient(
        limits=httpx.Limits(max_connections=5),
        timeout=httpx.Timeout(20.0)
    ) as client:
        results = await asyncio.gather(
            scrape_promoqui(client, zone),
            scrape_volantino(client, zone),
            scrape_offerte(client, zone),
            return_exceptions=True
        )

    all_offers = []
    for r in results:
        if isinstance(r, list):
            all_offers.extend(r)

    # Deduplica per nome + supermercato
    seen = set()
    unique = []
    for offer in all_offers:
        key = f"{offer['name'].lower()[:30]}_{offer['supermarket'].lower()}"
        if key not in seen:
            seen.add(key)
            unique.append(offer)

    # Fallback demo se niente trovato
    if not unique:
        unique = get_demo_data(zone)

    # Ordina: prima in offerta, poi per sconto decrescente
    unique.sort(key=lambda x: (-x["on_sale"], -x["discount_pct"], x["sale_price"]))

    return unique
