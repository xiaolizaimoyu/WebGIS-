import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// 开发环境配置（归属：前端 C）
export default defineConfig({
  plugins: [vue()],
  resolve: {
    // 用 @/ 代替相对路径，如 import xxx from '@/api/post'
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) }
  },
  server: {
    port: 5173,
    // 开发期把 /api 与 /uploads 代理到后端 8000 端口，前端零跨域、图片可直接用 /uploads/xxx
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/uploads': { target: 'http://127.0.0.1:8000', changeOrigin: true }
    }
  }
})
