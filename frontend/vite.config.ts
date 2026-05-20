import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite configuration for the NexGenIQ frontend.
// The dev server proxies /api to the FastAPI backend on port 8000 so the
// frontend and backend can run side by side in development without CORS
// friction.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
