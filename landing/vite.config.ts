import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/** Landing page estática (se despliega en Netlify). */
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5177,
  },
})
