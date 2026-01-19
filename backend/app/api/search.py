from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from app.db import get_db
from app.services.embeddings import embed

router = APIRouter()

@router.get("")
async def search(q: str = Query(..., min_length=1), mode: str = "hybrid", limit: int = 20, db: Session = Depends(get_db)):
    mode = (mode or "hybrid").lower()
    q = q.strip()

    keyword_rows = []
    semantic_rows = []

    if mode in ("keyword","hybrid"):
        keyword_rows = db.execute(sql_text("""            SELECT id, chat_id, chunk_text, ts_rank_cd(tsv, plainto_tsquery('english', :q)) AS k
            FROM chunk
            WHERE tsv @@ plainto_tsquery('english', :q)
            ORDER BY k DESC
            LIMIT :lim
        """), {"q": q, "lim": limit}).fetchall()

    if mode in ("semantic","hybrid"):
        emb = (await embed([q]))[0]
        semantic_rows = db.execute(sql_text("""            SELECT id, chat_id, chunk_text, 1 - (embedding <=> :e) AS s
            FROM chunk
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :e
            LIMIT :lim
        """), {"e": emb, "lim": limit}).fetchall()

    merged = {}
    for r in keyword_rows:
        merged[r[0]] = {"chunk_id": r[0], "chat_id": r[1], "text": r[2], "k": float(r[3] or 0), "s": 0.0}
    for r in semantic_rows:
        if r[0] not in merged:
            merged[r[0]] = {"chunk_id": r[0], "chat_id": r[1], "text": r[2], "k": 0.0, "s": float(r[3] or 0)}
        else:
            merged[r[0]]["s"] = float(r[3] or 0)

    items = list(merged.values())
    for it in items:
        if mode == "keyword":
            it["score"] = it["k"]
        elif mode == "semantic":
            it["score"] = it["s"]
        else:
            it["score"] = 0.45*it["k"] + 0.55*it["s"]

    items.sort(key=lambda x: x["score"], reverse=True)
    items = items[:limit]

    out = []
    for it in items:
        row = db.execute(sql_text("""            SELECT title, source_url, project, area, topic, tags, storage_note_path, version
            FROM chat_session WHERE id = :id
        """), {"id": it["chat_id"]}).fetchone()
        if not row:
            continue
        title, url, project, area, topic, tags, note_path, ver = row
        out.append({
            "score": it["score"],
            "chat_id": it["chat_id"],
            "title": title,
            "version": ver,
            "source_url": url,
            "project": project,
            "area": area,
            "topic": topic,
            "tags": tags,
            "note_path": note_path,
            "snippet": it["text"][:400].replace("\n"," ")
        })
    return {"q": q, "mode": mode, "results": out}
