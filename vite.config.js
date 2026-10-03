import { defineConfig } from "vite";

// Vite serves ./frontend in dev and proxies /api calls to Flask on :5000.
export default defineConfig({
  root: "frontend",
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:5000" } },
  build: { outDir: "../dist", emptyOutDir: true },
});
