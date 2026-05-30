import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { fetchBeers, triggerRefresh } from '@/lib/api'
import type {
  BeersResponse,
  CacheInfo,
  DiscountFilter,
  MarketEntry,
  Offer,
  SortBy,
} from '@/types'

const POLL_MS = 3000

/**
 * Cuore dello stato dell'app: ricerca per zona, refresh+polling dello scraping,
 * e filtri/ordinamento applicati lato client (come l'app vanilla originale).
 */
export function useBeers() {
  const [zone, setZone] = useState('')
  const [offers, setOffers] = useState<Offer[]>([])
  const [loading, setLoading] = useState(false)
  const [scraping, setScraping] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cacheInfo, setCacheInfo] = useState<CacheInfo | null>(null)
  const [hasSearched, setHasSearched] = useState(false)

  // Filtri client-side
  const [discount, setDiscount] = useState<DiscountFilter>('all')
  const [markets, setMarkets] = useState<Set<string>>(new Set())
  const [sortBy, setSortBy] = useState<SortBy>('discount')
  const [query, setQuery] = useState('')

  const pollRef = useRef<number | null>(null)
  const activeZone = useRef('')

  const stopPolling = useCallback(() => {
    if (pollRef.current !== null) {
      clearTimeout(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const apply = useCallback((data: BeersResponse) => {
    setOffers(data.offers)
    setScraping(data.scraping)
    setCacheInfo(data.cache_info)
  }, [])

  const poll = useCallback(
    async (z: string) => {
      try {
        const data = await fetchBeers(z)
        if (activeZone.current !== z) return
        apply(data)
        if (data.scraping) {
          pollRef.current = window.setTimeout(() => poll(z), POLL_MS)
        } else {
          stopPolling()
        }
      } catch {
        stopPolling()
        setScraping(false)
      }
    },
    [apply, stopPolling]
  )

  const search = useCallback(
    async (z: string) => {
      const zoneKey = z.trim()
      if (!zoneKey) return
      stopPolling()
      activeZone.current = zoneKey
      setZone(zoneKey)
      setLoading(true)
      setError(null)
      setHasSearched(true)
      setMarkets(new Set())
      setDiscount('all')
      try {
        const data = await fetchBeers(zoneKey)
        if (activeZone.current !== zoneKey) return
        apply(data)
        if (data.scraping) {
          pollRef.current = window.setTimeout(() => poll(zoneKey), POLL_MS)
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Errore di rete')
        setOffers([])
      } finally {
        setLoading(false)
      }
    },
    [apply, poll, stopPolling]
  )

  const refresh = useCallback(async () => {
    const z = activeZone.current
    if (!z) return
    try {
      await triggerRefresh(z)
      setScraping(true)
      stopPolling()
      pollRef.current = window.setTimeout(() => poll(z), POLL_MS)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Refresh fallito')
    }
  }, [poll, stopPolling])

  useEffect(() => () => stopPolling(), [stopPolling])

  const toggleMarket = useCallback((name: string) => {
    setMarkets((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }, [])

  const clearMarkets = useCallback(() => setMarkets(new Set()), [])

  // Lista mercati con conteggi (da tutte le offerte, pre-filtro mercato)
  const marketList = useMemo<MarketEntry[]>(() => {
    const m = new Map<string, MarketEntry>()
    for (const o of offers) {
      const e = m.get(o.supermarket)
      if (e) e.count++
      else m.set(o.supermarket, { name: o.supermarket, count: 1, meta: o.supermarket_meta })
    }
    return [...m.values()].sort((a, b) => b.count - a.count)
  }, [offers])

  // Offerte filtrate + ordinate
  const filtered = useMemo<Offer[]>(() => {
    let list = offers
    const q = query.trim().toLowerCase()
    if (q) list = list.filter((o) => o.name.toLowerCase().includes(q))
    if (discount === 'sale') list = list.filter((o) => o.on_sale)
    else if (discount !== 'all') {
      const min = parseInt(discount, 10)
      list = list.filter((o) => o.discount_pct >= min)
    }
    if (markets.size > 0) list = list.filter((o) => markets.has(o.supermarket))

    const sorted = [...list]
    switch (sortBy) {
      case 'price_asc':
        sorted.sort((a, b) => a.sale_price - b.sale_price)
        break
      case 'price_desc':
        sorted.sort((a, b) => b.sale_price - a.sale_price)
        break
      case 'name':
        sorted.sort((a, b) => a.name.localeCompare(b.name, 'it'))
        break
      case 'ppl_asc':
        sorted.sort(
          (a, b) =>
            (a.price_per_liter ?? Infinity) - (b.price_per_liter ?? Infinity)
        )
        break
      default:
        sorted.sort((a, b) => b.discount_pct - a.discount_pct)
    }
    return sorted
  }, [offers, query, discount, markets, sortBy])

  // Statistiche derivate (evita una chiamata extra a /api/stats)
  const stats = useMemo(() => {
    const onSale = offers.filter((o) => o.on_sale)
    const avgDiscount = onSale.length
      ? Math.round(onSale.reduce((s, o) => s + o.discount_pct, 0) / onSale.length)
      : 0
    const best = onSale.reduce<Offer | null>(
      (b, o) => (!b || o.discount_pct > b.discount_pct ? o : b),
      null
    )
    const withPpl = offers.filter((o) => o.price_per_liter != null)
    const cheapestPerLiter = withPpl.reduce<Offer | null>(
      (b, o) =>
        !b || (o.price_per_liter as number) < (b.price_per_liter as number)
          ? o
          : b,
      null
    )
    return {
      total: offers.length,
      onSale: onSale.length,
      avgDiscount,
      best,
      cheapestPerLiter,
    }
  }, [offers])

  return {
    // stato
    zone,
    offers,
    filtered,
    loading,
    scraping,
    error,
    cacheInfo,
    hasSearched,
    // filtri
    discount,
    setDiscount,
    markets,
    toggleMarket,
    clearMarkets,
    sortBy,
    setSortBy,
    query,
    setQuery,
    // derivati
    marketList,
    stats,
    // azioni
    search,
    refresh,
  }
}
