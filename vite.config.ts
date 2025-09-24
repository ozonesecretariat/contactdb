import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vueDevTools from "vite-plugin-vue-devtools";

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    watch: {
      followSymlinks: false,
      ignored: ["**/node_modules/**", "**/dist/**", "**/.git/**", "**/venv/**", "**/.venv/**", "'**/.fs/**'"],
      interval: 100,
      usePolling: true,
    },
  },
});
