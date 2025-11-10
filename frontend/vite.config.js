import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3010,
    strictPort: false, // 如果端口被占用，自动尝试下一个可用端口
    proxy: {
      // 将所有/api开头的请求代理到Flask后端
      '/api': {
        target: 'http://127.0.0.1:8010',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
