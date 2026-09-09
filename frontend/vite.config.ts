import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: true,
    watch: {
      // Dentro de Docker en Windows/macOS el bind mount no propaga los eventos
      // del sistema de archivos: sin polling, el HMR nunca se entera de un
      // cambio. Fuera del contenedor se deja apagado, que consume CPU.
      usePolling: process.env.VITE_USE_POLLING === "true",
      interval: 300,
    },
  },
  preview: { port: 4173, host: true },
});
