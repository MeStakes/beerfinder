import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'sonner'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
    <Toaster
      theme="dark"
      position="bottom-center"
      toastOptions={{
        style: {
          background: '#15100b',
          border: '1px solid hsl(34 20% 16%)',
          color: '#f4efe7',
        },
      }}
    />
  </StrictMode>,
)
