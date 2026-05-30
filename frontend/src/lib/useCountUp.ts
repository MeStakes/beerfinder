import { useEffect, useRef, useState } from 'react'

/** Anima un numero da 0 (o dal valore precedente) fino a `target`. */
export function useCountUp(target: number, duration = 900): number {
  const [value, setValue] = useState(0)
  const fromRef = useRef(0)

  useEffect(() => {
    const from = fromRef.current
    let raf = 0
    let start: number | null = null

    const tick = (t: number) => {
      if (start === null) start = t
      const p = Math.min((t - start) / duration, 1)
      const eased = 1 - Math.pow(1 - p, 3)
      const current = Math.round(from + (target - from) * eased)
      setValue(current)
      fromRef.current = current
      if (p < 1) raf = requestAnimationFrame(tick)
    }

    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [target, duration])

  return value
}
