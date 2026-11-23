# LSTM 88-class (December 2025)

The neural counterpart to the SVM track: same 88 intents, but sequences of
Word2Vec embeddings fed to a Bidirectional LSTM.

## Pipeline

| Notebook | What it produces |
| --- | --- |
| `01_Pattern_Acquisition.ipynb` | augmented intent patterns (`data/intents_diy_augmented.json`) |
| `02_Preprocessing.ipynb` | cleaned and stemmed text |
| `03_Feature_Extraction.ipynb` | Word2Vec CBOW model, padded sequences (`X.npy`, `y.npy`) |
| `04_LSTM_Modeling.ipynb` | Bidirectional LSTM training, early stopping, model checkpoint |
| `05_Evaluation.ipynb` | test metrics, confusion matrix, per-class report |
| `YOGA_Chatbot_Complete.ipynb` | condensed end-to-end version |

## Architecture (from `models/model_info.json`)

- Bidirectional LSTM, units 128 → 64, dropout 0.3
- input shape 8 x 100 (sequence length 8, Word2Vec CBOW size 100, vocab 302)
- 412,824 parameters, Adam at 1e-3, categorical cross-entropy
- early stopping at epoch 67 of 200, batch 32

## Reported result

- test accuracy **0.9635**, test loss 0.1222
- 3,936 train / 985 test samples

The trained model is `models/yoga_lstm_best.h5` (5.0 MB). It is a valid HDF5
Keras archive; loading it needs TensorFlow 2.x, which is **not** in
`requirements.txt` because the production chatbot serves the SVM instead.

## The run that failed

`notes/cv_model_info.json` and `notes/cv_results.json` are from a later attempt
that added Stratified 5-fold cross-validation, widened the embeddings to 300
dimensions with a 200k vocabulary, and scored **0.3956** on the test set
(5-fold mean 0.3712 ± 0.0110). Only the JSON results are kept; the 7.2 MB model
from that run is not in this repository. That collapse is part of why the label
space was redesigned from 88 intents to 12 semantic intents.
