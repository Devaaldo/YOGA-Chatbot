# Mengatasi Overfitting pada Chatbot Wisata Yogyakarta

## Apa itu Overfitting?

**Overfitting** terjadi ketika model machine learning terlalu "hafal" data training dan tidak bisa generalisasi dengan baik ke data baru.

### Ciri-ciri Overfitting:
- Training accuracy sangat tinggi (>95%)
- Test accuracy jauh lebih rendah dari training accuracy
- Gap antara training dan test accuracy > 10%
- Model perform sangat baik di training data tapi buruk di real-world data

## Teknik Anti-Overfitting yang Sudah Diimplementasikan

### 1. **Cross-Validation (K-Fold)**
```python
cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
```
- Membagi data training menjadi 5 fold
- Melatih model 5 kali dengan kombinasi fold berbeda
- Memberikan estimasi performa yang lebih robust

**Interpretasi:**
- CV mean mendekati test accuracy = Good generalization
- CV std kecil (<0.05) = Model stabil

### 2. **Learning Curves**
```python
plot_learning_curve(model, model_name, X, y, cv=5)
```
Visualisasi yang menunjukkan:
- Training score vs Validation score
- Gap antara keduanya
- Apakah model butuh lebih banyak data

**Interpretasi:**
- Training curve tinggi, validation curve rendah = OVERFITTING
- Kedua curve dekat = Good generalization
- Kedua curve rendah = Underfitting (model terlalu simple)

### 3. **Regularization Techniques**

#### a) SVM Regularization
```python
SVC(C=0.5, class_weight='balanced')
```
- **C parameter**: Lower C = Stronger regularization
  - C=0.1: Very strong regularization (may underfit)
  - C=0.5: Moderate regularization (recommended)
  - C=1.0: Light regularization
  - C=5.0: Almost no regularization (may overfit)
- **class_weight='balanced'**: Handle imbalanced classes

#### b) Random Forest Regularization
```python
RandomForestClassifier(
    max_depth=15,           # Limit tree depth
    min_samples_split=10,   # Minimum samples to split
    min_samples_leaf=4,     # Minimum samples in leaf
    max_features='sqrt'     # Reduce feature correlation
)
```
- **max_depth**: Deeper trees = more overfitting
- **min_samples_split**: Higher = less overfitting
- **min_samples_leaf**: Higher = smoother decision boundaries
- **max_features**: 'sqrt' reduces correlation between trees

#### c) Neural Network Regularization
```python
MLPClassifier(
    hidden_layer_sizes=(64, 32),  # Smaller network
    alpha=0.01,                   # L2 regularization
    early_stopping=True,          # Stop when val loss increases
    validation_fraction=0.15,     # 15% for validation
    n_iter_no_change=20          # Patience for early stopping
)
```
- **alpha**: L2 penalty (higher = stronger regularization)
- **early_stopping**: Prevents overfitting to training data
- **Smaller architecture**: (64, 32) instead of (128, 64, 32)

### 4. **Overfitting Detection**
```python
check_overfitting(model, model_name, X_train, y_train, X_test, y_test)
```
Mengukur:
- Training accuracy
- Test accuracy
- Gap (Train - Test)
- Cross-validation score

**Threshold:**
- Gap < 5%: No significant overfitting ✓
- Gap 5-10%: Moderate overfitting ⚠
- Gap > 10%: High overfitting ❌

## Strategi Tambahan (Jika Masih Overfitting)

### 1. Reduce Feature Complexity
```python
# Ubah TF-IDF parameters
tfidf_vectorizer = TfidfVectorizer(
    max_features=500,     # Reduce from 1000
    min_df=2,             # Increase from 1
    max_df=0.7            # More aggressive filtering
)
```

### 2. Data Augmentation
Tambah variasi data dengan:
- **Paraphrasing**: "wisata pantai" → "tempat wisata tepi laut"
- **Synonym replacement**: "cari" → "mencari", "butuh", "perlu"
- **Back-translation**: Indonesian → English → Indonesian

### 3. Increase Training Data
- Ideal: 100+ samples per intent
- Balance class distribution
- Remove duplicate patterns

