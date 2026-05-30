# CLAUDE.md — BeerFinder Project Context

> File di contesto per Claude Code. Leggilo prima di modificare qualsiasi file.

---

## Identità del progetto

**BeerFinder** è un'applicazione web full-stack Python che aggrega offerte birra dai supermercati italiani tramite scraping, le memorizza in SQLite e le espone tramite una SPA dark ultra-moderna.

Stack backend: `FastAPI` + `BeautifulSoup4` + `httpx` (async) + `aiosqlite`.
Stack frontend: SPA **React 19 + Vite + TypeScript + Tailwind + shadcn/ui** (in `frontend/`), buildata e servita da FastAPI. Design system dark "Liquid Gold" (oro/ambra su nero espresso, hero 3D + spotlight).

---

## Mappa file — cosa fa cosa

| File | Ruolo | Toccare quando… |
|---|---|---|
| `main.py` | FastAPI app, route API, serve la build React (`frontend/dist`) | aggiungi endpoint, cambi CORS/serving, modifichi cache |
| `scraper.py` | Scraper asincrono multi-sorgente | aggiungi fonti, sistemi parsing HTML, cambi keyword birra |
| `database.py` | CRUD SQLite asincrono + TTL cache + health fonti | cambi TTL, aggiungi tabelle, modifichi schema |
| `frontend/` | **SPA React + Vite + TS + Tailwind + shadcn** | cambi UI, aggiungi componenti/filtri, modifichi grafica |
| `frontend/src/` | Componenti, hook `useBeers`, client API, design system | tutto il lavoro frontend |
| `static/index.html` | Vecchio frontend vanilla (BACKUP, non più servito) | — |
| `requirements.txt` | Dipendenze Python esatte | aggiungi librerie, aggiorni versioni |
| `run.sh` | Avvio locale (build frontend + uvicorn) | cambi porta default o opzioni uvicorn |
| `Dockerfile` | Build produzione (stage Node per frontend + Python) | cambi versioni, dipendenze sistema |
| `docker-compose.yml` | Stack Docker completo | aggiungi servizi (redis, nginx…) |

---

## Convenzioni di codice

- **Lingua commenti:** italiano
- **Lingua variabili/funzioni:** inglese snake_case
- **Async ovunque:** tutte le funzioni I/O sono `async def`; non usare `requests` (usa `httpx`)
- **Nessun ORM:** solo SQL raw con `aiosqlite`
- **Frontend:** React + Vite + TypeScript + Tailwind + shadcn/ui in `frontend/` (build step: `npm run build` → `frontend/dist`, servita da FastAPI). Commenti italiano, identificatori inglese. Il vecchio `static/index.html` (vanilla) è backup, non più servito.
- **Nessun file .env richiesto** per avvio base

---

## Schema dati offerta (canonical)

Ogni oggetto offerta deve avere esattamente questa struttura:

```python
{
    "id": str,                    # "fonte_hash(nome+supermercato)"
    "name": str,                  # nome prodotto come appare nel volantino
    "supermarket": str,           # nome catena (es. "Esselunga")
    "supermarket_meta": {
        "logo": str,              # emoji (es. "🟢")
        "color": str,             # hex CSS (es. "#006b2b")
        "full_name": str,         # nome completo (es. "Esselunga")
    },
    "sale_price": float,          # prezzo attuale (sempre presente)
    "original_price": float|None, # prezzo pieno (None se non in offerta)
    "discount_pct": int,          # 0 se non in offerta
    "on_sale": bool,
    "image_url": str,             # URL assoluto o stringa vuota
    "validity": str,              # es. "Fino a domenica" o ""
    "link_url": str,              # link all'offerta (può essere "")
    "price_per_liter": float|None,# €/L calcolato (None se non inferibile)
    "source": str,                # es. "promoqui.it"
    "zone": str,                  # zona lowercase (es. "milano")
}
```

**Funzioni helper già disponibili in `scraper.py`:**
- `is_beer(text)` → bool — controlla se il testo riguarda birra
- `extract_price(text)` → float|None — estrae prezzo da stringa
- `get_supermarket_meta(name)` → dict — restituisce meta del supermercato
- `calc_discount(original, sale)` → int — calcola % sconto
- `calc_price_per_liter(name, price)` → float|None — €/L (formato esplicito → contenitore → lookup brand → default 0.66L)
- `infer_liters(name)` → float|None — volume in litri inferito dal nome
- `get_demo_data(zone)` → list — dati demo di fallback

