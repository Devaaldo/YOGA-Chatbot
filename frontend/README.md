# Jelajah Jogja — Frontend (React + Vite)

Bilingual Yogyakarta tourism website with the YOGA assistant, wired to the real
NLU model + 3,399-place knowledge base via the backend API (`../api/server.py`).

## Prasyarat
- **Node.js** 18+ (cek: `node -v`). Jika `node`/`npm` tidak dikenali, buka
  terminal baru setelah instalasi Node.
- **Python** + dependensi backend: dari root project jalankan
  `pip install -r requirements.txt -r requirements-api.txt`.

## Menjalankan (2 terminal)

**Terminal 1 — Backend API (model NLU + data):**
```bash
cd C:\Users\LENOVO\code\YOGA-Chatbot
set PYTHONPATH=src           # PowerShell: $env:PYTHONPATH="src"
python -m uvicorn api.server:app --port 8000
```

**Terminal 2 — Frontend (Vite):**
```bash
cd C:\Users\LENOVO\code\YOGA-Chatbot\frontend
npm install      # sekali saja
npm run dev
```
Buka **http://localhost:5173**. Chat YOGA memanggil model asli di `:8000`.
Jika API mati, frontend tetap jalan dengan data contoh (fallback).

## Konfigurasi
- URL API diatur lewat `VITE_API_URL` (lihat `.env.example`). Default
  `http://localhost:8000`. Untuk produksi, salin ke `.env` dan arahkan ke URL
  API yang sudah dideploy.

## Build untuk produksi / deploy
```bash
npm run build      # output ke dist/
```
- Hasil `dist/` adalah situs statis — deploy gratis ke **Netlify / Cloudflare
  Pages / GitHub Pages**.
- Catatan: backend (`api/server.py`) perlu host Python sendiri yang selalu
  nyala, dan `VITE_API_URL` di build harus menunjuk ke URL backend tersebut.

## Arsitektur singkat
```
React (Vite)  ──POST /api/chat──►  FastAPI (api/server.py)
   chat.jsx                          └─ NLUPipeline (model SVM) + ActionHandler
   Explore   ──GET /api/places──►       └─ KnowledgeBase (3.399 tempat)
```
Kit UI dari Claude Design dipakai apa adanya (pola global `window.JJ*`); `src/
main.jsx` menyediakan global React, memuat kit, mengambil data asli dari API,
lalu mount. Lihat komentar di `src/main.jsx`.
