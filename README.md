# YOGA: Yogyakarta Guide Assistant

An intent-classification chatbot for tourism in Yogyakarta, with two front-ends
sharing one NLU pipeline: a **Telegram bot** and the **Jelajah Jogja** web app.

The catalogue holds **2,559 unique destinations** after collapsing duplicated
POIs in the source data, and the intent model is a two-stage linear SVM
(94.6% accuracy, 0.89 macro F1 on a held-out split).

## Components

| Component | Path | What it is |
| --- | --- | --- |
| NLU core | `src/yoga_chatbot/` | preprocessing, entity extraction, greeting gate, intent SVM, knowledge base, action routing |
| Telegram bot | `src/yoga_chatbot/bot/` | `python-telegram-bot` front-end |
| Web API | `api/server.py` | FastAPI service exposing the model and catalogue over HTTP |
| Web frontend | `frontend/` | React + Vite site (Jelajah Jogja) |

## How a message is understood

```
User input (Telegram / Web)
       |
  TextProcessor          lowercase, strip URLs/punctuation, Sastrawi stemming
       |
  EntityExtractor        kecamatan (78) / kabupaten (5) / provinsi
       |                 earliest mention wins, so "pakem sleman" means Pakem
  HybridIntentClassifier
       |                 Stage 0  word-count gate (>3 tokens skip greetings)
       |                 Stage 1  binary greeting detector
       |                 Stage 2  12-class SVM intent (fallback under 0.15)
  ActionHandler          intent -> search / detail / itinerary
       |
  KnowledgeBase          2,559 places, de-duplicated at load
```

Location names are replaced with `[LOKASI]` before classification, so one
`rekomendasi_wisata` intent covers all 78 sub-districts instead of needing one
class per place name.

## Quick start

Requires Python 3.10–3.12 (the pinned `scikit-learn`/`numpy` versions have no
wheels for 3.13+). Model artifacts are stored in Git LFS: run `git lfs install`
once before cloning, or `git lfs pull` after, otherwise `models/*.pkl` are
pointer files and the app cannot unpickle them.

```bash
git lfs install
git clone <repo-url> && cd YOGA-Chatbot
python -m venv .venv
.venv/Scripts/activate           # macOS/Linux: source .venv/bin/activate
```

### A. Telegram bot

```bash
pip install -r requirements.txt
cp .env.example .env             # then set TELEGRAM_BOT_TOKEN from @BotFather
set PYTHONPATH=src               # PowerShell: $env:PYTHONPATH="src"
python -m yoga_chatbot.bot.bot
```

`run.bat` does the same on Windows.

### B. Web app (API + frontend)

```bash
# Terminal 1: backend (model + catalogue)
pip install -r requirements.txt -r requirements-api.txt
set PYTHONPATH=src
python -m uvicorn api.server:app --port 8000

# Terminal 2: frontend (Node 18+)
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

The site fetches places and counts from the API. With the API offline it falls
back to a small built-in sample and says so in the footer, instead of pretending
to have the full catalogue.

### API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/chat` | NLU -> reply + place cards (`message` 1–500 chars, `lang` `id`/`en`) |
| `GET` | `/api/places` | list/filter by `q`, `category`, `regency`, `max_price`, `min_rating`, `sort`, `limit` |
| `GET` | `/api/places/{id}` | single place |
| `GET` | `/api/meta` | category and regency counts |
| `GET` | `/api/health` | liveness probe + catalogue size |

## Data

- **Places**: Kaggle Indonesian tourism dataset, enriched with the Geoapify
  Places API. The two sources overlap: 3,399 raw rows collapse to 2,559 unique
  destinations (same name within ~165 m). `KnowledgeBase` performs that collapse
  on load and merges the missing fields of each duplicate group.
- **Sub-districts**: official administrative list of DIY (78 kecamatan across
  5 kabupaten/kota).
- **Intents**: manually curated patterns plus synonym/insertion/deletion
  augmentation.

Fields a place may not have (rating, ticket price, phone, website) are rendered
as "not available" rather than filled with a placeholder.

## Retraining

`scripts/train.py` is the canonical pipeline; the notebook is kept as the original
exploration only.

```bash
PYTHONPATH=src python scripts/relabel_intents.py   # raw -> 12 semantic intents
PYTHONPATH=src python scripts/train.py             # fit + save artifacts to models/
```

The script splits before augmenting, fits every vectorizer on the training split
only, and applies the same location-placeholder + stemming transform used at
inference time, so the reported metrics are not inflated by leakage.

## Model performance

Figures from `models/metadata.json` (the shipped artifacts):

| Metric | Value |
| --- | --- |
| Held-out accuracy | 94.59% |
| Held-out macro F1 | 89.46% |
| Training samples | 1,993 raw -> 7,759 augmented |
| Held-out samples | 499 |
| Intent classes | 12 |
| Entity types | 78 kecamatan, 5 kabupaten/kota, 1 provinsi |

## Model history

This chatbot was trained more than once. The experiments live in
[`experiments/`](experiments/README.md) so the notebooks and their numbers stay
with the code:

| Track | Model | Result |
| --- | --- | --- |
| `experiments/lstm-88class/` | Bidirectional LSTM on Word2Vec sequences, 88 intents | 96.35% test accuracy (985 samples) |
| `experiments/svm-88class/` | Linear SVM + hybrid greeting pipeline, 88 intents | 97.33% test accuracy (450 samples) |
| `experiments/model-comparison/` | SVM vs logistic regression vs naive Bayes | comparison notebook, no recorded winner |
| `experiments/legacy-v3/` | First pipeline, 5 then 10 intents | exploratory, no recorded metric |

Those runs used different datasets and splits, so the percentages are not
comparable to each other or to the production model. The production 12-class
setup exists because 88 intents with ~25 examples each collapsed on several
classes; `experiments/svm-88class/notes/MANY_CLASSES_PROBLEM.md` records that
diagnosis.

## Development

```bash
pip install -r requirements-dev.txt
make test          # pytest
make coverage      # pytest + coverage report
cd frontend && npm run build
```

CI runs the Python suite and the frontend production build on every push
(`.github/workflows/ci.yml`).

## Project structure

```
.
├── api/server.py                # FastAPI app
├── config/settings.py           # environment-driven configuration
├── data/
│   ├── raw/                     # intent patterns + original place list
│   ├── processed/               # tourism_knowledge_base.json (runtime data)
│   └── knowledge/               # kecamatan lookup
├── experiments/                 # earlier training tracks (SVM, LSTM, v3)
├── frontend/                    # React + Vite app
├── models/                      # fitted artifacts + metadata.json
├── notebooks/                   # original training exploration
├── scripts/                     # relabel, train, augment, place scraper
├── src/yoga_chatbot/
│   ├── preprocessing/           # TextProcessor
│   ├── nlu/                     # EntityExtractor, HybridIntentClassifier, pipeline
│   ├── knowledge/               # KnowledgeBase + de-duplication
│   ├── actions/                 # intent routing
│   └── bot/                     # Telegram handlers, keyboards, formatters
├── tests/                       # pytest suite
├── Dockerfile / app.py          # container entry (bot + health port)
└── run.bat                      # one-click Windows launcher
```

## License

MIT, see [`LICENSE`](LICENSE).
