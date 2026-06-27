import { defineConfig } from 'vite'

// The Jelajah Jogja UI kit was authored against a global `React` (UMD style),
// so we use the CLASSIC JSX transform (React.createElement) instead of the
// automatic runtime. `window.React` is provided in src/main.jsx before the kit
// modules execute. No @vitejs/plugin-react — the kit uses window globals, not
// ES module imports, so Fast Refresh does not apply.
export default defineConfig({
  esbuild: {
    jsx: 'transform',
    jsxFactory: 'React.createElement',
    jsxFragment: 'React.Fragment',
  },
  server: {
    port: 5173,
  },
})
