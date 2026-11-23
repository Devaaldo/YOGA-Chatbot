# 🗺️ YOGA: Yogya Guide Assistant

**YOGA** adalah chatbot rekomendasi wisata Yogyakarta yang dibangun menggunakan pendekatan **Hybrid NLP System** dengan multiple model comparison untuk intent classification.

---

## ✨ Fitur Utama

### 🔍 1. Intent Classification (Multi-Model Comparison)

Sistem melakukan klasifikasi intent berdasarkan input pengguna dengan **4 model berbeda**:

**Intent Classes:**

- `greeting` - Sapaan dari user
- `goodbye` - User mengakhiri percakapan
- `rekomendasi_wisata` - User minta rekomendasi wisata
- `detail_daerah` - User tanya detail tempat tertentu
- `help` - User butuh bantuan

**Models yang dibandingkan:**

1. **TF-IDF + SVM (Linear)** - Traditional ML approach
2. **FastText Embeddings + SVM (RBF)** - Word embeddings with kernel SVM
3. **BiLSTM** - Deep learning sequential model
4. **IndoBERT (Transformer)** - State-of-the-art pretrained Indonesian BERT

### 🗺️ 2. Tourism Recommendation System

Sistem memberikan rekomendasi wisata berdasarkan:

- **Kategori wisata** (pantai, candi, museum, bukit, dll)
- **Rating Google Maps**
- **Jumlah reviews**
- **Lokasi administratif**

Fitur:

- Top-5 ranking recommendation
- Category-based filtering
- Detailed place information (rating, address, coordinates, Google Maps link)

### 📊 3. Comprehensive Dataset

#### A. Wisata Dataset (135 tempat)

Scraped dari **Google Maps API** dengan kategori:

- 23 Pantai
- 15 Candi & Sejarah
- 12 Museum
- 11 Bukit & Puncak
- 11 Taman & Rekreasi
- 11 Spot Foto & Hits
- 8 Air Terjun
- 8 Goa
- Dan lainnya...

Data yang diambil:

- Nama tempat
- Rating & jumlah reviews
- Alamat lengkap
- Koordinat (lat/lng)
- Kategori wisata

#### B. Intent Dataset (5,925 samples)

Merged dari:

- **4,921 patterns** dari dataset lama (natural, varied, with typos)
- **1,183 patterns** dari scraping + generation baru

Distribusi:

- 4,734 rekomendasi_wisata
- 698 detail_daerah
- 287 greeting
- 118 goodbye
- 88 help

---

## 📦 Project Structure

```
yoga-v3/
├── data/
│   ├── old-data/                       # Dataset lama untuk referensi
│   │   ├── intents_diy_augmented.json  # 4,921 patterns
│   │   ├── intents_diy_full.json
│   │   └── intents_diy_full_backup.json
│   ├── intent_dataset.json             # 5,925 samples (MERGED)
│   ├── intent_dataset.csv
│   ├── wisata_yogyakarta.json          # 135 tempat wisata
│   └── wisata_yogyakarta.csv
├── models/                              # Trained models
│   ├── svm_tfidf.pkl                   # TF-IDF + SVM model
│   ├── tfidf.pkl                       # TF-IDF vectorizer
│   ├── svm_ft.pkl                      # FastText + SVM model
│   ├── ft.model                        # FastText word embeddings
│   ├── lstm.h5                         # BiLSTM model
│   ├── tok.pkl                         # Keras tokenizer
│   └── le.pkl                          # Label encoder
├── venv/                                # Virtual environment
├── .env                                 # Google Maps API key
├── requirements.txt                     # Python dependencies
├── target.md                            # Project goals & documentation
├── scrape_comprehensive.py              # Google Maps scraper (135 places)
├── merge_datasets.py                    # Merge old + new intent data
├── chatbot.py                           # CLI chatbot demo
├── YOGA.ipynb                           # Main training notebook
└── README.md                            # This file
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone repository
git clone <your-repo-url>
cd yoga-v3

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Google Maps API Key

Create `.env` file:

```
GOOGLE_MAPS_API_KEY=your_api_key_here
```

Get API key from: https://console.cloud.google.com/
Enable: **Places API** & **Maps JavaScript API**

### 3. Scraping Data (Optional)

Dataset sudah tersedia, tapi kalau mau scrape ulang:

```bash
# Scrape 135 tempat wisata dari Google Maps
python scrape_comprehensive.py

# Merge dengan dataset lama
python merge_datasets.py
```

### 4. Training Models

Open dan jalankan `YOGA.ipynb` di Jupyter Notebook atau Google Colab:

```bash
jupyter notebook YOGA.ipynb
```

Atau buka di VS Code dengan Jupyter extension.

Notebook akan:

1. Load dataset (5,925 samples)
2. Preprocessing (Sastrawi stemming & stopword removal)
3. Train 4 models (TF-IDF+SVM, FastText+SVM, BiLSTM, IndoBERT)
4. Evaluate & compare (Accuracy, F1-Score, Confusion Matrix)
5. Save trained models ke folder `models/`

### 5. Run Chatbot

```bash
python chatbot.py
```

Contoh interaksi:

```
You: halo
YOGA: Hai! Mau cari rekomendasi wisata di Yogyakarta?