### 4. Try Simpler Models
```python
# Naive Bayes (baseline)
from sklearn.naive_bayes import MultinomialNB
nb_model = MultinomialNB()

# Logistic Regression with regularization
from sklearn.linear_model import LogisticRegression
lr_model = LogisticRegression(C=0.5, max_iter=1000)
```

### 5. Ensemble Methods
```python
from sklearn.ensemble import VotingClassifier

ensemble = VotingClassifier(
    estimators=[
        ('svm', svm_model),
        ('rf', rf_model),
        ('mlp', mlp_model)
    ],
    voting='soft'  # Use probabilities
)
```

### 6. Hyperparameter Tuning
```python
from sklearn.model_selection import GridSearchCV

# Tune SVM
param_grid = {
    'C': [0.1, 0.5, 1.0, 5.0],
    'kernel': ['linear', 'rbf']
}
grid_search = GridSearchCV(SVC(), param_grid, cv=5, scoring='accuracy')
grid_search.fit(X_train, y_train)
best_model = grid_search.best_estimator_
```

## Cara Menggunakan Notebook

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run notebook:**
   - Buka `Chatbot_Wisata_Yogyakarta.ipynb`
   - Run semua cell dari atas ke bawah
   - Perhatikan output di Section 6 (Overfitting Detection)

3. **Interpretasi hasil:**
   - Lihat **Learning Curves**: Apakah gap besar?
   - Cek **Overfitting Comparison**: Model mana yang paling balance?
   - Pilih model dengan **Generalization Score** tertinggi

4. **Jika masih overfitting:**
   - Reduce `max_features` di TF-IDF
   - Increase regularization (lower C untuk SVM, higher alpha untuk MLP)
   - Collect more training data
   - Try simpler models (Naive Bayes, Logistic Regression)

## Metrics Explained

### Training vs Test Accuracy
- **Training Accuracy**: Performa di data yang digunakan untuk training
- **Test Accuracy**: Performa di data baru yang belum pernah dilihat
- **Gap**: Selisih antara keduanya (indicator overfitting)

### Cross-Validation Score
- Mean dari 5 kali training dengan data split berbeda
- Lebih reliable daripada single test accuracy
- Standar deviasi kecil = model stabil

### Generalization Score
```
Generalization Score = Test Accuracy - Overfitting Gap
```
- Metric yang balance antara accuracy dan generalization
- Higher is better
- Digunakan untuk memilih best model

## Best Practices

1. **Always check overfitting** sebelum deploy model
2. **Use cross-validation** untuk evaluasi yang robust
3. **Plot learning curves** untuk diagnose masalah
4. **Start with simple models** (Logistic Regression, Naive Bayes)
5. **Regularization first**, data augmentation second
6. **Monitor gap** antara training dan test accuracy
7. **Balance accuracy dan generalization** saat pilih model

## Troubleshooting

### Problem: Gap > 10% (High Overfitting)
**Solutions:**
1. Reduce model complexity (smaller network, shallower trees)
2. Increase regularization (lower C, higher alpha)
3. Use more cross-validation folds
4. Collect more diverse training data

### Problem: Both Train & Test Accuracy Low (Underfitting)
**Solutions:**
1. Increase model complexity
2. Decrease regularization
3. Add more features
4. Engineer better features

### Problem: Training Slow
**Solutions:**
1. Reduce max_features in TF-IDF
2. Use smaller dataset for initial testing
3. Use simpler models (Naive Bayes)
4. Set n_jobs=-1 untuk parallel processing

## References

- [Scikit-learn: Model Selection](https://scikit-learn.org/stable/model_selection.html)
- [Cross-Validation Tutorial](https://scikit-learn.org/stable/modules/cross_validation.html)
- [Learning Curves](https://scikit-learn.org/stable/modules/learning_curve.html)
- [SVM Parameters](https://scikit-learn.org/stable/modules/svm.html)
- [Random Forest Parameters](https://scikit-learn.org/stable/modules/ensemble.html#random-forests)

## Contact & Support

Jika masih ada pertanyaan tentang overfitting atau implementasi:
1. Review notebook section 6 (Overfitting Detection)
2. Cek section 8 (Additional Anti-Overfitting Strategies)
3. Eksperimen dengan different hyperparameters
