def chunk_text(text: str, max_chars: int = 4500, overlap: int = 300) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    chunks = []
    i, n = 0, len(text)
    while i < n:
        j = min(n, i + max_chars)
        chunks.append(text[i:j])
        if j == n:
            break
        i = max(0, j - overlap)
    return chunks
