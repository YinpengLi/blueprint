# ChatGPT KB Agent (Dropbox + Render + Keyword+Semantic Search)

## Deploy to Render (no coding)
1) Push this repo to GitHub
2) Render -> New -> Blueprint -> select repo (`render.yaml` provisions web + Postgres)

### Required env vars (Render -> Web Service -> Environment)
- ENCRYPTION_KEY : base64 of 32 random bytes
- DROPBOX_APP_KEY
- DROPBOX_APP_SECRET
- DROPBOX_REDIRECT_URL : https://<your-render-url>/api/auth/dropbox/callback

Recommended
- INGEST_API_KEY : protect ingest endpoints (extension sends X-API-Key)
- EMBEDDINGS_PROVIDER : fallback (default) or openai
- OPENAI_API_KEY : required if openai

## Enable pgvector on the database (once)
From a shell where you can run psql to your Render DB:
- CREATE EXTENSION IF NOT EXISTS vector;
- CREATE EXTENSION IF NOT EXISTS pg_trgm;

## Connect Dropbox
Open:
https://<render-url>/api/auth/dropbox/start

## Folder structure in Dropbox
Root: /ChatGPT-KB
- _Raw/YYYY/MM/DD/chat_<uuid>__<slug>/
- _Notes/<Project>/<Area>/<Topic>/...__vN__<chat_id>.md
- _Files/<Project>/<Area>/<Topic>/...
- _Packs/<Project>/...
