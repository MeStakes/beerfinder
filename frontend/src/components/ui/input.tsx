import * as React from 'react'
import { cn } from '@/lib/utils'

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, type, ...props }, ref) => (
  <input
    type={type}
    ref={ref}
    className={cn(
      'flex h-12 w-full rounded-md border border-input bg-secondary/40 px-4 py-2 text-base text-foreground transition-colors',
      'placeholder:text-muted-foreground focus-visible:outline-none focus-visible:border-gold/50 focus-visible:ring-2 focus-visible:ring-ring/40 disabled:opacity-50',
      className
    )}
    {...props}
  />
))
Input.displayName = 'Input'
