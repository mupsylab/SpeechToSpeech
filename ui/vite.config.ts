import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  base: "./",
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id, {  }) {
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        }
      },
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        followRedirects: true
      },
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
        rewriteWsOrigin: true
      }
    }
  }
})