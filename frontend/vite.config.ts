import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  // Ensure service worker is copied to dist
  publicDir: 'public',
  build: {
    // Ensure service worker is included in build
    rollupOptions: {
      input: {
        main: './index.html',
      },
    },
  },
})
