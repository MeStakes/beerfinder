"""
BeerFinder API - FastAPI backend
Endpoint REST per scraping offerte birra + serving frontend.
"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import time

from database import init_db, get_cached_offers, save_offers, get_cache_info
from scraper import scrape_all

# Tiene traccia delle zone per cui è in corso uno scraping (evita doppioni)
_scraping_zones: set = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea le tabelle SQLite all'avvio se non esistono
    await init_db()
    yield


app = FastAPI(
    title="BeerFinder API",
    description="Scraper offerte birra supermercati italiani",
    version="1.0.0",
    lifespan=lifespan,
)

# Permette richieste da qualsiasi origine (necessario per il frontend SPA)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supermercati sempre esclusi dai risultati
SUPERMARKET_ESCLUSI = ["bennet"]


# ─── Background task ──────────────────────────────────────────
async def run_scrape(zone: str):
    """Esegue lo scraping in background e salva i risultati nel database."""
    try:
        _scraping_zones.add(zone.lower())
        offers = await scrape_all(zone)
        await save_offers(zone, offers)
    finally:
        # Rimuove la zona dalla lista "in corso" anche in caso di errore
        _scraping_zones.discard(zone.lower())


# ─── API Routes ───────────────────────────────────────────────

@app.get("/api/beers")
async def get_beers(
    zone: str = Query(..., description="Città o CAP da cercare"),
    force_refresh: bool = Query(False, description="Forza nuovo scraping ignorando cache"),
    supermarket: str = Query("", description="Filtra per supermercato"),
    on_sale_only: bool = Query(False, description="Solo prodotti in offerta"),
    min_discount: int = Query(0, ge=0, le=100),
    sort_by: str = Query("discount", description="discount | price_asc | price_desc | name"),
):
    zone_key = zone.strip().lower()
    if not zone_key:
        raise HTTPException(400, "Zona obbligatoria")

    # Usa la cache se non è richiesto un aggiornamento forzato
    cached = None if force_refresh else await get_cached_offers(zone_key)

    if not cached and zone_key not in _scraping_zones:
        # Prima richiesta o force_refresh: scraping sincrono (l'utente aspetta il risultato)
        offers = await scrape_all(zone_key)
        await save_offers(zone_key, offers)
        cached = offers

    elif zone_key in _scraping_zones:
        # Scraping già in corso: usa la cache precedente per non bloccare l'utente
        cached = await get_cached_offers(zone_key) or []

    offers = cached or []

    # ── Supermercati esclusi — doppio filtro sottostringa (anche se il nome varia) ──
    offers = [o for o in offers if not any(e in o["supermarket"].lower() for e in SUPERMARKET_ESCLUSI)]

    # ── Filtri opzionali ──
    if supermarket:
        offers = [o for o in offers if supermarket.lower() in o["supermarket"].lower()]
    if on_sale_only:
        offers = [o for o in offers if o["on_sale"]]
    if min_discount > 0:
        offers = [o for o in offers if o["discount_pct"] >= min_discount]

    # ── Ordinamento ──
    sort_fns = {
        "discount": lambda x: -x["discount_pct"],
        "price_asc": lambda x: x["sale_price"],
        "price_desc": lambda x: -x["sale_price"],
        "name": lambda x: x["name"].lower(),
    }
    offers.sort(key=sort_fns.get(sort_by, sort_fns["discount"]))

    cache_info = await get_cache_info(zone_key)

    return {
        "zone": zone,
        "total": len(offers),
        "scraping": zone_key in _scraping_zones,
        "cache_info": cache_info,
        "offers": offers,
    }


@app.post("/api/refresh")
async def refresh(
    zone: str = Query(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Avvia un nuovo scraping in background per la zona specificata."""
    zone_key = zone.strip().lower()
    if zone_key in _scraping_zones:
        return {"message": "Scraping già in corso", "scraping": True}
    background_tasks.add_task(run_scrape, zone_key)
    return {"message": f"Scraping avviato per {zone}", "scraping": True}


@app.get("/api/stats")
async def stats(zone: str = Query(...)):
    """Statistiche offerte per zona: totale, in offerta, sconto medio, miglior deal."""
    zone_key = zone.strip().lower()
    offers = await get_cached_offers(zone_key) or []
    if not offers:
        return {"zone": zone, "total": 0, "on_sale": 0, "avg_discount": 0, "best_deal": None}

    on_sale = [o for o in offers if o["on_sale"]]
    avg_disc = int(sum(o["discount_pct"] for o in on_sale) / len(on_sale)) if on_sale else 0
    best = max(on_sale, key=lambda x: x["discount_pct"]) if on_sale else None

    # Conta quante offerte ci sono per ogni supermercato
    supermarkets = {}
    for o in offers:
        s = o["supermarket"]
        supermarkets[s] = supermarkets.get(s, 0) + 1

    return {
        "zone": zone,
        "total": len(offers),
        "on_sale": len(on_sale),
        "avg_discount": avg_disc,
        "best_deal": best,
        "supermarkets": supermarkets,
        "scraping": zone_key in _scraping_zones,
    }


@app.get("/api/supermarkets")
async def list_supermarkets(zone: str = Query(...)):
    """Lista supermercati trovati per zona, ordinati per numero di offerte."""
    zone_key = zone.strip().lower()
    offers = await get_cached_offers(zone_key) or []
    markets = {}
    for o in offers:
        s = o["supermarket"]
        if s not in markets:
            markets[s] = {"name": s, "count": 0, "meta": o["supermarket_meta"]}
        markets[s]["count"] += 1
    return sorted(markets.values(), key=lambda x: -x["count"])


@app.get("/api/health")
async def health():
    """Healthcheck — usato da Railway/Render per verificare che il server sia vivo."""
    return {"status": "ok", "timestamp": int(time.time())}


# ─── Serve frontend ───────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Serve la SPA (single-page application) contenuta in static/index.html."""
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
