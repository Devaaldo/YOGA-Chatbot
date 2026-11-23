# Anti-Overfitting Cheatsheet

## Quick Diagnosis

| Symptom | Diagnosis | Action |
|---------|-----------|--------|
| Train: 98%, Test: 75% | **HIGH OVERFITTING** | ❌ Increase regularization |
| Train: 92%, Test: 88% | **GOOD** | ✓ Model is fine |
| Train: 75%, Test: 72% | **UNDERFITTING** | ⚠ Increase model complexity |
| Train: 85%, Test: 40% | **SEVERE OVERFITTING** | ❌ Restart with simpler model |

## Gap Thresholds

```
Gap = Training Accuracy - Test Accuracy

Gap < 5%   ✓ Excellent generalization
Gap 5-10%  ⚠ Moderate overfitting (acceptable)
Gap > 10%  ❌ High overfitting (need action)
```

## Quick Fixes by Model

### SVM
```python
# Current (may overfit)
SVC(C=1.0)

# Anti-overfitting
SVC(C=0.5, class_weight='balanced')  # ← Lower C
SVC(C=0.1)  # Even stronger regularization
```

### Random Forest
```python
# Current (may overfit)
RandomForestClassifier(max_depth=20, min_samples_split=2)

# Anti-overfitting
RandomForestClassifier(
    max_depth=10,           # ← Reduce depth
    min_samples_split=10,   # ← Increase split threshold
    min_samples_leaf=4,     # ← Increase leaf size
    max_features='sqrt'     # ← Reduce features per tree
)
```

### Neural Network
```python
# Current (may overfit)
MLPClassifier(hidden_layer_sizes=(128, 64, 32), alpha=0.0001)

# Anti-overfitting
MLPClassifier(
    hidden_layer_sizes=(64, 32),  # ← Smaller network
    alpha=0.01,                   # ← Higher L2 penalty
    early_stopping=True,          # ← Enable early stopping
    validation_fraction=0.15      # ← More validation data
)
```

## TF-IDF Anti-Overfitting

```python
# Current (may overfit)
TfidfVectorizer(max_features=1000, min_df=1)

# Anti-overfitting
TfidfVectorizer(
    max_features=500,   # ← Reduce features
    min_df=2,           # ← Ignore rare words
    max_df=0.7          # ← Ignore too common words
)
```

## Parameter Impact Matrix

| Parameter | ↑ Increase | ↓ Decrease |
|-----------|------------|------------|
| SVM: C | More overfitting | Less overfitting ✓ |
| RF: max_depth | More overfitting | Less overfitting ✓ |
| RF: min_samples_split | Less overfitting ✓ | More overfitting |
| MLP: alpha | Less overfitting ✓ | More overfitting |
| MLP: hidden_layers | More overfitting | Less overfitting ✓ |
| TF-IDF: max_features | More overfitting | Less overfitting ✓ |

## Action Priority

When overfitting is detected, try in this order:

1. **Enable cross-validation** (already done ✓)
2. **Add regularization** (tune C, alpha, max_depth)
3. **Reduce features** (lower max_features in TF-IDF)
4. **Simplify model** (fewer layers, shallower trees)
5. **Add more data** (collect or augment)
6. **Try ensemble** (VotingClassifier)

## Code Snippets

### Check Overfitting
```python
# Training accuracy
train_pred = model.predict(X_train)
train_acc = accuracy_score(y_train, train_pred)

# Test accuracy
test_pred = model.predict(X_test)
test_acc = accuracy_score(y_test, test_pred)

# Gap
gap = train_acc - test_acc
print(f"Gap: {gap:.4f}")

if gap > 0.10:
    print("❌ HIGH OVERFITTING!")
elif gap > 0.05:
    print("⚠ Moderate overfitting")
else:
    print("✓ Good generalization")
```

### Cross-Validation
```python
from sklearn.model_selection import cross_val_score

cv_scores = cross_val_score(model, X_train, y_train, cv=5)
print(f"CV Mean: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
```

