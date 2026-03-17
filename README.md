# YOGA Chatbot — YOgyakarta Guide Assistant 

**A Telegram chatbot for recommending tourist destinations in Yogyakarta**.

This repository contains an intent-classification chatbot and utilities to enrich place data using Google Places API. The development notebook contains experiments with a hybrid TF‑IDF + SVM pipeline (used during research), while the production bot now uses the SVM hybrid pipeline by default (configurable to use an LSTM if you prefer).

---

##  Project Overview

- **Bot**: `src/telegram_bot.py` — loads a pre-trained LSTM intent classifier, Word2Vec embeddings, and a label encoder to classify user messages and reply using canned responses in `data/intents_diy_full.json`.
- **Bot (recommended)**: `src/telegram_bot_v3.py` — latest SVM-based hybrid pipeline (greeting detector + 88-class SVM). Use `src/run_telegram_v3.py` to run this version (it reads `TELEGRAM_TOKEN`).
- **Bot (alternate)**: `src/telegram_bot.py` — supports both SVM and LSTM via the `CLASSIFIER_TYPE` environment variable (default `svm`) and kept for compatibility.
- **Scraper**: `scripts/fetch_places_details.py` — uses Google Places APIs to retrieve details (ratings, opening hours, address components) for places parsed from the intents file.
- **Notebook**: `YOGA_Chatbot_Complete.ipynb` — EDA, preprocessing, feature extraction, training pipeline (dual TF-IDF hybrid pipeline and experiments). Can be used to re-train or reproduce model artifacts.

---

##  Features

- Intent classification for ~88 classes (greeting, goodbye, many `kecamatan_` intents for district-level recommendations).
- Response mapping and preview generation.
- Prediction & conversation logging for monitoring and retraining (`logs/predictions.jsonl`, `logs/conversations.jsonl`).
- Google Places scraper to enrich datasets from the intents "Top 5" lists.

---

## Repository Structure

```
├─ data/
│  ├─ intents_diy_full.json         # intent definitions & responses
│  └─ features/                     # expected: label_encoder.pickle, tfidf vectorizers
├─ models/
│  └─ greeting_detector.pkl, svm_model.pkl  # SVM artifacts expected by v3
├─ scripts/
│  └─ fetch_places_details.py      # Google Places scraping utility
├─ src/
│  ├─ telegram_bot_v3.py           # recommended SVM-based bot
│  ├─ telegram_bot.py              # alternate bot (svm/lstm)
│  └─ run_telegram_v3.py           # runner for v3
├─ logs/                           # auto-created: predictions.jsonl, conversations.jsonl
├─ requirements.txt
└─ YOGA_Chatbot_Complete.ipynb
```

---

## 🔧 Requirements

See `requirements.txt` for pinned dependencies. Minimum / tested versions include:

- Python 3.10+ (recommended)
- tensorflow==2.15.0
- python-telegram-bot==20.7
- sastrawi, numpy, pandas, scikit-learn
- python-dotenv

Install requirements:

PowerShell:

```powershell
python -m pip install -r requirements.txt
```

---

## ⚙️ Configuration

1. Create a `.env` file at the repository root (optional) OR set environment variables directly.

Examples (PowerShell):

```powershell
# For v3 runner (recommended):
$env:TELEGRAM_TOKEN = "your_token_here"

# If using src/telegram_bot.py directly (alternate):
$env:TELEGRAM_BOT_TOKEN = "your_token_here"
# Optional: choose classifier type (svm or lstm)
$env:CLASSIFIER_TYPE = "svm"
```

2. Required model artifacts (v3 / SVM pipeline):

- In `models/`:

  - `greeting_detector.pkl` — binary greeting detector (pickled sklearn model)
  - `svm_model.pkl` — main 88-class SVM classifier (pickled sklearn model)

- In `data/features/`:
  - `tfidf_greeting.pickle` — TF-IDF vectorizer for greeting detector
  - `tfidf_vectorizer.pickle` — TF-IDF vectorizer for main classifier
  - `label_encoder.pickle` — sklearn LabelEncoder

Optional LSTM artifacts (only if `CLASSIFIER_TYPE=lstm`):

- `models/yoga_lstm_best.h5`
- `data/features/word2vec.model`
- `data/features/feature_extraction_info.json` (with `max_length` and `vector_size`)

If you don't have the SVM artifacts, follow the notebook section below to export them from training outputs.

---

##  Running the Telegram Bot (Quick Start)

1. Set token in PowerShell for the current session (v3 uses `TELEGRAM_TOKEN`):

```powershell
$env:TELEGRAM_TOKEN = "<your_token_here>"
```

2. Run the v3 runner (recommended):

```powershell
python src/run_telegram_v3.py
```

Notes:

