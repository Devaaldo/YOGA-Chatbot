# Mengapa Precision & F1-Score Greeting Rendah? 🔍

## Root Cause: Pattern Overlap

Masalah utama: **Pattern yang sama muncul di multiple intents**

### Contoh Konkret:

```
Intent "greeting":
- "hai", "halo", "hi", "hello"
- "hai mas", "halo kak", "hi bot"

Intent "pagi":
- "hai", "hi", "halo chatbot"  ← DUPLICATE!
- "hai mas", "hey gan"          ← DUPLICATE!
- "selamat pagi", "good morning"

Intent "siang":
- "hai", "halo"                 ← DUPLICATE LAGI!
- "selamat siang"

Intent "sore":
- "hi", "hello"                 ← DUPLICATE LAGI!
- "selamat sore"
```

### Apa yang Terjadi?

1. **Model Bingung (Confusion)**
   - Pattern "hai" bisa berarti: greeting, pagi, siang, sore, atau malam
   - Tidak ada context yang jelas untuk membedakan
   - Model harus "tebak" berdasarkan probabilitas

2. **Training Menjadi Inconsistent**
   ```
   "hai" → greeting  (50% cases)
   "hai" → pagi      (25% cases)
   "hai" → siang     (15% cases)
   "hai" → sore      (10% cases)
   ```
   Model tidak pernah 100% yakin!

3. **False Positives Meningkat**
   - User input: "hai" (sebenarnya greeting)
   - Model predict: "pagi" (karena pagi punya banyak "hai")
   - Result: **Precision turun** untuk greeting

4. **Metrics Menjadi Buruk**
   - **Precision rendah**: Banyak false positive (salah predict greeting)
   - **Recall mungkin OK**: Model masih detect beberapa greeting
   - **F1-score rendah**: Average dari precision & recall

## Solusi Cepat (5 Menit) ✅

### Option 1: Gunakan Data yang Sudah Di-clean

Jalankan notebook `Low_Performance_Analysis.ipynb` untuk generate cleaned data:

```bash
jupyter notebook Low_Performance_Analysis.ipynb
```

File output: `data/intents_diy_cleaned.json`

Lalu update path di main notebook:
```python
# Ganti ini:
with open('data/intents_diy_augmented.json', 'r', encoding='utf-8') as file:

# Jadi ini:
with open('data/intents_diy_cleaned.json', 'r', encoding='utf-8') as file:
```

**Expected improvement: +10-20% precision**

### Option 2: Hybrid Rule + ML (15 Menit)

Tambahkan rule-based pre-filtering sebelum ML:

```python
import re

def chatbot_response_hybrid(user_input):
    """Hybrid: Rules first, then ML"""

    user_lower = user_input.lower()

    # Rule 1: Time-based greetings (100% precision!)
    if re.search(r'\b(pagi|morning)\b', user_lower):
        predicted_tag = 'pagi'
        confidence = 1.0
    elif re.search(r'\b(siang|afternoon)\b', user_lower):
        predicted_tag = 'siang'
        confidence = 1.0
    elif re.search(r'\b(sore|evening)\b', user_lower):
        predicted_tag = 'sore'
        confidence = 1.0
    elif re.search(r'\b(malam|night)\b', user_lower):
        predicted_tag = 'malam'
        confidence = 1.0
    else:
        # No rule matched, use ML
        processed_input = preprocess_text(user_input)
        input_tfidf = tfidf_vectorizer.transform([processed_input])
        predicted_tag = best_model.predict(input_tfidf)[0]
        confidence = max(best_model.predict_proba(input_tfidf)[0])

    # Get response
    if predicted_tag in responses_dict:
        response = random.choice(responses_dict[predicted_tag])
    else:
        response = "Maaf, saya tidak mengerti."

    return {
        'response': response,
        'intent': predicted_tag,
        'confidence': confidence
    }
```

**Expected improvement: +20-30% precision**

### Option 3: Merge Similar Intents (30 Menit)

Gabungkan semua greeting-related intents:

```python
# Strategy 1: Merge all into "greeting_all"
greeting_all = greeting + pagi + siang + sore + malam

# Strategy 2: Keep time-specific, remove generic
# Remove "greeting" intent entirely
# Keep only: pagi, siang, sore, malam
```

Edit file JSON:
1. Merge all patterns into one "greeting" intent
2. OR remove "greeting" intent, keep only time-specific ones

**Expected improvement: +30-40% precision** (tapi kehilangan granularity)

## Solusi Jangka Panjang 🏗️

### 1. Data Cleaning Rules

**Rule**: Pattern hanya boleh ada di SATU intent

