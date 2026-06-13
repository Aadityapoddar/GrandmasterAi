import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Proxy API calls to FastAPI so CORS isn't an issue in dev
      "/solve":       "http://localhost:8000",
      "/stress-test": "http://localhost:8000",
      "/jobs":        "http://localhost:8000",
      "/health":      "http://localhost:8000",
    },
  },
});
