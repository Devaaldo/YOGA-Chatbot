# Deploying the API

The web app is a static build (Netlify). The chat needs the FastAPI service in
`api/server.py` somewhere always-on, because the frontend calls `/api/chat`,
`/api/places` and `/api/meta` at runtime.

Current state: `frontend/netlify.toml` does not set `VITE_API_URL`, and the
Netlify site has `VITE_API_URL=https://devaaldo-yoga-chatbot.hf.space`. That
Space is private, so unauthenticated requests get 404 and the site runs in
sample mode (it says so in the footer and in the chat).

Pick one of the two paths below, then redeploy the frontend.

## Option A — Hugging Face Space (Docker)

The Dockerfile already listens on 7860, which is what the Docker SDK expects.
The image excludes `experiments/`, `frontend/`, `notebooks/` and `tests/`.

```bash
# once, with a token that has write access
hf auth login

# point the Space at this repository's files
hf upload Devaaldo/yoga-chatbot . --repo-type space \
  --exclude ".venv/**" --exclude "frontend/node_modules/**" --exclude ".git/**"

# the Space rebuilds on push; then confirm it answers
curl -s https://devaaldo-yoga-chatbot.hf.space/api/health
```

After that, either make the Space public (Settings → visibility) or set
`VITE_API_URL` in Netlify to the Space URL and rebuild.

Space README frontmatter, if the Space has its own README:

```yaml
---
title: YOGA Chatbot API
sdk: docker
app_port: 7860
---
```

## Option B — Render

`render.yaml` is a blueprint for a free web service:

1. Render dashboard → New → Blueprint → pick this repository.
2. It runs `pip install -r requirements.txt -r requirements-api.txt` and starts
   `uvicorn api.server:app` on `$PORT`, with `/api/health` as the health check.
3. Copy the service URL (for example `https://yoga-api.onrender.com`) and set
   `VITE_API_URL` in Netlify to it, then trigger a deploy.

The free plan sleeps after inactivity; the first request after a pause takes
30–50 seconds.

## Verifying a deployment

```bash
curl -s <base>/api/health          # {"status":"ok","places":2559}
curl -s <base>/api/meta | head -c 200
curl -s -X POST <base>/api/chat -H 'Content-Type: application/json' \
  -d '{"message":"pantai murah di gunungkidul","lang":"id"}'
```

`places` must be 2559. If it says 3399, the host is still running the old
catalogue with duplicates.
