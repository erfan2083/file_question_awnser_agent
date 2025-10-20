import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173, // Run dev server on 5173
    host: true, // Listen on all interfaces (good for Docker)
    proxy: {
      // Proxy API requests from /api to the backend server
      '/api': {
        target: 'http://backend:8000', // Use service name in Docker
        changeOrigin: true,
        // In local (non-Docker) dev, you might use:
        // target: 'http://localhost:8000',
      },
    },
  },
})