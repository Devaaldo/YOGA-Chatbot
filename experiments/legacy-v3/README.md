# Legacy v3 (December 2025)

The first working chatbot, kept because the later repositories replaced it
without carrying the notebooks forward. `ORIGINAL-README.md` is the README from
that repository, describing its feature set and the four models it compared.

- `YOGA.ipynb` — 5 intents (greeting, goodbye, recommendation, place detail,
  help), dataset built from Google Maps scraping plus manual templates.
- `YOGA_Full_Pipeline.ipynb` — 10 intents plus entity extraction, the first
  version that separated "what the user wants" from "where they want it".

That second idea is the one that survived: the production model in `src/` is 12
semantic intents plus an entity extractor, which is the same split at a larger
scale. Everything else here (scrapers, dataset builders, `chatbot.py` variants)
is superseded by `scripts/` and `src/`.
