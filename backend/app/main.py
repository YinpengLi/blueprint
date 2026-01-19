from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.api import ingest, search, packs, dropbox_auth

app = FastAPI(title="ChatGPT KB Agent (Dropbox + Hybrid Search)")
# Allow extension/browser clients to call the API. Protect ingest with INGEST_API_KEY.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

templates = Jinja2Templates(directory="app/templates")

app.include_router(ingest.router, prefix="/api/ingest")
app.include_router(search.router, prefix="/api/search")
app.include_router(packs.router, prefix="/api/context-pack")
app.include_router(dropbox_auth.router, prefix="/api/auth/dropbox")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