You: wisata di jogja
YOGA: >> Top 5 Rekomendasi Wisata di Yogyakarta:
1. Museum Batik Yogyakarta (Rating: 5.0/5, 566 reviews)
...

You: pantai di yogyakarta
YOGA: >> Top 5 Rekomendasi Pantai di Yogyakarta:
1. Pantai Krakal (Rating: 4.7/5, 2,821 reviews)
...

You: candi prambanan dimana
YOGA: >> Candi Prambanan
Rating: 4.7/5 (103,912 ulasan)
Alamat: Jl. Raya Solo - Yogyakarta, ...
Google Maps: https://www.google.com/maps?q=-7.7520206,110.4914674
```

---

## 🧪 Model Evaluation

Setiap model dievaluasi menggunakan:

- **Train/Test split** (80/20)
- **Stratified sampling**
- **Confusion Matrix**
- **Macro F1-score**
- **Per-class accuracy**

Metrics yang dibandingkan:

- Overall accuracy
- F1-score (macro average)
- Training time
- Inference speed
- Model size

Expected performance (based on large dataset):

- TF-IDF + SVM: ~92-95% accuracy
- FastText + SVM: ~90-93% accuracy
- BiLSTM: ~93-96% accuracy
- IndoBERT: ~95-98% accuracy (best)

---

## 🛠️ Technologies Used

### NLP & ML:

- **Sastrawi** - Indonesian stemming & stopword removal
- **Scikit-learn** - TF-IDF, SVM, evaluation metrics
- **Gensim** - FastText word embeddings
- **TensorFlow/Keras** - BiLSTM neural network
- **Transformers (Hugging Face)** - IndoBERT pretrained model

### Data:

- **Google Maps API** - Tourism data scraping
- **Pandas** - Data manipulation
- **NumPy** - Numerical operations

### Visualization:

- **Matplotlib** - Training curves, bar charts
- **Seaborn** - Confusion matrices, heatmaps

---

## 📈 Dataset Statistics

### Intent Dataset:

- **Total**: 5,925 samples
- **Train**: 4,740 samples (80%)
- **Test**: 1,185 samples (20%)

Distribution:

- rekomendasi_wisata: 4,734 (79.9%)
- detail_daerah: 698 (11.8%)
- greeting: 287 (4.8%)
- goodbye: 118 (2.0%)
- help: 88 (1.5%)

### Wisata Dataset:

- **Total**: 135 tourist places
- **Categories**: 14 different categories
- **Average rating**: 4.5/5
- **Total reviews**: 1,000,000+ combined

---

## 🎯 Use Cases

1. **Tourism Chatbot** - Help tourists find places in Yogyakarta
2. **NLP Research** - Compare traditional ML vs deep learning for Indonesian text
3. **Intent Classification** - Study multi-model comparison for chatbot systems
4. **Data Scraping** - Learn Google Maps API integration
5. **Educational** - Understand end-to-end NLP pipeline

---

## 🔮 Future Improvements

- [ ] Add sentiment analysis untuk reviews
- [ ] Implement RAG (Retrieval Augmented Generation) dengan LLM
- [ ] Web interface (Streamlit/Flask)
- [ ] Multi-turn conversation dengan context memory
- [ ] Personalized recommendation based on user preferences
- [ ] Add more data sources (Wikipedia, TripAdvisor, Instagram)
- [ ] Voice interface (Speech-to-Text)
- [ ] Deploy to cloud (Heroku/GCP/AWS)

---

## 📝 License

This project is for educational and research purposes.

---

## 👨‍💻 Author

**Devaaldo**

- GitHub: [@Devaaldo](https://github.com/Devaaldo)
- Email: akbarprdn2512@gmail.com

---

## 🙏 Acknowledgments

- **Sastrawi** - Indonesian NLP toolkit
- **IndoBERT** - Indonesian BERT pretrained model
- **Google Maps API** - Tourism data source
- **Hugging Face** - Transformers library

---

## 📚 References

- [Sastrawi Documentation](https://github.com/sastrawi/sastrawi)
- [IndoBERT Paper](https://arxiv.org/abs/2011.00677)
- [TF-IDF Explanation](https://scikit-learn.org/stable/modules/feature_extraction.html#tfidf-term-weighting)
- [LSTM Tutorial](https://colah.github.io/posts/2015-08-Understanding-LSTMs/)
- [Google Maps Places API](https://developers.google.com/maps/documentation/places/web-service)

---

**Happy Coding! 🚀**
