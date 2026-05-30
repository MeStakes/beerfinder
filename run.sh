#!/bin/bash
# Avvio rapido BeerFinder in locale (backend FastAPI + frontend React buildato)

set -e

echo "🍺 BeerFinder — Avvio..."

# ── Python ──
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 non trovato. Installalo da https://python.org"
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "📦 Creando ambiente virtuale..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "📦 Installando dipendenze Python..."
pip install -q -r requirements.txt

# ── Frontend (build statica servita da FastAPI) ──
if command -v npm &> /dev/null; then
    if [ ! -d "frontend/dist" ]; then
        echo "📦 Build del frontend (React/Vite)..."
        (cd frontend && npm install --silent && npm run build)
    fi
else
    echo "⚠️  npm non trovato: salto la build frontend (fallback su static/index.html)."
fi

echo ""
echo "✅ Server avviato su → http://localhost:8000"
echo "   Sviluppo frontend con hot-reload:  cd frontend && npm run dev   (apre http://localhost:5173)"
echo "   Premi CTRL+C per fermare"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
