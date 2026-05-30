import type {
  BeersResponse,
  SourcesHealthResponse,
  StatsResponse,
} from '@/types'

// In dev Vite fa da proxy di /api -> http://localhost:8000 (vedi vite.config.ts).
// In produzione il frontend è servito dallo stesso FastAPI, quindi /api è relativo.
const BASE = '/api'

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    let detail = ''
    try {
      const body = await res.json()
      detail = body?.detail ?? ''
    } catch {
      /* corpo non-JSON: ignora */
    }
    throw new Error(detail || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

/** Offerte per zona (con eventuale force refresh che bypassa la cache). */
export function fetchBeers(
  zone: string,
  opts?: { forceRefresh?: boolean }
): Promise<BeersResponse> {
  const p = new URLSearchParams({ zone })
  if (opts?.forceRefresh) p.set('force_refresh', 'true')
  return getJson<BeersResponse>(`${BASE}/beers?${p.toString()}`)
}

/** Avvia uno scraping in background per la zona. */
export function triggerRefresh(
  zone: string
): Promise<{ message: string; scraping: boolean }> {
  const p = new URLSearchParams({ zone })
  return getJson(`${BASE}/refresh?${p.toString()}`, { method: 'POST' })
}

/** Statistiche aggregate (non usate dall'app — le stats sono derivate lato client). */
export function fetchStats(zone: string): Promise<StatsResponse> {
  return getJson<StatsResponse>(`${BASE}/stats?zone=${encodeURIComponent(zone)}`)
}

/** Stato di salute delle fonti di scraping. */
export function fetchSourcesHealth(
  zone?: string
): Promise<SourcesHealthResponse> {
  const q = zone ? `?zone=${encodeURIComponent(zone)}` : ''
  return getJson<SourcesHealthResponse>(`${BASE}/sources/health${q}`)
}
