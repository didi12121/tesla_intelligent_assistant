import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    allowedHosts: ['zhaidi.eicp.top'],
    proxy: {
      '/api': 'http://localhost:8001',
      '/tesla': 'http://localhost:8001',
    },
  },
})
