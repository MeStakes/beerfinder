import type { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { Boxes, Tag, Percent, Droplet } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { useCountUp } from '@/lib/useCountUp'
import { ppl } from '@/lib/format'
import type { Offer } from '@/types'

interface Stats {
  total: number
  onSale: number
  avgDiscount: number
  best: Offer | null
  cheapestPerLiter: Offer | null
}

function Tile({
  icon,
  label,
  value,
  sub,
  delay,
}: {
  icon: ReactNode
  label: string
  value: ReactNode
  sub?: string
  delay: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay }}
    >
      <Card className="glass flex h-full flex-col gap-2 p-4">
        <div className="flex items-center gap-2 text-muted-foreground">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-gold/12 text-gold">
            {icon}
          </span>
          <span className="text-xs font-semibold uppercase tracking-wide">
            {label}
          </span>
        </div>
        <div className="nums font-display text-3xl font-semibold text-froth">
          {value}
        </div>
        {sub && <div className="truncate text-xs text-muted-foreground">{sub}</div>}
      </Card>
    </motion.div>
  )
}

export function StatsPanel({ stats }: { stats: Stats }) {
  const total = useCountUp(stats.total)
  const onSale = useCountUp(stats.onSale)
  const avg = useCountUp(stats.avgDiscount)

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      <Tile icon={<Boxes className="h-4 w-4" />} label="Offerte" value={total} delay={0} />
      <Tile
        icon={<Tag className="h-4 w-4" />}
        label="In offerta"
        value={onSale}
        delay={0.06}
      />
      <Tile
        icon={<Percent className="h-4 w-4" />}
        label="Sconto medio"
        value={`${avg}%`}
        delay={0.12}
      />
      <Tile
        icon={<Droplet className="h-4 w-4" />}
        label="Miglior €/L"
        value={
          stats.cheapestPerLiter?.price_per_liter != null
            ? ppl(stats.cheapestPerLiter.price_per_liter)
            : '—'
        }
        sub={stats.cheapestPerLiter?.supermarket_meta.full_name}
        delay={0.18}
      />
    </div>
  )
}
