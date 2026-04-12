# 🍺 BeerFinder — Offerte Birra in Tempo Reale

> Scraper intelligente che aggrega volantini e siti dei supermercati italiani, trova le migliori offerte sulla birra e le espone in un'interfaccia dark ultra-moderna.

---

## ✨ Features

- **🔍 Ricerca per zona** — inserisci città o CAP, il sito trova le offerte vicino a te
- **🏪 Multi-sorgente** — scrapa in parallelo da promoqui.it, volantino.it e offerte.it
- **💾 Cache SQLite** — TTL 24h per non stressare le fonti, aggiornamento manuale on-demand
- **🎨 UI dark premium** — glassmorphism, bolle animate, card con glow amber, scheletri di caricamento
- **🏷️ Badge & filtri** — filtra per sconto minimo, supermercato, solo in offerta; ordina per prezzo o sconto
- **📊 Stats live** — totale offerte, sconto medio, miglior deal del giorno
- **🔄 Polling automatico** — se lo scraping è in corso la UI si aggiorna da sola ogni 3 secondi
- **🐳 Deploy-ready** — Dockerfile + docker-compose per Railway, Render, Fly.io, qualsiasi VPS

---

## 🗂️ Struttura del progetto

```
beer-finder/
├── main.py              # FastAPI app — API REST + serving frontend
├── scraper.py           # Scraper multi-sorgente asincrono
├── database.py          # Cache SQLite asincrona (aiosqlite)
├── requirements.txt     # Dipendenze Python
├── run.sh               # Avvio rapido in locale (crea venv + installa + avvia)
├── Dockerfile           # Build produzione
├── docker-compose.yml   # Stack completo con volume persistente
└── static/
    └── index.html       # SPA — HTML/CSS/JS vanilla, zero dipendenze frontend
```

---

## 🚀 Avvio rapido (locale)

### Prerequisiti

