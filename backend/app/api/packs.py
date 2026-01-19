import datetime, re
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from app.db import get_db
from app.security import require_api_key
from app.api.dropbox_auth import get_access_token
from app.services.dropbox import upload_bytes
from app.config import settings

router = APIRouter()

def slugify(s: str) -> str:
    s = (s or "pack").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60] or "pack"

@router.post("")
async def create_pack(payload: dict, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    require_api_key(x_api_key)
    chat_ids = payload.get("chat_ids") or []
    project = payload.get("project") or "Unsorted"
    if not chat_ids:
        return {"error": "chat_ids required"}

    rows = []
    for cid in chat_ids:
        r = db.execute(sql_text("SELECT title, version, storage_note_path FROM chat_session WHERE id=:id"), {"id": cid}).fetchone()
        if r:
            rows.append((cid, r[0], r[1], r[2]))

    now = datetime.datetime.utcnow()
    ymd = now.strftime("%Y-%m-%d")
    slug = slugify(rows[0][1] if rows else "Context Pack")

    lines = [f"# Context Pack — {project}", "", f"Generated: {now.isoformat()}Z", "", "## Included Chats"]
    for cid, title, ver, note_path in rows:
        lines.append(f"- {title} (v{ver}) — {note_path}")
    lines += ["", "## Authority Summary", "- (Fill in) short summary.", "", "## Decisions / Constraints", "- (Fill in)", "", "## Open Questions", "- (Fill in)", "", "## Next Action", "- (Fill in one instruction)", ""]
    pack = "\n".join(lines)

    access_token = await get_access_token(db)
    connected = bool(access_token)
    path = f"{settings.KB_DROPBOX_ROOT}/_Packs/{project}/{ymd}__{slug}__context-pack.md"
    if connected:
        await upload_bytes(access_token, path, pack.encode("utf-8"))
    return {"connected_dropbox": connected, "storage_path": path, "pack_text": pack}