### Learning Curve
```python
from sklearn.model_selection import learning_curve

train_sizes, train_scores, val_scores = learning_curve(
    model, X, y, cv=5, train_sizes=np.linspace(0.1, 1.0, 10)
)

# Plot
plt.plot(train_sizes, train_scores.mean(axis=1), label='Train')
plt.plot(train_sizes, val_scores.mean(axis=1), label='Val')
plt.legend()
plt.show()
```

## Model Selection Strategy

```python
# Score = Test Accuracy - Gap
# Higher score = Better generalization

models = {
    'SVM': {'test_acc': 0.92, 'gap': 0.03},
    'RF': {'test_acc': 0.94, 'gap': 0.12},
    'MLP': {'test_acc': 0.91, 'gap': 0.04}
}

for name, metrics in models.items():
    score = metrics['test_acc'] - metrics['gap']
    print(f"{name}: Score = {score:.4f}")

# Output:
# SVM: Score = 0.89  ← BEST (good accuracy, low gap)
# RF: Score = 0.82   (high accuracy, but high gap)
# MLP: Score = 0.87  (good balance)
```

## Hyperparameter Tuning

### Quick Grid Search
```python
from sklearn.model_selection import GridSearchCV

# SVM
param_grid = {'C': [0.1, 0.5, 1.0, 5.0]}
grid = GridSearchCV(SVC(), param_grid, cv=5)
grid.fit(X_train, y_train)
print(f"Best C: {grid.best_params_['C']}")

# Random Forest
param_grid = {'max_depth': [5, 10, 15, 20]}
grid = GridSearchCV(RandomForestClassifier(), param_grid, cv=5)
grid.fit(X_train, y_train)
print(f"Best depth: {grid.best_params_['max_depth']}")
```

## Data Augmentation Examples

```python
# Original
patterns = ["wisata pantai", "tempat wisata", "rekomendasi wisata"]

# Augmented
augmented = [
    "wisata pantai",
    "tempat wisata pantai",      # Add context
    "destinasi pantai",           # Synonym
    "objek wisata tepi laut",    # Paraphrase
    "tempat wisata",
    "lokasi wisata",              # Synonym
    "tempat rekreasi",            # Related term
    "rekomendasi wisata",
    "saran tempat wisata",        # Paraphrase
    "referensi wisata"            # Synonym
]
```

## Emergency Actions

### If Gap > 20% (Critical Overfitting)
```python
# 1. Use simplest model
from sklearn.naive_bayes import MultinomialNB
model = MultinomialNB()

# 2. Drastically reduce features
vectorizer = TfidfVectorizer(max_features=100)

# 3. Use more test data
X_train, X_test = train_test_split(X, y, test_size=0.3)

# 4. Check for data leakage
# - Duplicate samples?
# - Test data in training?
```

## Visual Indicators

### Learning Curve Interpretation
```
Training ─────────────── (high, flat)
                    ╱
Validation ────────╱ (converging)
                 ✓ Good generalization

Training ─────────────── (high, flat)

Validation ──────────── (low, flat)
                 ❌ Overfitting

Training ─────╱ (increasing)
            ╱
Validation ╱ (increasing, close)
         ✓ Need more data (underfitting)
```

## Workflow Checklist

- [ ] Load data dan split train/test (80/20)
- [ ] Train model dengan default parameters
- [ ] Calculate training accuracy
- [ ] Calculate test accuracy
- [ ] Calculate gap (train - test)
- [ ] Run cross-validation
- [ ] Plot learning curve
- [ ] If gap > 5%: Add regularization
- [ ] If gap > 10%: Reduce model complexity
- [ ] Compare multiple models
- [ ] Select based on generalization score
- [ ] Save best model

## Remember

1. **High training accuracy ≠ Good model**
2. **Test accuracy matters more than training**
3. **Generalization > Perfect fit**
4. **Simple model > Complex model** (if similar performance)
5. **Always validate with unseen data**
