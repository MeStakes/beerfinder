import { SearchX, Loader2 } from 'lucide-react'
import type { Offer } from '@/types'
import { BeerCard } from './BeerCard'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

const GRID = 'grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'

function CardSkeleton() {
  return (
    <Card className="glass overflow-hidden">
      <Skeleton className="aspect-[5/4] rounded-none" />
      <div className="flex flex-col gap-3 p-4">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-5 w-3/4" />
        <div className="flex items-end justify-between pt-2">
          <Skeleton className="h-7 w-20" />
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
        <Skeleton className="mt-2 h-3 w-full" />
      </div>
    </Card>
  )
}

interface Props {
  offers: Offer[]
  loading: boolean
  scraping: boolean
}

export function BeerGrid({ offers, loading, scraping }: Props) {
  if (loading && offers.length === 0) {
    return (
      <div className={GRID}>
        {Array.from({ length: 8 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (offers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
        {scraping ? (
          <>
            <Loader2 className="h-10 w-10 animate-spin text-gold" />
            <p className="font-display text-xl text-froth">Sto cercando le offerte…</p>
            <p className="max-w-sm text-sm text-muted-foreground">
              Sto leggendo i volantini dei supermercati della zona. Ci vuole qualche secondo.
            </p>
          </>
        ) : (
          <>
            <div className="rounded-full border border-border bg-secondary/40 p-5">
              <SearchX className="h-9 w-9 text-muted-foreground" />
            </div>
            <p className="font-display text-xl text-froth">Nessuna offerta trovata</p>
            <p className="max-w-sm text-sm text-muted-foreground">
              Prova un'altra zona o rimuovi qualche filtro.
            </p>
          </>
        )}
      </div>
    )
  }

  return (
    <div className={GRID}>
      {offers.map((o, i) => (
        <BeerCard key={o.id} offer={o} index={i} />
      ))}
    </div>
  )
}
