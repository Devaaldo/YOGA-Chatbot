# Jelajah Jogja: Frontend (React + Vite)

Bilingual Yogyakarta tourism site with the YOGA assistant. It calls the real NLU
model and the de-duplicated catalogue through the backend API
(`../api/server.py`).

## Prasyarat

- **Node.js** 18+ (`node -v`). If `node`/`npm` is not recognised, open a new
  terminal after installing Node.
- **Python** plus the backend dependencies. From the repository root:
  `pip install -r requirements.txt -r requirements-api.txt`.

## Menjalankan (2 terminal)

**Terminal 1: backend API (model NLU + data), from the repository root:**

```bash
set PYTHONPATH=src           # PowerShell: $env:PYTHONPATH="src"
python -m uvicorn api.server:app --port 8000
```

**Terminal 2: frontend:**

```bash
cd frontend
npm install      # sekali saja
npm run dev
```

Open **http://localhost:5173**. The chat calls the model on `:8000`. If the API
is unreachable the site keeps its curated sample and labels itself as running in
sample mode in the footer.

## Konfigurasi

- API URL comes from `VITE_API_URL` (see `.env.example`); default
  `http://localhost:8000`. For production, set it to the deployed API URL at
  build time.

## Build untuk produksi / deploy

```bash
npm run build      # output ke dist/
```

- `dist/` is a static site, so Netlify, Cloudflare Pages or GitHub Pages all work.
- The backend needs its own always-on Python host, and `VITE_API_URL` must point
  at it during the build.

## Arsitektur singkat

```
React (Vite)  ──POST /api/chat──►  FastAPI (api/server.py)
   chat.jsx                          └─ NLUPipeline (SVM) + ActionHandler
   Explore   ──GET /api/places──►       └─ KnowledgeBase (2,559 tempat unik)
             ──GET /api/meta────►         category & regency counts
```

The UI kit is authored as global modules (`window.JJ*`, `window.JJUI`,
`window.JJSCREENS`). `src/main.jsx` provides the React globals, loads the kit in
dependency order, fetches places and counts, adapts the API payload to the kit's
place shape, then mounts the app.
