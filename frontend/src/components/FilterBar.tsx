import { SlidersHorizontal, ArrowUpDown, Search } from 'lucide-react'
import type { DiscountFilter, SortBy } from '@/types'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

const DISCOUNTS: { key: DiscountFilter; label: string }[] = [
  { key: 'all', label: 'Tutte' },
  { key: 'sale', label: 'In offerta' },
  { key: '10', label: '10%+' },
  { key: '20', label: '20%+' },
  { key: '30', label: '30%+' },
]

const SORTS: { key: SortBy; label: string }[] = [
  { key: 'discount', label: 'Sconto maggiore' },
  { key: 'ppl_asc', label: 'Prezzo al litro ↑' },
  { key: 'price_asc', label: 'Prezzo ↑' },
  { key: 'price_desc', label: 'Prezzo ↓' },
  { key: 'name', label: 'Nome A→Z' },
]

interface Props {
  discount: DiscountFilter
  setDiscount: (d: DiscountFilter) => void
  sortBy: SortBy
  setSortBy: (s: SortBy) => void
  query: string
  setQuery: (q: string) => void
}

export function FilterBar({
  discount,
  setDiscount,
  sortBy,
  setSortBy,
  query,
  setQuery,
}: Props) {
  return (
    <div className="glass flex flex-col gap-4 rounded-lg p-4 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-wrap items-center gap-1.5">
        <SlidersHorizontal className="mr-1 h-4 w-4 text-gold/70" />
        {DISCOUNTS.map((d) => (
          <button
            key={d.key}
            onClick={() => setDiscount(d.key)}
            className={cn(
              'rounded-full px-3 py-1.5 text-sm font-medium transition-colors',
              discount === d.key
                ? 'bg-gold text-primary-foreground shadow-glow'
                : 'text-muted-foreground hover:bg-secondary/60 hover:text-froth'
            )}
          >
            {d.label}
          </button>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filtra per nome…"
            className="h-10 w-40 pl-9 text-sm sm:w-48"
            autoComplete="off"
          />
        </div>
        <div className="relative">
          <ArrowUpDown className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortBy)}
            aria-label="Ordina per"
            className="h-10 cursor-pointer appearance-none rounded-md border border-input bg-secondary/40 pl-9 pr-8 text-sm text-foreground transition-colors focus:border-gold/50 focus:outline-none"
          >
            {SORTS.map((s) => (
              <option key={s.key} value={s.key} className="bg-[#15100b] text-froth">
                {s.label}
              </option>
            ))}
          </select>
          <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
            ▾
          </span>
        </div>
      </div>
    </div>
  )
}
