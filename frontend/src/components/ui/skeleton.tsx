import type { HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export function Skeleton({ className, style, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('animate-shimmer rounded-md bg-secondary/40', className)}
      style={{
        backgroundImage:
          'linear-gradient(90deg, transparent, hsl(42 60% 80% / 0.08), transparent)',
        backgroundSize: '200% 100%',
        ...style,
      }}
      {...props}
    />
  )
}
