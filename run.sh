#!/bin/bash
# Avvio rapido BeerFinder in locale

set -e

echo "🍺 BeerFinder — Avvio server..."

# Controlla Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 non trovato. Installalo da https://python.org"
    exit 1
fi

# Installa dipendenze se necessario
if [ ! -d ".venv" ]; then
    echo "📦 Creando ambiente virtuale..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "📦 Installando dipendenze..."
pip install -q -r requirements.txt

echo ""
echo "✅ Server avviato su → http://localhost:8000"
echo "   Premi CTRL+C per fermare"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
