"""Gemini embeddings with explicit provider-off fallback."""
from .config import settings


def embed_text(text: str) -> list[float] | None:
    if not settings.semantic_retrieval_enabled or settings.llm_provider.lower() != "gemini" or not settings.gemini_api_key:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.embed_content(model=settings.embedding_model, contents=text[:8000])
        values = getattr(response, "embeddings", None) or []
        if not values: return None
        vector = getattr(values[0], "values", None)
        return [float(x) for x in vector] if vector else None
    except Exception:
        return None


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b): return 0.0
    dot = sum(x*y for x,y in zip(a,b))
    na = sum(x*x for x in a) ** 0.5
    nb = sum(y*y for y in b) ** 0.5
    return dot / (na*nb) if na and nb else 0.0
