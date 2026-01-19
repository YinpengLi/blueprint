import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from app.db import get_db
from app.security import encrypt_json, decrypt_json
from app.services.dropbox import auth_url, exchange_code

router = APIRouter()

def ensure_table(db: Session):
    db.execute(sql_text("""    CREATE TABLE IF NOT EXISTS token_store (
      id integer PRIMARY KEY DEFAULT 1,
      token_json jsonb NOT NULL
    );
    """))
    db.commit()

@router.get("/start")
async def start():
    return RedirectResponse(auth_url(str(uuid.uuid4())))

@router.get("/callback")
async def callback(code: str, state: str, db: Session = Depends(get_db)):
    ensure_table(db)
    tok = await exchange_code(code)
    enc = encrypt_json(tok)
    db.execute(sql_text("INSERT INTO token_store (id, token_json) VALUES (1, :t) ON CONFLICT (id) DO UPDATE SET token_json = EXCLUDED.token_json"), {"t": enc})
    db.commit()
    return HTMLResponse("<h3>Dropbox connected.</h3><p>You can close this tab.</p>")

@router.get("/status")
async def status(db: Session = Depends(get_db)):
    ensure_table(db)
    row = db.execute(sql_text("SELECT token_json FROM token_store WHERE id=1")).fetchone()
    return {"connected_dropbox": bool(row)}

async def get_access_token(db: Session) -> str | None:
    ensure_table(db)
    row = db.execute(sql_text("SELECT token_json FROM token_store WHERE id=1")).fetchone()
    if not row:
        return None
    tok = decrypt_json(row[0])
    return tok.get("access_token")
