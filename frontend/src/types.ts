// Tipi condivisi — rispecchiano lo schema canonico dell'offerta del backend.

export interface SupermarketMeta {
  logo: string
  color: string
  full_name: string
}

export interface Offer {
  id: string
  name: string
  supermarket: string
  supermarket_meta: SupermarketMeta
  sale_price: number
  original_price: number | null
  discount_pct: number
  on_sale: boolean
  image_url: string
  validity: string
  link_url?: string
  price_per_liter: number | null
  source: string
  zone: string
}

export interface CacheInfo {
  cached: boolean
  age_seconds: number
  expires_in: number
  scraped_at: number
}

export interface BeersResponse {
  zone: string
  total: number
  scraping: boolean
  cache_info: CacheInfo
  offers: Offer[]
}

export interface StatsResponse {
  zone: string
  total: number
  on_sale: number
  avg_discount: number
  best_deal: Offer | null
  supermarkets?: Record<string, number>
  scraping?: boolean
}

export interface SourceHealth {
  source: string
  last_status: string
  last_items: number
  last_attempt: number
  last_error: string | null
  last_success: number | null
  last_success_items: number
  healthy: boolean
}

export interface SourcesHealthResponse {
  sources: SourceHealth[]
  count: number
  healthy_count: number
}

// Ordinamenti e filtri gestiti lato client (come l'app originale).
export type SortBy = 'discount' | 'ppl_asc' | 'price_asc' | 'price_desc' | 'name'
export type DiscountFilter = 'all' | 'sale' | '10' | '20' | '30'

export interface MarketEntry {
  name: string
  count: number
  meta: SupermarketMeta
}
