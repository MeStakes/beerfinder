/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL assoluto del backend FastAPI (Railway). Vuoto in locale (proxy Vite). */
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
