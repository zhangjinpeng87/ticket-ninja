import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'html-transform',
      transformIndexHtml(html) {
        return html.replace(
          /<script type="module" crossorigin src="([^"]+)"><\/script>/,
          '<script src="$1"></script>'
        );
      }
    }
  ],
  base: './',
  build: {
    outDir: path.resolve(__dirname, '../../build/ui'),
    assetsDir: 'assets',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        format: 'iife',
        inlineDynamicImports: true
      }
    },
    target: 'es2015',
    modulePreload: false
  },
  server: {
    port: 3000
  }
});
