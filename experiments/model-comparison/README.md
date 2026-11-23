# Model comparison (December 2025, yoga-v2)

The stage where the chatbot stopped being a single hand-written intent list and
started comparing classifiers.

## Contents

- `Chatbot_Wisata_Yogyakarta.ipynb` — trains and compares **Linear SVM, logistic
  regression and Multinomial Naive Bayes**, prints a comparison table, and saves
  the best one.
- `Low_Performance_Analysis.ipynb` — diagnoses why greeting intents scored 0.00
  while the kecamatan intents scored 1.00.
- `chatbot_model.pkl`, `tfidf_vectorizer.pkl`, `responses_dict.pkl` — the
  artifacts that were committed to that repository.

## Discrepancy worth knowing

`chatbot_model.pkl` loads as an **MLPClassifier** (`sklearn.neural_network`),
not as the SVM, logistic regression or naive Bayes that the notebook compares.
The pickle was saved by an earlier revision of the workflow, so it does not
correspond to any cell in the notebook that ships beside it. It is kept for
provenance, not for reuse: loading it needs scikit-learn 1.3.x, while this repo
pins 1.4.2 for its own models.

The `responses_dict.pkl` holds the canned reply templates used by that bot
version. The current API builds replies from the intent and the catalogue, so
the dict is unused here.
