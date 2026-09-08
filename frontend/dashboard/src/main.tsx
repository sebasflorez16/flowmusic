import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import App from './App.tsx'
import './index.css'

/**
 * Punto de entrada de la aplicación.
 *
 * Monta React en modo estricto, envuelve la app en `BrowserRouter` (React
 * Router v6) e importa los estilos globales del design system.
 */
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
