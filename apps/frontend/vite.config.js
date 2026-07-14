import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      recharts: path.resolve(__dirname, './src/__tests__/mockRecharts.js'),
    },
  },
  test: {
    environment: 'node', // Use node environment to avoid jsdom/cssstyle startup require ESM crash
    globals: true,
    setupFiles: [],
    alias: {
      recharts: path.resolve(__dirname, './src/__tests__/mockRecharts.js'),
    },
  },
})
