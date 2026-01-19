import uuid, json, datetime, hashlib, re
from fastapi import APIRouter, Depends, Header, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from app.db import get_db, Base, engine
from app.security import require_api_key
from app.models.chat import ChatSession
from app.models.message import Message
from app.models.chunk import Chunk
from app.models.file import FileAsset
from app.services.chunking import chunk_text
from app.services.embeddings import embed
from app.services.indexer import infer_project_and_tags, build_tsvector
from app.services.file_extract import extract_text
from app.config import settings
from app.api.dropbox_auth import get_access_token
from app.services.dropbox import upload_bytes

router = APIRouter()

def slugify(s: str) -> str:
    s = (s or "chat").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60] or "chat"

def ensure_db():
    # ensure pgvector before tables
    with engine.begin() as conn:
        conn.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(sql_text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
    Base.metadata.create_all(bind=engine)

@router.on_event("startup")
def _startup():
    ensure_db()

@router.post("/chat")
async def ingest_chat(payload: dict, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    require_api_key(x_api_key)
    ensure_db()

    title = payload.get("title") or "ChatGPT Chat"
    source_url = payload.get("source_url") or payload.get("url") or ""
    captured_at = payload.get("captured_at") or datetime.datetime.utcnow().isoformat() + "Z"
    messages = payload.get("messages") or []

    full_text = "\n\n".join([m.get("text","") for m in messages if isinstance(m, dict)])
    inferred_project, inferred_tags = infer_project_and_tags((title + "\n" + full_text)[:200000])

    project = payload.get("project_hint") or inferred_project or "Unsorted"
    area = payload.get("area_hint") or "General"
    topic = payload.get("topic_hint") or "General"
    tags = set(payload.get("tags_hint") or [])
    for t in inferred_tags:
        tags.add(t)

    root_id = None
    version = 1
    if source_url:
        row = db.execute(sql_text("SELECT root_id, max(version) FROM chat_session WHERE source_url=:u GROUP BY root_id"), {"u": source_url}).fetchone()
        if row:
            root_id = row[0]
            version = int(row[1]) + 1

    chat_id = uuid.uuid4()
    if not root_id:
        root_id = chat_id

    access_token = await get_access_token(db)
    connected = bool(access_token)

    now = datetime.datetime.utcnow()
    y, mm, dd = now.strftime("%Y"), now.strftime("%m"), now.strftime("%d")
    slug = slugify(title)

    raw_base = f"{settings.KB_DROPBOX_ROOT}/_Raw/{y}/{mm}/{dd}/chat_{chat_id}__{slug}"
    note_base = f"{settings.KB_DROPBOX_ROOT}/_Notes/{project}/{area}/{topic}"
    note_name = f"{y}-{mm}-{dd}__{slug}__v{version}__{chat_id}.md"
    note_path = f"{note_base}/{note_name}"

    md_lines = [f"# {title}", "", f"- URL: {source_url}", f"- Captured: {captured_at}", f"- Version: v{version}", "", "---", ""]
    for m in messages:
        role = (m.get("role") or "unknown").lower()
        head = "## User" if role == "user" else ("## Assistant" if role == "assistant" else "## Message")
        md_lines += [head, "", m.get("text",""), "", "---", ""]
    md = "\n".join(md_lines)

    if connected:
        await upload_bytes(access_token, f"{raw_base}/conversation.json", json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
        await upload_bytes(access_token, f"{raw_base}/conversation.md", md.encode("utf-8"))
        await upload_bytes(access_token, f"{raw_base}/files_manifest.json", json.dumps(payload.get("ui_files") or [], ensure_ascii=False, indent=2).encode("utf-8"))
        await upload_bytes(access_token, note_path, md.encode("utf-8"))

    chat = ChatSession(
        id=chat_id, root_id=root_id, version=version,
        title=title, source_url=source_url, captured_at=captured_at,
        project=project, area=area, topic=topic, tags=sorted(tags),
        storage_raw_path=raw_base, storage_note_path=note_path,
        created_at=datetime.datetime.utcnow().isoformat() + "Z"
    )
    db.add(chat)
    for idx, m in enumerate(messages):
        db.add(Message(chat_id=str(chat_id), role=(m.get("role") or "unknown"), idx=idx, content_text=m.get("text",""), content_md=m.get("md")))
    db.commit()

    chunks = chunk_text(full_text)
    if chunks:
        embs = await embed(chunks)
        for i, (ct, ev) in enumerate(zip(chunks, embs)):
            c = Chunk(chat_id=str(chat_id), source_type="chat", chunk_idx=i, chunk_text=ct, embedding=ev)
            db.add(c); db.flush()
            build_tsvector(db, c.id, ct)
        db.commit()

    return {"chat_id": str(chat_id), "root_id": str(root_id), "version": version, "connected_dropbox": connected, "note_path": note_path}

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    project: str = Form("Unsorted"),
    area: str = Form("General"),
    topic: str = Form("General"),
    chat_id: str | None = Form(None),
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    require_api_key(x_api_key)
    ensure_db()

    data = await file.read()
    sha = hashlib.sha256(data).hexdigest()
    now = datetime.datetime.utcnow()
    ymd = now.strftime("%Y-%m-%d")

    access_token = await get_access_token(db)
    connected = bool(access_token)

    path = f"{settings.KB_DROPBOX_ROOT}/_Files/{project}/{area}/{topic}/{ymd}__{sha[:8]}__{file.filename}"
    if connected:
        await upload_bytes(access_token, path, data)

    text = extract_text(file.filename, data)
    fa = FileAsset(chat_id=chat_id, filename=file.filename, mime=file.content_type or "", storage_path=path, sha256=sha, extracted_text=text)
    db.add(fa); db.commit()

    if text:
        chunks = chunk_text(text)
        embs = await embed(chunks) if chunks else []
        tmp_chat = str(uuid.uuid4())
        for i, (ct, ev) in enumerate(zip(chunks, embs)):
            c = Chunk(chat_id=str(chat_id) if chat_id else tmp_chat, source_type="file", chunk_idx=i, chunk_text=ct, embedding=ev)
            db.add(c); db.flush()
            build_tsvector(db, c.id, ct)
        db.commit()

    return {"stored": True, "connected_dropbox": connected, "storage_path": path, "sha256": sha, "extracted": bool(text)}