- Python 3.11+ ([python.org](https://python.org))
- pip

### 1 — Clona / scarica il progetto

```bash
git clone https://github.com/tuousername/beerfinder.git
cd beerfinder
```

### 2 — Avvia con un comando

```bash
bash run.sh
```

Lo script crea automaticamente un ambiente virtuale, installa le dipendenze e avvia il server.

### 3 — Apri il browser

```
http://localhost:8000
```

Inserisci la tua città (es. `Milano`, `Roma`, `20121`) e premi **Cerca offerte**.

---

## 🐳 Deploy con Docker

### Locale con Docker Compose

```bash
docker-compose up --build
```

Il sito sarà disponibile su `http://localhost:8000`. Il database SQLite è persistente nel volume `./beer_finder.db`.

### Deploy su Railway

1. Crea un nuovo progetto su [railway.app](https://railway.app)
2. Collega la repo GitHub
3. Railway rileva il `Dockerfile` in automatico
4. Deploy in un click — ottieni una URL pubblica

### Deploy su Render

1. Nuovo **Web Service** su [render.com](https://render.com)
2. Runtime: **Docker**
3. Disk persistente montato su `/app` per il database
4. Variabili d'ambiente: nessuna richiesta

### Deploy su Fly.io

```bash
fly launch
fly deploy
```

---

## 🔌 API Reference

Tutte le API sono disponibili su `/api/...` e rispondono in JSON.

### `GET /api/beers`

Restituisce le offerte birra per una zona. Usa la cache se disponibile.

| Parametro | Tipo | Default | Descrizione |
|---|---|---|---|
| `zone` | string | **required** | Città o CAP |
| `force_refresh` | bool | `false` | Ignora cache e riscrapa |
| `supermarket` | string | `""` | Filtra per supermercato |
| `on_sale_only` | bool | `false` | Solo prodotti in offerta |
| `min_discount` | int | `0` | Sconto minimo (0–100) |
| `sort_by` | string | `discount` | `discount` \| `price_asc` \| `price_desc` \| `name` |

**Esempio risposta:**

```json
{
  "zone": "Milano",
  "total": 18,
  "scraping": false,
  "cache_info": {
    "cached": true,
    "age_seconds": 3600,
    "expires_in": 82800,
    "scraped_at": 1712923200
  },
  "offers": [
    {
      "id": "demo_0",
      "name": "Birra Moretti 6x33cl",
      "supermarket": "Esselunga",
      "supermarket_meta": { "logo": "🟢", "color": "#006b2b", "full_name": "Esselunga" },
      "sale_price": 4.49,
      "original_price": 5.99,
      "discount_pct": 25,
      "on_sale": true,
      "image_url": "",
      "validity": "Fino a domenica",
      "source": "promoqui.it",
      "zone": "Milano"
    }
  ]
}
```

---

### `POST /api/refresh`

Avvia un nuovo scraping in background (non blocca).

| Parametro | Tipo | Descrizione |
|---|---|---|
| `zone` | string | Città o CAP |

---

### `GET /api/stats`

Statistiche aggregate per zona.

```json
{
  "zone": "Roma",
  "total": 18,
  "on_sale": 14,
  "avg_discount": 22,
  "best_deal": { "name": "Heineken 24x33cl", "discount_pct": 25, ... },
  "supermarkets": { "Esselunga": 4, "Conad": 3, "Lidl": 2 }
}
```

---

### `GET /api/supermarkets`

Lista supermercati trovati per zona, ordinati per numero di offerte.

---

### `GET /api/health`

Healthcheck — restituisce `{ "status": "ok", "timestamp": 1712923200 }`.

---

## 🏗️ Architettura

```
Browser (SPA)
    │  fetch /api/beers?zone=...
    ▼
FastAPI (main.py)
    │
    ├── Cache HIT?  ──→  Restituisce dati SQLite
    │
    └── Cache MISS / force_refresh
            │
            ▼
        scraper.py  (asyncio.gather)
            ├── scrape_promoqui()   → promoqui.it
            ├── scrape_volantino()  → volantino.it
            └── scrape_offerte()    → offerte.it
                        │
                        ▼  deduplica + sort
                    database.py  →  SQLite  →  API response
```

**Flusso scraping:**

1. `scrape_all(zone)` lancia le 3 fonti in parallelo con `asyncio.gather`
2. I risultati vengono deduplicati per `nome[:30] + supermercato`
3. Se nessuna fonte risponde (rete assente, bot-protection) → fallback dati demo
4. Tutto salvato in SQLite con timestamp; TTL 24h

---

## 🛒 Supermercati supportati

Il parser riconosce automaticamente 18+ catene italiane:

| Supermercato | Colore | Supermercato | Colore |
|---|---|---|---|
| Lidl | 🔵 #0050aa | Esselunga | 🟢 #006b2b |
| Conad | 🔴 #e30613 | Carrefour | 🔵 #004899 |
| Eurospin | 🟡 #ffcc00 | Penny Market | 🔴 #e30613 |
| Aldi | 🔵 #00539f | IN'S Mercato | 🟠 #f47920 |
| MD Discount | 🟡 #f5a200 | Coop/Ipercoop | 🔵 #0072bc |
| Iper | 🟣 #6a0dad | Bennet | 🟢 #009639 |
| Despar/Interspar | 🟢 #007a33 | PAM | 🔴 #da291c |
| Sigma | 🔴 #e52330 | Simply | 🟢 #00843d |
| U2 Supermercato | 🟠 #ff6600 | Famila | 🔵 #004b87 |

---

## ⚙️ Configurazione

Nessun file `.env` richiesto per l'avvio base. Variabili opzionali:

| Variabile | Default | Descrizione |
|---|---|---|
| `PORT` | `8000` | Porta del server |
| `WORKERS` | `2` | Worker uvicorn (Dockerfile) |

---

## 🔧 Sviluppo

### Aggiungere una nuova fonte

1. Apri `scraper.py`
2. Crea una funzione `async def scrape_nomefonte(client, zone) -> list:`
3. Aggiungi la chiamata in `scrape_all()` dentro `asyncio.gather(...)`
4. Ogni offer deve avere questi campi:

```python
{
    "id": "nomefonte_hash",
    "name": str,
    "supermarket": str,
    "supermarket_meta": dict,   # get_supermarket_meta(supermarket)
    "sale_price": float,
    "original_price": float | None,
    "discount_pct": int,
    "on_sale": bool,
    "image_url": str,
    "validity": str,
    "source": str,
    "zone": str,
}
```

### Hot reload in sviluppo

```bash
uvicorn main:app --reload --port 8000
```

---

## 📝 Note legali

- Lo scraper rispetta i `robots.txt` delle fonti aggregate
- Rate limiting: delay random 1–2s tra le richieste
- User-agent rotation tra browser reali
- I dati appartengono ai rispettivi supermercati — uso personale/demo only

---

## 🗺️ Roadmap

- [ ] Integrazione Playwright per siti JS-heavy
- [ ] Notifiche push quando arriva un'offerta sotto soglia
- [ ] Comparatore prezzi storico (grafico prezzi nel tempo)
- [ ] PWA installabile su mobile
- [ ] Export CSV/Excel delle offerte
- [ ] API key per accesso esterno

---

## 📄 Licenza

MIT — libero uso, modifica e distribuzione.

---

*Made with 🍺 and Claude*