- `run_telegram_v3.py` loads `TELEGRAM_TOKEN` and starts `src/telegram_bot_v3.py` (the SVM hybrid pipeline).
- If you prefer the alternate bot entrypoint, you can set `TELEGRAM_BOT_TOKEN` and use `src/telegram_bot.py` directly; that file supports `CLASSIFIER_TYPE=svm|lstm` via env var `CLASSIFIER_TYPE`.

---

##  Scripts — Google Places Scraper

Usage (PowerShell):

```powershell
python scripts/fetch_places_details.py --api-key "YOUR_GOOGLE_PLACES_API_KEY" --intents "data/intents_diy_full.json" --output-csv "data/tourism_places_details.csv" --output-json "data/tourism_places_details.json"
```

Options:

- `--max-places N` to run on a smaller subset (useful for testing).

The script will parse `Top 5` lists from `kecamatan_` intents and query Google Places for details. Outputs: CSV and JSON files with columns like `place_name, nama, kecamatan, kabupaten, provinsi, harga, jam_buka, rating, reviews_count, phone, website, address, google_maps_url, place_id, types`.

---

##  Retrain / Reproduce Model Artifacts

The training & evaluation pipeline is in `YOGA_Chatbot_Complete.ipynb`.

Summary steps to produce artifacts used by the bot:

1. Run notebook cells (or run parts in a Python script) to:
   - Preprocess and build TF-IDF / Word2Vec / LSTM pipeline
   - Train and evaluate models
2. Export/save artifacts with these filenames/paths expected by the bot:

```python
# Example snippets to save SVM artifacts from notebook training
with open('data/features/label_encoder.pickle', 'wb') as f:
    pickle.dump(label_encoder, f)
with open('data/features/tfidf_vectorizer.pickle', 'wb') as f:
    pickle.dump(tfidf_main, f)
with open('data/features/tfidf_greeting.pickle', 'wb') as f:
    pickle.dump(tfidf_greeting, f)
with open('models/svm_model.pkl', 'wb') as f:
    pickle.dump(main_classifier, f)
with open('models/greeting_detector.pkl', 'wb') as f:
    pickle.dump(greeting_detector, f)

# Optional: save LSTM artifacts (if you train an LSTM)
model.save('models/yoga_lstm_best.h5')
word2vec_model.save('data/features/word2vec.model')
json.dump({'max_length': max_len, 'vector_size': vector_size}, open('data/features/feature_extraction_info.json','w'), ensure_ascii=False)
```

Make sure `vector_size` matches the Word2Vec vectors used when training the LSTM and `max_length` is the same padding length used in preprocessing.

---

##  Logs & Monitoring

- Predictions & model output: `logs/predictions.jsonl`
- Full conversations: `logs/conversations.jsonl`

Each entry is a JSON object (newline-delimited). Useful for error analysis and re-training.

---

##  Troubleshooting

- Missing model files: The bot raises errors if any expected artifact is absent; ensure the correct filenames and paths.
- Token issues: `TELEGRAM_BOT_TOKEN` must be set in `.env` or environment.
- `run_telegram_v3.py` is legacy and expects different variable names — prefer the direct `python -c "from src.telegram_bot import main; main()"` approach.
- Gensim Word2Vec versions must be compatible between training and inference (same vector sizes).
- TensorFlow may need a specific Python version and CPU/GPU config depending on the environment.

---

## Image Categories / Screenshot Examples

Add images to an `images/` directory and reference them here for the README. Example categories and filenames:

- [Screenshot halaman telegram] `images/telegram_chat_screenshot.png` — example bot interaction in Telegram ✅
- [Screenshot: training loss & accuracy] `images/notebook_training_plots.png` — plots from the notebook during training 📈
- [Screenshot: scraper CSV preview] `images/scraper_csv_preview.png` — sample rows of scraped place data 📋
- [Screenshot: logs preview] `images/logs_preview.png` — example entries from `logs/predictions.jsonl` and `logs/conversations.jsonl` 📝

When adding screenshots, include concise captions and alt text like: `![Screenshot halaman telegram](images/telegram_chat_screenshot.png)`.

---

##  Example Quick Tests

- Send: "Rekomendasi wisata di Bantul" → expect an intent for general tourism and a response from the corresponding intent.
- Send short greetings: "Hai" / "Selamat pagi" → greeting intents should be detected.
- If the bot replies with a clarification message, check `logs/predictions.jsonl` to see predicted probabilities.

---

## Contributing

- Add new intents to `data/intents_diy_full.json` (keep structure consistent).
- If you add `Top 5` lists in kecamatan responses, re-run the scraper to collect place metadata.

---

## Created By

- Muhammad Akbar Pradana (Devaaldo)
- Link Repository : github.com/Devaaldo/yoga
