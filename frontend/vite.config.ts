import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 8080,
    strictPort: false,
    hmr: {
      host: 'localhost',
      port: 8080,
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
