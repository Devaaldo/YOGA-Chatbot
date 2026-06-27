
# Jelajah Jogja — Yogyakarta Tourism Assistant

<!-- The YAML block above configures the Hugging Face Space that hosts the API.
     On GitHub it just renders as a small metadata table — harmless. -->

An NLU-powered tourism assistant for **Yogyakarta (Daerah Istimewa Yogyakarta)**.
A single hybrid-SVM intent model + a 3,399-place knowledge base power **two
front-ends**:

- 🤖 **YOGA Telegram bot** — conversational recommendations in chat.
- 🌐 **Jelajah Jogja web app** — a bilingual (ID/EN) React site to browse
  destinations, with the YOGA assistant embedded.

Both talk to the same NLU pipeline, so improving the model improves both.

## Components

| Component | Path | What it is |
| --------- | ---- | ---------- |
| NLU core | `src/yoga_chatbot/` | preprocessing, entity extraction, hybrid intent classifier, knowledge base, action routing |
| Telegram bot | `src/yoga_chatbot/bot/` | python-telegram-bot front-end |
| Web API | `api/server.py` | FastAPI service exposing the model + data over HTTP |
| Web frontend | `frontend/` | React + Vite site (`Jelajah Jogja`) — see `frontend/README.md` |

## NLU Architecture

```
User input (Telegram / Web)
       |
  TextProcessor          Sastrawi stemmer + TF-IDF normalisation
       |
  EntityExtractor        Detects kecamatan / kabupaten / provinsi (78 sub-districts)
       |
  HybridIntentClassifier 3-stage SVM pipeline (94.6% 5-fold CV accuracy)
       |                   Stage 0: word-count gate
       |                   Stage 1: binary GreetingDetector
       |                   Stage 2: 12-class semantic SVM (with confidence fallback)
       |
  ActionHandler          Routes intent to the appropriate search / response method
       |
  KnowledgeBase          In-memory JSON store: 3,399 Yogyakarta tourism places
```

## Quick Start

```bash
# Clone + virtual environment
git clone <repo-url> && cd YOGA-Chatbot
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
```

### A. Telegram bot

```bash
pip install -r requirements.txt
cp .env.example .env             # then set TELEGRAM_BOT_TOKEN (from @BotFather)
set PYTHONPATH=src               # PowerShell: $env:PYTHONPATH="src"
python -m yoga_chatbot.bot.bot
```
On Windows you can also just double-click `run.bat`.

### B. Web app (API + frontend)

Two terminals — the API serves the model, the frontend serves the site.

```bash
# Terminal 1 — backend API (model + data)
pip install -r requirements.txt -r requirements-api.txt
set PYTHONPATH=src
python -m uvicorn api.server:app --port 8000

# Terminal 2 — frontend (needs Node.js 18+)
cd frontend
npm install
npm run dev                      # http://localhost:5173
```
The chat in the web app calls the real NLU model at `:8000`; if the API is off
it falls back to sample data. Full details: [`frontend/README.md`](frontend/README.md).

### Web API endpoints

| Method | Path | Purpose |
| ------ | ---- | ------- |
| `POST` | `/api/chat` | run the NLU model → reply + place cards |
| `GET`  | `/api/places` | list places (filter by `q`/`category`/`regency`/`max_price`/`min_rating`, `sort`) |
| `GET`  | `/api/places/{id}` | single place |
| `GET`  | `/api/meta` | category & regency counts |
| `GET`  | `/api/health` | liveness probe |

## Retraining the model

```bash
PYTHONPATH=src python scripts/relabel_intents.py   # raw -> semantic intents
PYTHONPATH=src python scripts/train.py             # train + save artifacts to models/
```

## Development

```bash
pip install -r requirements-dev.txt
make test          # run the pytest suite
make coverage      # tests + coverage report
```

## Project Structure

```
.
├── api/                         # FastAPI web API (server.py)
├── config/settings.py           # Centralised configuration
├── data/
│   ├── raw/                     # Source intents + raw data
│   ├── processed/               # tourism_knowledge_base.json
│   └── knowledge/               # kecamatan/kabupaten lookup
├── frontend/                    # React + Vite web app (Jelajah Jogja)
├── models/                      # Trained model artifacts (.pkl) + metadata.json
├── notebooks/                   # Training & evaluation notebook
├── scripts/
│   ├── relabel_intents.py       # raw location tags -> 12 semantic intents
│   ├── train.py                 # reproducible training pipeline (-> models/)
│   ├── augment_data.py          # data augmentation helpers
│   └── fetch_places.py          # Google Places API scraper
├── src/yoga_chatbot/
│   ├── preprocessing/           # TextProcessor (Sastrawi stemmer)
│   ├── nlu/                     # EntityExtractor, HybridIntentClassifier, NLUPipeline
│   ├── knowledge/               # KnowledgeBase (search methods)
│   ├── actions/                 # ActionHandler (intent routing)
│   └── bot/                     # Telegram handlers, keyboards, formatters
├── tests/                       # Pytest suite
├── Dockerfile / app.py          # container entry (bot)
└── run.bat                      # one-click local bot launcher (Windows)
```

## Model Performance

Metrics come from `scripts/train.py`: a stratified 5-fold cross-validation
(augmentation applied inside each fold) plus a single held-out split. TF-IDF is
fit on training data only — no leakage. See `models/metadata.json` for the exact
figures from the latest run.

| Metric                | Value                                   |
| --------------------- | --------------------------------------- |
| CV accuracy (5-fold)  | 94.58% ± 1.38%                          |
| CV macro F1 (5-fold)  | 89.73% ± 2.76%                          |
| Hold-out test accuracy| 93.99%                                  |
| Hold-out macro F1     | 87.86%                                  |
| Training samples      | 1,993 raw → 7,811 after augmentation    |
| Intent classes        | 12 (semantic)                           |
| Entity types          | kecamatan (78), kabupaten (5), provinsi |

> CV/hold-out figures evaluate the **main 12-class SVM only**. At runtime the
> greeting intents are served first by the Stage-1 binary detector, so these
> numbers slightly understate real-world greeting accuracy.

## Supported Intent Examples

| User input                   | Intent             | Entity                 |
| ---------------------------- | ------------------ | ---------------------- |
| "halo"                       | greeting           | —                      |
| "selamat pagi"               | pagi               | —                      |
| "wisata di bantul"           | rekomendasi_wisata | kabupaten: bantul      |
| "pantai di gunungkidul"      | cari_by_type       | kabupaten: gunungkidul |
| "tiket murah 30rb"           | cari_by_harga      | —                      |
| "rating terbaik"             | cari_by_rating     | —                      |
| "info candi prambanan"       | info_detail        | —                      |
| "lokasi pantai parangtritis" | info_lokasi        | —                      |

## Data Sources

- **Tourism places**: Kaggle (Indonesian Tourism Dataset) + Geoapify Places API enrichment
- **Kecamatan data**: Official administrative boundaries of DIY (78 kecamatan, 5 kabupaten/kota)
- **Intent patterns**: Manually curated + automated augmentation (synonym replacement, insertion, deletion)
