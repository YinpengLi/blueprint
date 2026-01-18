from sqlalchemy import text as sql_text
from app.config import settings

def _parse_rules():
    rules = []
    for part in (settings.AUTOTAG_RULES or "").split(";"):
        part = part.strip()
        if not part or ":" not in part:
            continue
        proj, kws = part.split(":", 1)
        kws = [k.strip() for k in kws.split(",") if k.strip()]
        if proj.strip() and kws:
            rules.append((proj.strip(), kws))
    return rules

RULES = _parse_rules()

def infer_project_and_tags(text: str):
    t = (text or "").lower()
    project = None
    tags = set()
    for proj, kws in RULES:
        for kw in kws:
            if kw.lower() in t:
                project = project or proj
                tags.add(proj)
                tags.add(kw)
    for kw in ["render", "onedrive", "dashboard", "mvp", "issb", "asrs", "aassb", "translation"]:
        if kw in t:
            tags.add(kw.upper() if kw in ["issb","asrs"] else kw)
    return project, sorted(tags)

def build_tsvector(db, chunk_id: int, text_val: str):
    db.execute(sql_text("UPDATE chunk SET tsv = to_tsvector('english', :t) WHERE id = :id"), {"t": text_val, "id": chunk_id})
