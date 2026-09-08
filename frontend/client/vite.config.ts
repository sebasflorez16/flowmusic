import { fileURLToPath, URL } from 'node:url'

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

/**
 * Configuración de Vite para la vista del cliente (PWA móvil).
 *
 * - Escucha en 0.0.0.0 para que el celular (misma red WiFi) pueda acceder.
 * - Puerto 5174 (distinto del dashboard en 5173).
 * - Proxy de /api y /ws al backend Django.
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5174,
    // Permite cualquier host (localhost, IP local, túneles ngrok, etc.) en dev.
    allowedHosts: true,
    proxy: {
      '/api': {
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
