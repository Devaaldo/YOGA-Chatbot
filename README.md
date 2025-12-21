# YOGA Chatbot — YOgyakarta Guide Assistant 🧘‍♀️

**A Telegram chatbot for recommending tourist destinations in Yogyakarta**.

This repository contains a trained intent-classification chatbot (LSTM) and a scraping utility to enrich place data using Google Places API. It includes training notebooks, inference code for a Telegram bot, and utilities for collecting place metadata.

---

## 🔍 Project Overview

- **Bot**: `src/telegram_bot.py` — loads a pre-trained LSTM intent classifier, Word2Vec embeddings, and a label encoder to classify user messages and reply using canned responses in `data/intents_diy_full.json`.
- **Scraper**: `scripts/fetch_places_details.py` — uses Google Places APIs to retrieve details (ratings, opening hours, address components) for places parsed from the intents file.
- **Notebook**: `YOGA_Chatbot_Complete.ipynb` — EDA, preprocessing, feature extraction, training pipeline (dual TF-IDF hybrid pipeline and experiments). Can be used to re-train or reproduce model artifacts.

---

## ✅ Features

- Intent classification for ~88 classes (greeting, goodbye, many `kecamatan_` intents for district-level recommendations).
- Response mapping and preview generation.
- Prediction & conversation logging for monitoring and retraining (`logs/predictions.jsonl`, `logs/conversations.jsonl`).
- Google Places scraper to enrich datasets from the intents "Top 5" lists.

---

## Repository Structure

```
├─ data/
│  ├─ intents_diy_full.json         # intent definitions & responses
│  └─ features/                     # expected: label_encoder.pickle, word2vec.model, feature_extraction_info.json
├─ models/
│  └─ yoga_lstm_best.h5            # expected Keras LSTM model used by the bot
├─ scripts/
│  └─ fetch_places_details.py      # Google Places scraping utility
├─ src/
│  ├─ telegram_bot.py              # Telegram bot logic and model loading
│  └─ run_telegram_v3.py           # legacy runner (see notes)
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

1. Create a `.env` file at the repository root with your Telegram Bot token:

```
TELEGRAM_BOT_TOKEN=your_token_here
```

2. Ensure the following model artifacts exist (paths expected by `src/telegram_bot.py`):

- `models/yoga_lstm_best.h5` (Keras model)
- `data/features/label_encoder.pickle` (Pickled sklearn LabelEncoder)
- `data/features/word2vec.model` (Gensim Word2Vec model)
- `data/features/feature_extraction_info.json` (JSON with at least: `{"max_length": <int>, "vector_size": <int>}`)

If you don't have them, see "Retrain / Reproduce artifacts" below.

---

## ▶️ Running the Telegram Bot (Quick Start)

1. Set token in PowerShell for the current session:

```powershell
$env:TELEGRAM_BOT_TOKEN = "<your_token_here>"
```

2. Run the bot (recommended call that works with the current structure):

```powershell
python -c "from src.telegram_bot import main; main()"
```

Notes:

- `src/run_telegram_v3.py` references `TELEGRAM_TOKEN` and `telegram_bot_v3` (which does not exist in this repo). Prefer calling `src/telegram_bot.main()` as shown above.
- If `TELEGRAM_BOT_TOKEN` is not set, the bot will log an error and exit.

---

## 🧪 Scripts — Google Places Scraper

Usage (PowerShell):

```powershell
python scripts/fetch_places_details.py --api-key "YOUR_GOOGLE_PLACES_API_KEY" --intents "data/intents_diy_full.json" --output-csv "data/tourism_places_details.csv" --output-json "data/tourism_places_details.json"
```

Options:

- `--max-places N` to run on a smaller subset (useful for testing).

The script will parse `Top 5` lists from `kecamatan_` intents and query Google Places for details. Outputs: CSV and JSON files with columns like `place_name, nama, kecamatan, kabupaten, provinsi, harga, jam_buka, rating, reviews_count, phone, website, address, google_maps_url, place_id, types`.

---

## 🔁 Retrain / Reproduce Model Artifacts

The training & evaluation pipeline is in `YOGA_Chatbot_Complete.ipynb`.

Summary steps to produce artifacts used by the bot:

1. Run notebook cells (or run parts in a Python script) to:
   - Preprocess and build TF-IDF / Word2Vec / LSTM pipeline
   - Train and evaluate models
2. Export/save artifacts with these filenames/paths expected by the bot:

```python
# Example snippets to save artifacts in the notebook or a script
model.save('models/yoga_lstm_best.h5')
with open('data/features/label_encoder.pickle', 'wb') as f:
    pickle.dump(label_encoder, f)
word2vec_model.save('data/features/word2vec.model')
# feature_extraction_info.json
json.dump({'max_length': max_len, 'vector_size': vector_size}, open('data/features/feature_extraction_info.json','w'), ensure_ascii=False)
```

Make sure `vector_size` matches the Word2Vec vectors used when training the LSTM and `max_length` is the same padding length used in preprocessing.

---

## 📂 Logs & Monitoring

- Predictions & model output: `logs/predictions.jsonl`
- Full conversations: `logs/conversations.jsonl`

Each entry is a JSON object (newline-delimited). Useful for error analysis and re-training.

---

## ⚠️ Troubleshooting

- Missing model files: The bot raises errors if any expected artifact is absent; ensure the correct filenames and paths.
- Token issues: `TELEGRAM_BOT_TOKEN` must be set in `.env` or environment.
- `run_telegram_v3.py` is legacy and expects different variable names — prefer the direct `python -c "from src.telegram_bot import main; main()"` approach.
- Gensim Word2Vec versions must be compatible between training and inference (same vector sizes).
- TensorFlow may need a specific Python version and CPU/GPU config depending on the environment.

---

## 🖼️ Image Categories / Screenshot Examples

Add images to an `images/` directory and reference them here for the README. Example categories and filenames:

- [Screenshot halaman telegram] `images/telegram_chat_screenshot.png` — example bot interaction in Telegram ✅
- [Screenshot: training loss & accuracy] `images/notebook_training_plots.png` — plots from the notebook during training 📈
- [Screenshot: scraper CSV preview] `images/scraper_csv_preview.png` — sample rows of scraped place data 📋
- [Screenshot: logs preview] `images/logs_preview.png` — example entries from `logs/predictions.jsonl` and `logs/conversations.jsonl` 📝

When adding screenshots, include concise captions and alt text like: `![Screenshot halaman telegram](images/telegram_chat_screenshot.png)`.

---

## ✅ Example Quick Tests

- Send: "Rekomendasi wisata di Bantul" → expect an intent for general tourism and a response from the corresponding intent.
- Send short greetings: "Hai" / "Selamat pagi" → greeting intents should be detected.
- If the bot replies with a clarification message, check `logs/predictions.jsonl` to see predicted probabilities.

---

## Contributing

- Add new intents to `data/intents_diy_full.json` (keep structure consistent).
- If you add `Top 5` lists in kecamatan responses, re-run the scraper to collect place metadata.

---