---

## API endpoints esistenti

```
GET  /api/beers?zone=...          → offerte con filtri e sort
POST /api/refresh?zone=...        → avvia scraping background
GET  /api/stats?zone=...          → statistiche aggregate
GET  /api/supermarkets?zone=...   → lista supermercati trovati
GET  /api/sources/health?zone=... → stato fonti (da scrape_log): ultimo tentativo/successo per fonte
GET  /api/health                  → healthcheck
GET  /                            → serve la SPA React (frontend/dist), fallback static/index.html
GET  /{path}                      → catch-all SPA (serve asset della build o index.html)
```

Tutti i parametri query sono documentati in `main.py` con `Query(...)`.

---

## Come aggiungere una nuova fonte di scraping

1. In `scraper.py`, crea la funzione:

```python
async def scrape_nomefonte(client: httpx.AsyncClient, zone: str) -> list:
    offers = []
    url = f"https://www.nomefonte.it/cerca/birra/{zone}/"
    try:
        resp = await client.get(url, headers=get_headers(), timeout=15, follow_redirects=True)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        # ... parsing ...
        await log_scrape(zone, "nomefonte", "ok", len(offers))
    except Exception as e:
        await log_scrape(zone, "nomefonte", "error", 0, str(e))
    return offers
```

2. Aggiungila in `scrape_all()`:

```python
results = await asyncio.gather(
    scrape_promoqui(client, zone),
    scrape_tiendeo(client, zone),
    scrape_nomefonte(client, zone),   # ← aggiungi qui
    return_exceptions=True
)
```

> **Fonti attive:** `promoqui.it` + `tiendeo.it`. `volantino.it` e `offerte.it` sono state **rimosse** (domini dismessi: volantino.it ora è un print-shop SumUp, offerte.it è parcheggiato su Sedo). Le loro funzioni restano in `scraper.py` come riferimento ma non sono più chiamate.

---

## Come aggiungere un endpoint API

In `main.py`, segui questo pattern:

```python
@app.get("/api/nuovo-endpoint")
async def nuovo_endpoint(
    zone: str = Query(..., description="Città o CAP"),
    parametro: str = Query("default", description="Descrizione"),
):
    # logica
    return {"data": ...}
```

---

## Comportamento cache

- TTL: **86400 secondi (24 ore)** — definito in `database.py:TTL_SECONDS`
- La cache è per-zona (chiave = `zone.lower()`)
- `force_refresh=true` bypassa la cache ma non la cancella finché non arrivano nuovi dati
- Il fallback demo viene restituito quando tutte le fonti falliscono (rete assente, bot-protection)
- Tabella `scrape_log` tiene traccia di ogni tentativo con status e numero item trovati

---

## Frontend — struttura React in `frontend/`

SPA Vite + React 19 + TypeScript + Tailwind + shadcn/ui. Path alias `@/` → `src/`.
- **Dev:** `npm run dev` (Vite :5173) fa da proxy di `/api` → FastAPI :8000.
- **Prod:** `npm run build` → `frontend/dist`, servita da FastAPI (`/api` relativo, stessa origine).

| File | Ruolo |
|---|---|
| `src/App.tsx` | Layout + orchestrazione (header, hero, stats, filtri, griglia, footer) |
| `src/main.tsx` | Mount React + `<Toaster>` (sonner) |
| `src/hooks/useBeers.ts` | Stato centrale: ricerca, refresh+polling (3s), filtri/ordinamento client-side, stats derivate |
| `src/lib/api.ts` | Client tipizzato delle API (`/api/...`) |
| `src/lib/format.ts` | Formattazione € / €-L all'italiana + URL Google Maps |
| `src/lib/useCountUp.ts` | Hook animazione numeri (stat tiles) |
| `src/types.ts` | Tipi condivisi (`Offer`, `Stats`, `SourceHealth`…) |
| `src/components/Hero.tsx` | Hero: Spotlight + boccale 3D (`BeerGlass`) + `SearchBar`, parallax mouse |
| `src/components/BeerGlass.tsx` | Boccale "Liquid Gold" in SVG + bolle (framer-motion) |
| `src/components/SearchBar.tsx` | Input zona + cerca + refresh |
| `src/components/StatsPanel.tsx` | 4 tile con count-up |
| `src/components/FilterBar.tsx` | Filtro sconto (segmented) + ordina + filtro nome |
| `src/components/MarketChips.tsx` | Chip toggle per supermercato (colore brand) |
| `src/components/BeerCard.tsx` | Card singola offerta (prezzo, €/L, sconto, Maps) |
| `src/components/BeerGrid.tsx` | Griglia + skeleton + stati vuoto/scraping |
| `src/components/SourcesHealth.tsx` | Stato fonti (footer) |
| `src/components/ui/*` | Primitivi shadcn (`card`, `button`, `input`, `badge`, `skeleton`) + `spotlight` + `splite` |

