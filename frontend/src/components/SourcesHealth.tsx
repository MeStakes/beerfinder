import type { SourceHealth } from '@/types'
import { cn } from '@/lib/utils'

/** Tempo relativo in italiano da un timestamp unix (secondi). */
function rel(ts: number): string {
  if (!ts) return ''
  const diff = Math.max(0, Math.floor(Date.now() / 1000 - ts))
  if (diff < 60) return 'adesso'
  if (diff < 3600) return `${Math.floor(diff / 60)} min fa`
  if (diff < 86400) return `${Math.floor(diff / 3600)} h fa`
  return `${Math.floor(diff / 86400)} g fa`
}

export function SourcesHealth({ sources }: { sources: SourceHealth[] }) {
  if (!sources.length) return null

  return (
    <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
      <span className="font-semibold uppercase tracking-wide text-froth/70">
        Stato fonti
      </span>
      {sources.map((s) => (
        <span key={s.source} className="flex items-center gap-2">
          <span
            className={cn(
              'h-2 w-2 rounded-full',
              s.healthy ? 'bg-deal shadow-[0_0_8px_hsl(152_58%_46%)]' : 'bg-destructive'
            )}
          />
          <span className="font-medium text-froth/90">{s.source}</span>
          <span className="opacity-70">
            {s.last_items} offerte · {rel(s.last_attempt)}
          </span>
        </span>
      ))}
    </div>
  )
}
