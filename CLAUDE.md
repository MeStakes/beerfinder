# CLAUDE.md — BeerFinder Project Context

> File di contesto per Claude Code. Leggilo prima di modificare qualsiasi file.

---

## Identità del progetto

**BeerFinder** è un'applicazione web full-stack Python che aggrega offerte birra dai supermercati italiani tramite scraping, le memorizza in SQLite e le espone tramite una SPA dark ultra-moderna.

Stack: `FastAPI` + `BeautifulSoup4` + `httpx` (async) + `aiosqlite` + HTML/CSS/JS vanilla.

---

## Mappa file — cosa fa cosa

| File | Ruolo | Toccare quando… |
|---|---|---|
| `main.py` | FastAPI app, route API, serving static | aggiungi endpoint, cambi CORS, modifichi la logica di cache |
| `scraper.py` | Scraper asincrono multi-sorgente | aggiungi fonti, sistemi parsing HTML, cambi keyword birra |
| `database.py` | CRUD SQLite asincrono + TTL cache | cambi TTL, aggiungi tabelle, modifichi schema |
| `static/index.html` | SPA completa (HTML+CSS+JS in un file) | cambi UI, aggiungi filtri, modifichi grafica |
| `requirements.txt` | Dipendenze Python esatte | aggiungi librerie, aggiorni versioni |
| `run.sh` | Avvio rapido locale con venv | cambi porta default o opzioni uvicorn |
| `Dockerfile` | Build produzione | cambi versione Python, aggiungi dipendenze sistema |
| `docker-compose.yml` | Stack Docker completo | aggiungi servizi (redis, nginx…) |

---

## Convenzioni di codice

- **Lingua commenti:** italiano
- **Lingua variabili/funzioni:** inglese snake_case
- **Async ovunque:** tutte le funzioni I/O sono `async def`; non usare `requests` (usa `httpx`)
- **Nessun ORM:** solo SQL raw con `aiosqlite`
- **Frontend:** vanilla JS, niente framework, niente build step — tutto in `static/index.html`
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
    "source": str,                # es. "promoqui.it"
    "zone": str,                  # zona lowercase (es. "milano")
}
```

**Funzioni helper già disponibili in `scraper.py`:**
- `is_beer(text)` → bool — controlla se il testo riguarda birra
- `extract_price(text)` → float|None — estrae prezzo da stringa
- `get_supermarket_meta(name)` → dict — restituisce meta del supermercato
- `calc_discount(original, sale)` → int — calcola % sconto
- `get_demo_data(zone)` → list — dati demo di fallback

---

## API endpoints esistenti

```
GET  /api/beers?zone=...          → offerte con filtri e sort
POST /api/refresh?zone=...        → avvia scraping background
GET  /api/stats?zone=...          → statistiche aggregate
GET  /api/supermarkets?zone=...   → lista supermercati trovati
GET  /api/health                  → healthcheck
GET  /                            → serve static/index.html
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
    scrape_volantino(client, zone),
    scrape_offerte(client, zone),
    scrape_nomefonte(client, zone),   # ← aggiungi qui
    return_exceptions=True
)
```

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

## Frontend — struttura JS in `index.html`

Funzioni principali:

| Funzione | Ruolo |
|---|---|
| `doSearch()` | Avvia la ricerca, chiama `fetchBeers()`, gestisce loading state |
| `fetchBeers(zone, sortBy)` | Fetch API `/api/beers`, restituisce JSON |
| `doRefresh()` | POST `/api/refresh`, avvia `startPolling()` |
| `startPolling(zone)` | Polling ogni 3s finché `scraping=false` |
| `handleResponse(data)` | Aggiorna stats, chiama `buildMarketChips()` + `applyFilters()` |
| `applyFilters()` | Filtra e ordina `allOffers`, chiama `renderGrid()` |
| `renderGrid(offers)` | Genera HTML delle card |
| `beerCard(offer, idx)` | Template HTML singola card |
| `showSkeletons()` | Mostra skeleton loader (9 card) |
| `showToast(msg, type)` | Notifica bottom-center |

Stato globale:
- `allOffers` — array offerte corrente (pre-filtro)
- `currentZone` — zona attiva
- `activeFilter` — filtro sconto attivo (`'all'`, `'sale'`, `'10'`, `'20'`, `'30'`)
- `activeMarkets` — Set supermercati selezionati

---

## Variabili CSS (design system)

```css
--bg: #06060a            /* sfondo principale */
--surface: #0e0e16       /* superfici elevate */
--card: #12121c          /* card */
--card-hover: #17172a    /* card hover */
--border: #1e1e30        /* bordi */
--amber: #f59e0b         /* colore primario (birra) */
--amber-dim: #d97706     /* amber scuro */
--amber-glow: rgba(245,158,11,0.15)
--green: #10b981         /* badge offerta */
--red: #ef4444           /* errori */
--text: #f0eff5          /* testo principale */
--text-sub: #8b8aa0      /* testo secondario */
--text-dim: #4a4960      /* testo disabilitato */
--radius: 16px           /* border-radius card */
--radius-sm: 10px
--transition: 0.25s cubic-bezier(0.4,0,0.2,1)
```

---

## Comandi utili

```bash
# Avvio sviluppo con hot reload
uvicorn main:app --reload --port 8000

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
- Non importare librerie frontend via npm/CDN non necessarie — UI è intenzionalmente zero-dependency
- Non committare `beer_finder.db` — è runtime data
- Non esporre le route API senza validazione `zone` (già gestita con `HTTPException(400)`)
- Non rimuovere il fallback demo — serve quando le fonti sono irraggiungibili

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
