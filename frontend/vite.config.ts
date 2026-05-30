import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // In sviluppo le chiamate /api vengono inoltrate al backend FastAPI su :8000
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
