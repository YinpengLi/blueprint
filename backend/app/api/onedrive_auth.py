import uuid, time
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from app.db import get_db, Base, engine
from app.security import encrypt_json, decrypt_json
from app.services.onedrive import auth_url, exchange_code, refresh

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
    tok["expires_at"] = int(time.time()) + int(tok.get("expires_in", 3600)) - 60
    enc = encrypt_json(tok)
    db.execute(sql_text("INSERT INTO token_store (id, token_json) VALUES (1, :t) ON CONFLICT (id) DO UPDATE SET token_json = EXCLUDED.token_json"), {"t": enc})
    db.commit()
    return HTMLResponse("<h3>OneDrive connected.</h3><p>You can close this tab.</p>")

@router.get("/status")
async def status(db: Session = Depends(get_db)):
    ensure_table(db)
    row = db.execute(sql_text("SELECT token_json FROM token_store WHERE id=1")).fetchone()
    return {"connected_onedrive": bool(row)}

async def get_access_token(db: Session) -> str | None:
    ensure_table(db)
    row = db.execute(sql_text("SELECT token_json FROM token_store WHERE id=1")).fetchone()
    if not row:
        return None
    tok = decrypt_json(row[0])
    if int(tok.get("expires_at", 0)) < int(time.time()) + 60:
        newtok = await refresh(tok["refresh_token"])
        newtok["refresh_token"] = newtok.get("refresh_token", tok["refresh_token"])
        newtok["expires_at"] = int(time.time()) + int(newtok.get("expires_in", 3600)) - 60
        enc = encrypt_json(newtok)
        db.execute(sql_text("UPDATE token_store SET token_json=:t WHERE id=1"), {"t": enc})
        db.commit()
        tok = newtok
    return tok.get("access_token")
