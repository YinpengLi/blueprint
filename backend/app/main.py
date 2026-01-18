from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.api import ingest, search, packs, onedrive_auth

app = FastAPI(title="ChatGPT KB Agent (OneDrive + Hybrid Search)")
templates = Jinja2Templates(directory="app/templates")

app.include_router(ingest.router, prefix="/api/ingest")
app.include_router(search.router, prefix="/api/search")
app.include_router(packs.router, prefix="/api/context-pack")
app.include_router(onedrive_auth.router, prefix="/api/auth/onedrive")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
