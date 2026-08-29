import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Port 4200 is deliberate: 3000 is PairPath's frontend and 5173 is Study
// Guider's, and 4200 is already on Code Coach's default CORS allow-list
// (backend/app/core/config.py), so the portal works against a stock backend
// with no extra configuration.
export default defineConfig({
  plugins: [react()],
  server: { port: 4200, strictPort: true },
})
