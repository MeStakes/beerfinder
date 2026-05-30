import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** Unisce classi Tailwind in modo intelligente (dedup + merge dei conflitti). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
