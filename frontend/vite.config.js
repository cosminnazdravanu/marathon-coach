// frontend/src/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const redirect127 = {
  name: 'redirect-127-to-localhost',
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      const host = req.headers.host || ''
      if (host.startsWith('127.0.0.1')) {
        const loc = `http://localhost:${server.config.server.port}${req.url || '/'}`
        res.statusCode = 302
        res.setHeader('Location', loc)
        res.end()
        return
      }
      next()
    })
  },
}

export default defineConfig({
  plugins: [redirect127, react()],
  server: { host: true, port: 5173 }, // host:true = listen on 0.0.0.0 (covers 127 & localhost)
})