```
✅ GOOD:
- greeting: "halo apa kabar", "permisi", "bisa bantu"
- pagi: "selamat pagi", "good morning"
- siang: "selamat siang", "good afternoon"

❌ BAD:
- greeting: "hai", "halo"
- pagi: "hai", "halo", "selamat pagi"  ← DUPLICATE!
```

### 2. Pattern Design Guidelines

**Generic Greeting** (intent: greeting):
```
- "halo apa kabar"
- "hai boleh tanya"
- "permisi mau tanya"
- "bisa bantu saya?"
- "ada yang bisa bantu?"
```

**Time-Specific Greeting** (intent: pagi/siang/sore/malam):
```
- "selamat pagi"
- "pagi yoga"
- "good morning"
- TIDAK termasuk: "hai", "halo" tanpa time context
```

### 3. Hierarchical Classification

Two-stage model:

```
Stage 1: Is greeting? (binary)
├─ Yes → Stage 2
└─ No → Other intent classification

Stage 2: What type of greeting?
├─ Generic (greeting)
├─ Time-based (pagi/siang/sore/malam)
└─ Special (assalamualaikum, etc)
```

### 4. Context-Aware Patterns

Tambahkan context untuk disambiguate:

```python
# BAD (ambiguous):
patterns = ["hai", "halo", "hi"]

# GOOD (contextual):
patterns = [
    "hai yoga",
    "halo mau tanya",
    "hi boleh tanya",
    "permisi ada yang bisa bantu"
]
```

## Quick Reference: Fix Priority

### Priority 1 (DO THIS FIRST): Clean Data ⭐⭐⭐
- Time: 5 minutes
- Effort: Low
- Impact: +10-20% precision
- Method: Run Low_Performance_Analysis.ipynb

### Priority 2: Hybrid Rules ⭐⭐⭐
- Time: 15 minutes
- Effort: Medium
- Impact: +20-30% precision
- Method: Add regex pre-filtering

### Priority 3: Merge Intents ⭐⭐
- Time: 30 minutes
- Effort: Medium
- Impact: +30-40% precision (but less granularity)
- Method: Edit JSON manually

### Priority 4: Feature Engineering ⭐
- Time: 2 hours
- Effort: High
- Impact: +15-25% precision
- Method: Add pattern length, time words, etc.

### Priority 5: Hierarchical Model ⭐
- Time: 4+ hours
- Effort: Very High
- Impact: +25-35% precision
- Method: Build two-stage classifier

## Verification

After applying fixes, check these metrics:

```python
# Per-class metrics
from sklearn.metrics import classification_report

print(classification_report(y_test, y_pred))

# Look for "greeting" row:
#              precision    recall  f1-score   support
# greeting         0.95      0.92      0.93       100  ← Should improve!
```

**Good targets after fix:**
- Precision: > 0.85
- Recall: > 0.80
- F1-Score: > 0.82

## FAQ

**Q: Kenapa tidak fix di preprocessing?**
A: Preprocessing tidak bisa fix pattern overlap. Ini masalah data quality, bukan preprocessing.

**Q: Apakah overfitting menyebabkan ini?**
A: Tidak. Ini bukan overfitting. Ini **data confusion** karena duplicate patterns dengan label berbeda.

**Q: Haruskah hapus semua greeting selain time-specific?**
A: Tergantung use case. Jika chatbot perlu respond beda untuk "hai" vs "selamat pagi", keep both. Kalau tidak, merge saja.

**Q: Berapa banyak duplicate yang acceptable?**
A: Idealnya **0%**. Setiap pattern hanya boleh ada di 1 intent. Max acceptable: 5%.

**Q: Bagaimana detect duplicate di dataset besar?**
A: Run notebook `Low_Performance_Analysis.ipynb` - akan automatic detect dan report semua duplicates.

## Files

- **Low_Performance_Analysis.ipynb**: Analisis lengkap + generate cleaned data
- **intents_diy_cleaned.json**: Data yang sudah di-clean (auto-generated)
- **Chatbot_Wisata_Yogyakarta.ipynb**: Main training notebook

## Next Steps

1. ✅ Run `Low_Performance_Analysis.ipynb`
2. ✅ Check overlap report
3. ✅ Use cleaned data OR implement hybrid approach
4. ✅ Re-train model
5. ✅ Verify precision improvement
6. ✅ Deploy!

---

**TL;DR**: Greeting performance rendah karena pattern "hai", "halo", dll muncul di multiple intents (greeting, pagi, siang). **Quick fix**: Gunakan cleaned data atau hybrid rule+ML approach.