Stato (in `useBeers`): `offers`/`filtered`, `discount` (`'all'|'sale'|'10'|'20'|'30'`), `markets` (Set), `sortBy` (`'discount'|'ppl_asc'|'price_asc'|'price_desc'|'name'`), `query`, `scraping`.

### Hero 3D
`BeerGlass.tsx` è un boccale SVG animato (CSS + framer-motion), reso di default perché affidabile e on-brand. `ui/splite.tsx` (`SplineScene`) resta pronto: per una scena Spline a tema birra basta importarlo nell'Hero con l'URL `.splinecode`.

---

## Design system "Liquid Gold"

Definito in `frontend/tailwind.config.js` + `frontend/src/index.css` (token HSL come variabili shadcn). Nero espresso + oro/ambra fuso, vetro (`.glass`), bagliore (`shadow-glow`), grana + gradienti caldi sullo sfondo.

- **Font:** **Fraunces** (display, `font-display`), **Hanken Grotesk** (body, `font-sans`), **Geist Mono** (prezzi, `font-mono` / `.nums`).
- **Accenti:** `--gold`, `--amber`, `--froth` (testo chiaro), `--deal` (verde sconto). `--radius: 1rem`.
- **Utility custom:** `.glass`, `.text-gold-gradient`, `.rule-gold`, `.nums`, animazioni `animate-spotlight` / `animate-float` / `animate-glow-pulse` / `animate-shimmer`.
- Token shadcn standard (`bg-card`, `text-foreground`, `border-border`, `bg-primary`…) mappati su variabili CSS in `index.css`.

---

## Comandi utili

```bash
# Avvio sviluppo backend con hot reload
uvicorn main:app --reload --port 8000

# Frontend dev (hot reload, proxy /api -> :8000)
cd frontend && npm run dev          # http://localhost:5173

# Build frontend (poi servito da FastAPI su :8000)
cd frontend && npm run build        # -> frontend/dist

# Test sintassi Python
python3 -c "import ast; [ast.parse(open(f).read()) for f in ['main.py','scraper.py','database.py']]"

# Svuota cache per una zona
python3 -c "import aiosqlite, asyncio; asyncio.run(aiosqlite.connect('beer_finder.db')).__aenter__() ..."

# Build Docker
docker build -t beerfinder .
docker run -p 8000:8000 beerfinder

# Deploy Docker Compose
docker-compose up --build -d
docker-compose logs -f
```

---

## Cose da NON fare

- Non usare `requests` (sync) — tutto async con `httpx`
- Non modificare `static/index.html` per cambiare la UI: il frontend vivo è `frontend/` (React). `static/` resta solo come backup.
- Non committare `beer_finder.db` (runtime data), né `frontend/node_modules/` / `frontend/dist/` (già in `.gitignore`; `dist` viene buildato)
- Non esporre le route API senza validazione `zone` (già gestita con `HTTPException(400)`)
- Non rimuovere il fallback demo — serve quando le fonti sono irraggiungibili
- Il catch-all SPA in `main.py` deve restare l'ultima route registrata (dopo tutte le `/api/...`)

---

## Dipendenze Python (da `requirements.txt`)

| Libreria | Versione | Uso |
|---|---|---|
| `fastapi` | 0.110.0 | Framework API |
| `uvicorn[standard]` | 0.29.0 | ASGI server |
| `httpx` | 0.27.0 | HTTP client asincrono |
| `beautifulsoup4` | 4.12.3 | Parsing HTML |
| `aiosqlite` | 0.20.0 | SQLite asincrono |
| `lxml` | 5.2.1 | Parser HTML veloce per BS4 |
| `fake-useragent` | 1.5.1 | Rotazione user-agent |
| `python-multipart` | 0.0.9 | Form data FastAPI |
| `python-dotenv` | 1.0.1 | Variabili d'ambiente opzionali |
