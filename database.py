"""
Gestione database SQLite con cache TTL per le offerte birra.
"""
import aiosqlite
import json
import time
from pathlib import Path
from typing import Optional

DB_PATH = Path("beer_finder.db")
TTL_SECONDS = 86400  # 24 ore


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS beer_offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone TEXT NOT NULL,
                data JSON NOT NULL,
                scraped_at REAL NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scrape_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                items_found INTEGER DEFAULT 0,
                timestamp REAL NOT NULL,
                error TEXT
            )
        """)
        await db.commit()


async def get_cached_offers(zone: str) -> Optional[list]:
    """Restituisce offerte in cache se non scadute, altrimenti None."""
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT data, scraped_at FROM beer_offers WHERE zone = ? ORDER BY scraped_at DESC LIMIT 1",
            (zone.lower(),)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                data, scraped_at = row
                if now - scraped_at < TTL_SECONDS:
                    return json.loads(data)
    return None


async def save_offers(zone: str, offers: list):
    """Salva offerte nel database."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Rimuovi vecchie offerte per questa zona
        await db.execute("DELETE FROM beer_offers WHERE zone = ?", (zone.lower(),))
        await db.execute(
            "INSERT INTO beer_offers (zone, data, scraped_at) VALUES (?, ?, ?)",
            (zone.lower(), json.dumps(offers, ensure_ascii=False), time.time())
        )
        await db.commit()


async def log_scrape(zone: str, source: str, status: str, items: int = 0, error: str = None):
    """Log dell'attività di scraping."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO scrape_log (zone, source, status, items_found, timestamp, error) VALUES (?, ?, ?, ?, ?, ?)",
            (zone.lower(), source, status, items, time.time(), error)
        )
        await db.commit()


async def get_cache_info(zone: str) -> dict:
    """Info sulla cache per una zona."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT scraped_at FROM beer_offers WHERE zone = ? ORDER BY scraped_at DESC LIMIT 1",
            (zone.lower(),)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                age = time.time() - row[0]
                return {
                    "cached": True,
                    "age_seconds": int(age),
                    "expires_in": max(0, int(TTL_SECONDS - age)),
                    "scraped_at": int(row[0])
                }
    return {"cached": False, "age_seconds": 0, "expires_in": 0, "scraped_at": 0}


async def get_sources_health(zone: Optional[str] = None) -> list:
    """Stato di salute di ogni fonte di scraping, ricavato da scrape_log.
    Per ciascuna source restituisce l'ultimo tentativo e l'ultimo successo.
    Se 'zone' è passata, filtra solo i log di quella zona."""
    where = "WHERE zone = ?" if zone else ""
    params = (zone.lower(),) if zone else ()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            f"SELECT source, status, items_found, timestamp, error "
            f"FROM scrape_log {where} ORDER BY timestamp DESC",
            params
        ) as cursor:
            rows = await cursor.fetchall()

    # Aggrega in Python: righe già ordinate per timestamp DESC, quindi
    # il primo record di ogni source = ultimo tentativo; il primo "ok" = ultimo successo.
    sources: dict = {}
    for source, status, items, ts, error in rows:
        if source not in sources:
            sources[source] = {
                "source": source,
                "last_status": status,
                "last_items": items,
                "last_attempt": int(ts),
                "last_error": error,
                "last_success": None,
                "last_success_items": 0,
                # Sana = ULTIMO tentativo andato a buon fine con almeno 1 offerta
                "healthy": status == "ok" and (items or 0) > 0,
            }
        if status == "ok" and sources[source]["last_success"] is None:
            sources[source]["last_success"] = int(ts)
            sources[source]["last_success_items"] = items
    return sorted(sources.values(), key=lambda x: -x["last_attempt"])
