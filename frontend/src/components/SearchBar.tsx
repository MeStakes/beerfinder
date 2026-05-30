import { useState, type FormEvent } from 'react'
import { Search, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

interface Props {
  onSearch: (zone: string) => void
  onRefresh: () => void
  loading: boolean
  scraping: boolean
  hasZone: boolean
}

export function SearchBar({ onSearch, onRefresh, loading, scraping, hasZone }: Props) {
  const [value, setValue] = useState('')

  const submit = (e: FormEvent) => {
    e.preventDefault()
    onSearch(value)
  }

  return (
    <form onSubmit={submit} className="flex w-full max-w-xl flex-col gap-3 sm:flex-row">
      <div className="relative flex-1">
        <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Città o CAP — es. Milano, 20100"
          className="pl-11"
          autoComplete="off"
          spellCheck={false}
        />
      </div>
      <Button type="submit" variant="gold" size="lg" disabled={loading || !value.trim()}>
        {loading ? 'Cerco…' : 'Trova offerte'}
      </Button>
      {hasZone && (
        <Button
          type="button"
          variant="outline"
          size="lg"
          onClick={onRefresh}
          disabled={scraping}
          title="Aggiorna offerte"
          aria-label="Aggiorna offerte"
        >
          <RefreshCw className={cn('h-4 w-4', scraping && 'animate-spin')} />
          <span className="sm:hidden">Aggiorna</span>
        </Button>
      )}
    </form>
  )
}
