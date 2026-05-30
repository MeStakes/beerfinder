import { motion } from 'framer-motion'
import { MapPin, Clock } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Offer } from '@/types'
import { euro, ppl, mapsUrl } from '@/lib/format'

export function BeerCard({ offer, index }: { offer: Offer; index: number }) {
  const meta = offer.supermarket_meta
  const color = meta.color || '#f5b62c'

  return (
    <motion.div
      initial={{ opacity: 0, y: 22 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: Math.min(index * 0.025, 0.35) }}
    >
      <Card className="group glass relative flex h-full flex-col overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:border-gold/30 hover:shadow-glow">
        {/* immagine prodotto */}
        <div className="relative aspect-[5/4] overflow-hidden bg-[radial-gradient(circle_at_50%_28%,hsl(40_40%_22%/0.45),transparent_70%)]">
          {offer.image_url ? (
            <img
              src={offer.image_url}
              alt={offer.name}
              loading="lazy"
              className="h-full w-full object-contain p-4 transition-transform duration-500 group-hover:scale-105"
              onError={(e) => {
                e.currentTarget.style.visibility = 'hidden'
              }}
            />
          ) : (
            <div className="flex h-full items-center justify-center text-6xl opacity-25">
              🍺
            </div>
          )}

          {offer.on_sale && offer.discount_pct > 0 && (
            <div className="absolute left-3 top-3">
              <Badge variant="gold" className="text-sm shadow-glow">
                −{offer.discount_pct}%
              </Badge>
            </div>
          )}

          <span className="absolute right-3 top-3 rounded-full bg-black/45 px-2 py-0.5 text-[10px] font-medium text-muted-foreground backdrop-blur">
            {offer.source}
          </span>
        </div>

        {/* corpo */}
        <div className="flex flex-1 flex-col gap-3 p-4">
          <div className="flex items-center gap-2">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full ring-2 ring-white/10"
              style={{ background: color }}
            />
            <span className="truncate text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {meta.full_name || offer.supermarket}
            </span>
          </div>

          <h3 className="line-clamp-2 font-display text-lg font-semibold leading-snug text-froth">
            {offer.name}
          </h3>

          <div className="mt-auto flex items-end justify-between gap-2 pt-2">
            <div className="flex flex-col leading-tight">
              <span className="nums font-mono text-2xl font-semibold text-gold">
                {euro(offer.sale_price)}
              </span>
              {offer.original_price && (
                <span className="nums text-sm text-muted-foreground line-through">
                  {euro(offer.original_price)}
                </span>
              )}
            </div>
            {offer.price_per_liter != null && (
              <Badge
                variant="outline"
                className="nums border-gold/25 text-gold/90"
                title="Prezzo al litro"
              >
                {ppl(offer.price_per_liter)}
              </Badge>
            )}
          </div>

          {/* footer */}
          <div className="flex items-center justify-between gap-2 border-t border-border/60 pt-3 text-xs text-muted-foreground">
            <span className="flex min-w-0 items-center gap-1 truncate">
              {offer.validity ? (
                <>
                  <Clock className="h-3 w-3 shrink-0" />
                  <span className="truncate">{offer.validity}</span>
                </>
              ) : (
                <span className="opacity-50">offerta volantino</span>
              )}
            </span>
            <a
              href={mapsUrl(offer.supermarket, offer.zone)}
              target="_blank"
              rel="noreferrer"
              className="flex shrink-0 items-center gap-1 text-gold/80 transition-colors hover:text-gold"
            >
              <MapPin className="h-3 w-3" /> Mappa
            </a>
          </div>
        </div>
      </Card>
    </motion.div>
  )
}
