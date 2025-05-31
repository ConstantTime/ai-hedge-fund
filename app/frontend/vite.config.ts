import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig } from 'vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/opportunities': 'http://localhost:8000',
      '/portfolio': 'http://localhost:8000',
      '/hedge-fund': 'http://localhost:8000',
      '/ping': 'http://localhost:8000'
    }
  }
})
