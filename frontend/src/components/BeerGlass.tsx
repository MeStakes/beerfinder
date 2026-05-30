import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

// Bolle che salgono nel boccale (animate via framer-motion)
const BUBBLES = [
  { left: '34%', size: 7, delay: 0, dur: 3.4 },
  { left: '46%', size: 10, delay: 0.9, dur: 4.2 },
  { left: '58%', size: 6, delay: 1.7, dur: 3.6 },
  { left: '52%', size: 8, delay: 2.3, dur: 4.6 },
  { left: '40%', size: 5, delay: 1.2, dur: 3.0 },
  { left: '63%', size: 7, delay: 0.5, dur: 4.0 },
  { left: '48%', size: 4, delay: 2.8, dur: 3.3 },
]

/** Boccale di birra "Liquid Gold" disegnato in SVG + bolle animate. */
export function BeerGlass({ className }: { className?: string }) {
  return (
    <div className={cn('relative', className)}>
      {/* alone caldo dietro al boccale */}
      <div className="absolute left-1/2 top-1/2 h-[360px] w-[360px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,hsl(40_92%_56%/0.35),transparent_62%)] blur-2xl animate-glow-pulse" />

      <svg
        viewBox="0 0 220 320"
        className="relative h-[340px] w-[244px] drop-shadow-[0_24px_40px_rgba(0,0,0,0.55)]"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="liquid" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#fde047" />
            <stop offset="0.35" stopColor="#f5b62c" />
            <stop offset="1" stopColor="#c2740a" />
          </linearGradient>
          <linearGradient id="glass" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#ffffff" stopOpacity="0.16" />
            <stop offset="0.5" stopColor="#ffffff" stopOpacity="0.04" />
            <stop offset="1" stopColor="#ffffff" stopOpacity="0.1" />
          </linearGradient>
          <clipPath id="cup">
            <path d="M54 40 L166 40 L147 292 q-1 9 -10 9 L83 301 q-9 0 -10 -9 Z" />
          </clipPath>
        </defs>

        {/* corpo vetro */}
        <path
          d="M54 40 L166 40 L147 292 q-1 9 -10 9 L83 301 q-9 0 -10 -9 Z"
          fill="url(#glass)"
          stroke="rgba(255,255,255,0.22)"
          strokeWidth="2"
        />

        {/* liquido + bagliore interno */}
        <g clipPath="url(#cup)">
          <rect x="40" y="92" width="140" height="220" fill="url(#liquid)" />
          {/* riflesso laterale */}
          <rect x="62" y="92" width="10" height="210" fill="#fff" opacity="0.18" />
          {/* schiuma */}
          <rect x="40" y="78" width="140" height="22" fill="#fde7c4" />
          <circle cx="68" cy="80" r="13" fill="#fde7c4" />
          <circle cx="92" cy="74" r="15" fill="#fef3d6" />
          <circle cx="118" cy="77" r="14" fill="#fde7c4" />
          <circle cx="142" cy="75" r="13" fill="#fef3d6" />
          <circle cx="104" cy="82" r="12" fill="#fff8e7" />
        </g>

        {/* bordo schiuma che sborda */}
        <circle cx="70" cy="70" r="11" fill="#fef3d6" />
        <circle cx="96" cy="64" r="13" fill="#fff8e7" />
        <circle cx="124" cy="67" r="12" fill="#fef3d6" />
        <circle cx="148" cy="68" r="10" fill="#fff8e7" />

        {/* riflesso sul vetro */}
        <path
          d="M62 52 L74 52 L66 280 L56 280 Z"
          fill="#ffffff"
          opacity="0.08"
        />
      </svg>

      {/* bolle animate sopra l'SVG */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {BUBBLES.map((b, i) => (
          <motion.span
            key={i}
            className="absolute rounded-full bg-white/70"
            style={{ left: b.left, bottom: 34, width: b.size, height: b.size }}
            initial={{ y: 0, opacity: 0 }}
            animate={{ y: -200, opacity: [0, 0.9, 0] }}
            transition={{
              duration: b.dur,
              delay: b.delay,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        ))}
      </div>
    </div>
  )
}
