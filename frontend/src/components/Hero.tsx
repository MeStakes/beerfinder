import { useRef } from 'react'
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion'
import { Sparkles } from 'lucide-react'
import { Spotlight } from '@/components/ui/spotlight'
import { Card } from '@/components/ui/card'
import { BeerGlass } from './BeerGlass'
import { SearchBar } from './SearchBar'

interface Props {
  onSearch: (zone: string) => void
  onRefresh: () => void
  loading: boolean
  scraping: boolean
  hasZone: boolean
  healthyCount: number
}

export function Hero({ healthyCount, ...search }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const mx = useMotionValue(0)
  const my = useMotionValue(0)
  const rotateX = useSpring(useTransform(my, [-0.5, 0.5], [10, -10]), {
    stiffness: 120,
    damping: 18,
  })
  const rotateY = useSpring(useTransform(mx, [-0.5, 0.5], [-14, 14]), {
    stiffness: 120,
    damping: 18,
  })

  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const r = ref.current?.getBoundingClientRect()
    if (!r) return
    mx.set((e.clientX - r.left) / r.width - 0.5)
    my.set((e.clientY - r.top) / r.height - 0.5)
  }
  const onLeave = () => {
    mx.set(0)
    my.set(0)
  }

  return (
    <Card
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      className="relative min-h-[540px] overflow-hidden border-border/60 bg-[#070504]"
    >
      <Spotlight className="-top-40 left-0 md:-top-24 md:left-1/4" fill="hsl(40 92% 60%)" />

      {/* griglia decorativa sottile */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage:
            'linear-gradient(hsl(40 60% 70%) 1px, transparent 1px), linear-gradient(90deg, hsl(40 60% 70%) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
      />

      <div className="relative z-10 grid min-h-[540px] items-center gap-8 p-7 md:grid-cols-[1.1fr_0.9fr] md:p-12">
        <div className="flex flex-col justify-center">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-6 inline-flex w-fit items-center gap-2 rounded-full border border-gold/25 bg-gold/10 px-3 py-1 text-xs font-semibold text-gold"
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-deal opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-deal" />
            </span>
            {healthyCount > 0 ? `${healthyCount} fonti live` : 'aggregatore volantini'}
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.05 }}
            className="font-display text-[clamp(2.4rem,5vw,4.2rem)] font-semibold leading-[0.98] tracking-tight text-froth text-balance"
          >
            Le offerte birra
            <br />
            che vale la pena{' '}
            <span className="italic text-gold-gradient">cercare.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.12 }}
            className="mt-5 max-w-md text-pretty text-base leading-relaxed text-muted-foreground"
          >
            Aggrega i volantini dei supermercati italiani e li ordina per{' '}
            <span className="text-froth/90">prezzo al litro</span>. Trova davvero
            l'affare, non solo lo sconto in vetrina.
          </motion.p>

          <div className="rule-gold my-7 w-44 rounded-full" />

          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <SearchBar {...search} />
            <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
              <Sparkles className="h-3.5 w-3.5 text-gold/70" />
              Prova: Milano · Roma · Napoli · Torino
            </p>
          </motion.div>
        </div>

        <div
          className="relative hidden items-center justify-center md:flex"
          style={{ perspective: 1100 }}
        >
          <motion.div
            style={{ rotateX, rotateY, transformStyle: 'preserve-3d' }}
            className="animate-float"
          >
            <BeerGlass />
          </motion.div>
        </div>
      </div>
    </Card>
  )
}
