"""
Gestione database SQLite con cache TTL per le offerte birra.
"""
import aiosqlite
import json
import time
from pathlib import Path

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


async def get_cached_offers(zone: str) -> list | None:
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
