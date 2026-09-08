import { createRoot } from 'react-dom/client'

import App from './App.tsx'
import './index.css'

/**
 * Punto de entrada de la vista TV.
 *
 * NOTA: no se usa StrictMode porque en desarrollo duplica la ejecución de los
 * efectos, lo que carga la API de YouTube IFrame dos veces y rompe la
 * comunicación por postMessage del reproductor.
 */
createRoot(document.getElementById('root')!).render(<App />)
