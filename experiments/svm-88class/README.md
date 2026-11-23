# SVM 88-class (December 2025)

The full pipeline that produced the telegram bot's 88-intent model: one intent
per kecamatan plus the usual conversation intents.

## Pipeline

| Notebook | What it produces |
| --- | --- |
| `01_Pattern_Acquisition.ipynb` | intent patterns from `data/intents_diy_full.json` and the place details |
| `02_Preprocessing.ipynb` | `data/preprocessed/preprocessed_text.csv` (Sastrawi stemming) |
| `03_Feature_Extraction.ipynb` | TF-IDF matrix (`X.npy`, `X_tfidf.npy`) and the label encoder |
| `04_SVM_Modeling.ipynb` | 88-class linear SVM, test metrics, confusion matrix |
| `04_Binary_GreetingDetector.ipynb` | binary greeting-vs-rest SVM used by the hybrid pipeline |
| `05_Evaluation.ipynb` | per-class metrics and error analysis |
| `05_Hybrid_Evaluation.ipynb` | three-stage pipeline vs the single SVM |
| `YOGA_Chatbot_Complete.ipynb` | end-to-end walkthrough in one notebook |

## Reported results

From `models/model_info.json`:

- Linear SVM, 88 classes, TF-IDF 1,000 features
- test accuracy **0.9733**, macro F1 **0.9744**, weighted F1 **0.9747**
- 1,797 train / 450 test, 1,509 support vectors

From `models/hybrid_pipeline_info.json`:

- hybrid (word-count gate, greeting detector, main SVM) accuracy **0.9756** vs
  baseline **0.9733**
- greeting F1 0.7406 baseline, 0.7638 hybrid

## Caveat

The trained SVM pickle was never committed to the old repositories, so
`models/` holds the metrics and plots only. Running `04_SVM_Modeling.ipynb`
regenerates the model. The 88 labels had roughly 25 examples each, which is why
several classes collapsed; see `notes/MANY_CLASSES_PROBLEM.md`.
