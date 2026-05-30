import type { CSSProperties } from 'react'
import type { MarketEntry } from '@/types'
import { cn } from '@/lib/utils'

interface Props {
  markets: MarketEntry[]
  active: Set<string>
  onToggle: (name: string) => void
  onClear: () => void
}

export function MarketChips({ markets, active, onToggle, onClear }: Props) {
  if (markets.length <= 1) return null

  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        onClick={onClear}
        className={cn(
          'rounded-full border px-3 py-1.5 text-sm font-medium transition-all',
          active.size === 0
            ? 'border-gold/40 bg-gold/12 text-gold'
            : 'border-border text-muted-foreground hover:border-gold/30 hover:text-froth'
        )}
      >
        Tutti i mercati
      </button>

      {markets.map((m) => {
        const on = active.has(m.name)
        const style: CSSProperties | undefined = on
          ? { borderColor: m.meta.color, boxShadow: `0 0 0 1px ${m.meta.color}55` }
          : undefined
        return (
          <button
            key={m.name}
            onClick={() => onToggle(m.name)}
            style={style}
            className={cn(
              'flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition-all',
              on
                ? 'bg-secondary text-froth'
                : 'border-border text-muted-foreground hover:border-gold/30 hover:text-froth'
            )}
          >
            <span aria-hidden>{m.meta.logo}</span>
            <span>{m.meta.full_name || m.name}</span>
            <span className="nums text-xs opacity-60">{m.count}</span>
          </button>
        )
      })}
    </div>
  )
}
