import hashlib
import numpy as np
import httpx
from app.config import settings

DIM = 1536

def _fallback(text: str) -> list[float]:
    h = hashlib.sha256(text.encode("utf-8", errors="ignore")).digest()
    rng = np.random.default_rng(int.from_bytes(h[:8], "big"))
    v = rng.normal(size=(DIM,)).astype(np.float32)
    v = v / (np.linalg.norm(v) + 1e-12)
    return v.tolist()

async def embed(texts: list[str]) -> list[list[float]]:
    provider = (settings.EMBEDDINGS_PROVIDER or "fallback").lower()
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not set")
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"model": settings.OPENAI_EMBEDDINGS_MODEL, "input": texts}
            )
            r.raise_for_status()
            return [d["embedding"] for d in r.json()["data"]]
    return [_fallback(t) for t in texts]
