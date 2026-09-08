import { fileURLToPath, URL } from 'node:url'

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

/**
 * Configuración de Vite para el dashboard del dueño.
 *
 * - Alias `@/*` -> `src/*` (para imports limpios tipo shadcn/ui).
 * - Proxy de `/api` y `/ws` al backend Django en desarrollo, de modo que el
 *   frontend no necesite manejar CORS ni URLs absolutas en local.
 */
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
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
