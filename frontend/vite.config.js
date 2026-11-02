import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // During development, send API calls to the Python agent server
    proxy: { "/api": "http://127.0.0.1:8001" },
  },
});
