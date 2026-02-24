import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/ws': {
        target: 'http://localhost:8000',  // http:// を使う（Vite が WebSocket Upgrade を自動処理）
        ws: true,
      },
    },
  },
});
