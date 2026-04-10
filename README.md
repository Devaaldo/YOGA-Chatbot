# YOGA Chatbot - Yogyakarta Guide Assistant

Telegram chatbot for tourism recommendations in Yogyakarta (Daerah Istimewa Yogyakarta).

## Architecture

```
User input (Telegram)
       |
  TextProcessor          Sastrawi stemmer + TF-IDF normalisation
       |
  EntityExtractor        Detects kecamatan / kabupaten / provinsi (78 sub-districts)
       |
  HybridIntentClassifier 3-stage SVM pipeline (97.33% accuracy)
       |                   Stage 0: word-count gate
       |                   Stage 1: binary GreetingDetector
       |                   Stage 2: 88-class main SVM
       |
  ActionHandler          Routes intent to the appropriate search / response method
       |
  KnowledgeBase          In-memory JSON store: 3,000+ Yogyakarta tourism places
       |
  Formatters + Keyboards Telegram Markdown + InlineKeyboardMarkup
```

## Quick Start

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd YOGA-Chatbot

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
make install

# 4. Configure environment variables
.env
# Edit .env and set TELEGRAM_BOT_TOKEN

# 5. Run the bot
make run
```

## Development

```bash
# Install dev dependencies (includes pytest, jupyter)
make install-dev

# Run tests
make test

# Run tests with coverage report
make coverage

# Augment training data
make augment
```

## Project Structure

```
.
├── config/
│   └── settings.py              # Centralised configuration
├── data/
│   ├── raw/                     # Original unmodified data files
│   ├── processed/               # Augmented and enriched datasets
│   └── knowledge/               # Kecamatan/kabupaten lookup data
├── models/                      # Trained model artifacts (.pkl)
├── notebooks/                   # Training and evaluation notebooks
├── scripts/
│   ├── augment_data.py          # Data augmentation pipeline
│   └── fetch_places.py          # Google Places API scraper
├── src/
│   └── yoga_chatbot/
│       ├── preprocessing/       # TextProcessor (Sastrawi stemmer)
│       ├── nlu/                 # EntityExtractor, HybridIntentClassifier, NLUPipeline
│       ├── knowledge/           # KnowledgeBase (search methods)
│       ├── actions/             # ActionHandler (intent routing)
│       └── bot/                 # Telegram handlers, keyboards, formatters
└── tests/                       # Pytest test suite
```

## Model Performance

| Metric                  | Value                                   |
| ----------------------- | --------------------------------------- |
| Test accuracy           | 97.33%                                  |
| Greeting F1 improvement | +20% (binary detector)                  |
| Training samples        | 4,921 (after augmentation)              |
| Intent classes          | 88                                      |
| Entity types            | kecamatan (78), kabupaten (5), provinsi |

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
