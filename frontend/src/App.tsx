import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Beer, Loader2 } from 'lucide-react'
import { useBeers } from '@/hooks/useBeers'
import { fetchSourcesHealth } from '@/lib/api'
import type { SourcesHealthResponse } from '@/types'
import { Hero } from '@/components/Hero'
import { StatsPanel } from '@/components/StatsPanel'
import { FilterBar } from '@/components/FilterBar'
import { MarketChips } from '@/components/MarketChips'
import { BeerGrid } from '@/components/BeerGrid'
import { SourcesHealth } from '@/components/SourcesHealth'

export default function App() {
  const b = useBeers()
  const [health, setHealth] = useState<SourcesHealthResponse | null>(null)

  // Errori -> toast
  useEffect(() => {
    if (b.error) toast.error(b.error)
  }, [b.error])

  // Stato fonti: al mount, e quando cambia zona o termina lo scraping
  useEffect(() => {
    let alive = true
    fetchSourcesHealth(b.zone || undefined)
      .then((h) => {
        if (alive) setHealth(h)
      })
      .catch(() => {})
    return () => {
      alive = false
    }
  }, [b.zone, b.scraping])

  const handleRefresh = () => {
    b.refresh()
    toast('Aggiornamento avviato…', {
      description: 'Sto rileggendo i volantini della zona.',
    })
  }

  const ageHours = b.cacheInfo?.cached
    ? Math.floor(b.cacheInfo.age_seconds / 3600)
    : null

  return (
    <div className="mx-auto flex min-h-svh max-w-[1320px] flex-col gap-8 px-4 py-6 sm:px-6 md:py-10">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-b from-gold to-amber text-primary-foreground shadow-glow">
            <Beer className="h-5 w-5" />
          </span>
          <span className="font-display text-xl font-semibold tracking-tight text-froth">
            BeerFinder
          </span>
        </div>
        <span className="hidden text-xs text-muted-foreground sm:block">
          Volantini supermercati italiani · aggiornato ogni giorno
        </span>
      </header>

      <Hero
        onSearch={b.search}
        onRefresh={handleRefresh}
        loading={b.loading}
        scraping={b.scraping}
        hasZone={!!b.zone}
        healthyCount={health?.healthy_count ?? 0}
      />

      {b.hasSearched && (
        <section className="flex flex-col gap-6">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="font-display text-2xl font-semibold text-froth">
                Offerte a{' '}
                <span className="capitalize text-gold-gradient">{b.zone}</span>
              </h2>
              <p className="text-sm text-muted-foreground">
                {b.filtered.length} di {b.offers.length} offerte
                {ageHours !== null &&
                  ` · aggiornate ${ageHours === 0 ? 'oggi' : `${ageHours}h fa`}`}
              </p>
            </div>
            {b.scraping && (
              <span className="flex items-center gap-2 rounded-full border border-gold/25 bg-gold/10 px-3 py-1 text-xs font-medium text-gold">
                <Loader2 className="h-3 w-3 animate-spin" />
                aggiornamento in corso
              </span>
            )}
          </div>

          {b.offers.length > 0 && <StatsPanel stats={b.stats} />}

          {b.offers.length > 0 && (
            <FilterBar
              discount={b.discount}
              setDiscount={b.setDiscount}
              sortBy={b.sortBy}
              setSortBy={b.setSortBy}
              query={b.query}
              setQuery={b.setQuery}
            />
          )}

          <MarketChips
            markets={b.marketList}
            active={b.markets}
            onToggle={b.toggleMarket}
            onClear={b.clearMarkets}
          />

          <BeerGrid offers={b.filtered} loading={b.loading} scraping={b.scraping} />
        </section>
      )}

      {/* Footer */}
      <footer className="mt-auto border-t border-border/60 pt-6">
        {health && <SourcesHealth sources={health.sources} />}
        <p className="mt-4 text-xs text-muted-foreground/70">
          BeerFinder · i prezzi possono variare per punto vendita — verifica sempre in
          negozio. Dati dai volantini di promoqui.it e tiendeo.it.
        </p>
      </footer>
    </div>
  )
}
