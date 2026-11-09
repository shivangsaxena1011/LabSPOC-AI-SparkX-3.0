import re, json
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Document, DocumentChunk, Asset, ChunkVector, AssetDocumentLink
from .embeddings import embed_text, cosine

STOP = {"what", "which", "where", "when", "does", "this", "that", "with", "from", "have", "about", "tell", "show", "give", "please", "the", "and", "for", "are", "is", "can", "you", "how", "why"}

def terms(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zA-Z0-9_\-\u0900-\u097F]+", text.lower()) if len(t) > 1 and t not in STOP]

def retrieve(db: Session, query: str, limit: int = 5, asset_id: str | None = None):
    # Single eager query joining DocumentChunk, Document, and ChunkVector (eliminates N+1)
    query_stmt = (
        select(DocumentChunk, Document, ChunkVector)
        .join(Document, Document.id == DocumentChunk.document_id)
        .outerjoin(ChunkVector, ChunkVector.chunk_id == DocumentChunk.id)
        .where(Document.status == "approved")
    )

    # If linked to a specific asset, boost or prioritize linked documents
    linked_doc_ids = set()
    if asset_id:
        links = db.execute(select(AssetDocumentLink.document_id).where(AssetDocumentLink.asset_id == asset_id)).scalars().all()
        linked_doc_ids = set(links)

    rows = db.execute(query_stmt).all()
    q = set(terms(query))
    qvec = embed_text(query)
    scored = []

    for chunk, doc, vector in rows:
        words = terms(chunk.text)
        wordset = set(words)
        overlap = len(q & wordset)
        lexical = (overlap / max(1, len(q))) if q else 0.0

        semantic = 0.0
        if qvec and vector and vector.vector_json:
            try:
                vec_data = json.loads(vector.vector_json)
                semantic = max(0.0, cosine(qvec, vec_data))
            except Exception:
                semantic = 0.0

        # Base hybrid score
        if qvec:
            score = (0.65 * semantic + 0.35 * lexical)
        else:
            score = lexical + (overlap / max(1, len(wordset)) * 0.15)

        # Asset-linked document boost
        if doc.id in linked_doc_ids:
            score += 0.15

        if score > 0:
            scored.append((score, lexical, semantic, chunk, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "score": round(score, 4),
            "lexical_score": round(lex, 4),
            "semantic_score": round(sem, 4),
            "document_id": doc.id,
            "filename": doc.filename,
            "category": doc.category,
            "version": doc.version,
            "page": chunk.page_number,
            "chunk_id": chunk.id,
            "text": chunk.text
        }
        for score, lex, sem, chunk, doc in scored[:limit]
    ]

def find_asset(db: Session, hotspot_id: str | None, question: str):
    if hotspot_id:
        asset = db.get(Asset, hotspot_id)
        if asset:
            return asset
    q = set(terms(question))
    assets = db.execute(select(Asset)).scalars().all()
    ranked = []
    for a in assets:
        score = len(q & set(terms(f"{a.name} {a.description} {a.zone} {a.manufacturer} {a.model_number}")))
        if score:
            ranked.append((score, a))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked[0][1] if ranked else None
