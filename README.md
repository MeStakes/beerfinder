# BeerFinder — Offerte Birra a Modena

Scraper che aggrega i volantini dei supermercati italiani, trova le offerte sulla birra e le mostra in un'interfaccia dark.

---

## Cosa fa

- Cerca offerte birra su **promoqui.it**, volantino.it e offerte.it
- Salva i risultati in SQLite con cache di 24h (non riscarica ogni volta)
- Mostra tutto in una pagina web dark con card, filtri e link al volantino originale
- La zona è fissa su **Modena** — apri il sito e le offerte si caricano da sole

---

## Struttura

```
├── main.py              # Server FastAPI — API REST + serve la pagina web
├── scraper.py           # Scraper asincrono multi-sorgente
├── database.py          # Cache SQLite (aiosqlite)
├── static/index.html    # Interfaccia web (HTML/CSS/JS, zero dipendenze)
├── requirements.txt     # Dipendenze Python
├── run.sh               # Script di avvio rapido
├── Dockerfile           # Per deploy in produzione
└── docker-compose.yml   # Stack completo con volume persistente
```

---

## Avvio locale

### Prerequisiti

- Python 3.9+

### Avvia con un comando

```bash
bash run.sh
```

Lo script crea il virtualenv, installa le dipendenze e avvia il server.

Poi apri: **http://localhost:8000**

Le offerte si caricano automaticamente all'apertura.

---

## Deploy su Railway (per condividerlo con altri)

1. Vai su [railway.app](https://railway.app) → accedi con GitHub
2. "New Project" → "Deploy from GitHub repo" → seleziona questa repo
3. Railway usa il `Dockerfile` in automatico
4. Ottieni una URL pubblica da mandare agli amici

---

## API

```
GET  /api/beers?zone=modena          → offerte (con filtri opzionali)
POST /api/refresh?zone=modena        → forza nuovo scraping in background
GET  /api/stats?zone=modena          → statistiche (totale, sconto medio, best deal)
GET  /api/supermarkets?zone=modena   → lista supermercati trovati
GET  /api/health                     → healthcheck
GET  /                               → pagina web
```

Parametri opzionali per `/api/beers`:

| Parametro | Default | Descrizione |
|---|---|---|
| `force_refresh` | `false` | Ignora cache e riscarica |
| `supermarket` | `""` | Filtra per supermercato |
| `on_sale_only` | `false` | Solo prodotti in offerta |
| `min_discount` | `0` | Sconto minimo % |
| `sort_by` | `discount` | `discount` / `price_asc` / `price_desc` / `name` |

---

## Note

- **Bennet è escluso** dai risultati (hardcoded in `main.py`)
- La cache dura 24h per zona — usa `force_refresh=true` o il pulsante Aggiorna per riscaricate
- Se tutte le fonti falliscono (bot-protection, rete assente) vengono mostrati dati demo
- `Accept-Encoding` va omesso dagli header: httpx non decomprime automaticamente se impostato manualmente

---

*Made with Claude*
