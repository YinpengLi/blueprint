# ChatGPT KB Agent (OneDrive + Render + Keyword+Semantic Search)

## What it does
- Chrome extension exports a ChatGPT conversation to your agent
- Agent stores raw snapshots + notes to OneDrive (single account)
- Agent indexes content in Postgres for keyword + semantic (pgvector) search
- Web UI at `/` supports OneDrive connect, file upload (indexed), and search
- Re-exporting the same chat URL creates version v2, v3, ... automatically

## Deploy to Render
1. Push repo to GitHub
2. Render -> New -> Blueprint -> select repo (`render.yaml` provisions web + Postgres)

### Required env vars
- ENCRYPTION_KEY : base64 of 32 random bytes
- ONEDRIVE_CLIENT_ID
- ONEDRIVE_CLIENT_SECRET
- ONEDRIVE_REDIRECT_URL : https://<render-url>/api/auth/onedrive/callback

Recommended
- INGEST_API_KEY : protect ingest endpoints (extension sends X-API-Key)
- EMBEDDINGS_PROVIDER : fallback (default) or openai
- OPENAI_API_KEY : required if openai

## OneDrive connect
Open:
https://<render-url>/api/auth/onedrive/start

## Chrome extension install
- Chrome -> chrome://extensions -> Developer mode -> Load unpacked -> select `extension/`
- Set Backend URL and API key (if you set INGEST_API_KEY)
- Click Export This Chat

## File uploads
Use `/` upload section to put PDF/DOCX/XLSX in the KB and index their contents.
For protected ingest, upload via a small curl command with X-API-Key header, or temporarily omit INGEST_API_KEY.

## Folder structure in OneDrive
Root: /ChatGPT-KB
- _Raw/YYYY/MM/DD/chat_<uuid>__<slug>/
- _Notes/<Project>/<Area>/<Topic>/...__vN__<chat_id>.md
- _Files/<Project>/<Area>/<Topic>/...
- _Packs/<Project>/...
