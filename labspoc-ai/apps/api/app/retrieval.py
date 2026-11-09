import re, json
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Document, DocumentChunk, Asset, ChunkVector
from .embeddings import embed_text, cosine

STOP = {"what","which","where","when","does","this","that","with","from","have","about","tell","show","give","please","the","and","for","are","is","can","you","how","why"}
def terms(text: str):
    return [t for t in re.findall(r"[a-zA-Z0-9_-]+", text.lower()) if len(t) > 2 and t not in STOP]

def retrieve(db: Session, query: str, limit: int = 5):
    rows = db.execute(select(DocumentChunk, Document).join(Document, Document.id == DocumentChunk.document_id).where(Document.status == "approved")).all()
    q = set(terms(query)); qvec = embed_text(query)
    scored = []
    for chunk, doc in rows:
        words = terms(chunk.text); wordset = set(words)
        overlap = len(q & wordset)
        lexical = (overlap / max(1, len(q))) if q else 0.0
        vector = db.get(ChunkVector, chunk.id)
        semantic = 0.0
        if qvec and vector:
            try: semantic = max(0.0, cosine(qvec, json.loads(vector.vector_json)))
            except Exception: semantic = 0.0
        # Hybrid scoring; lexical remains usable when Gemini embeddings are unavailable.
        score = (0.65 * semantic + 0.35 * lexical) if qvec else lexical + overlap / max(1, len(wordset)) * 0.15
        if score > 0:
            scored.append((score, lexical, semantic, chunk, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"score":round(score,4),"lexical_score":round(lex,4),"semantic_score":round(sem,4),
             "document_id":doc.id,"filename":doc.filename,"page":chunk.page_number,"chunk_id":chunk.id,"text":chunk.text}
            for score,lex,sem,chunk,doc in scored[:limit]]

def find_asset(db: Session, hotspot_id: str | None, question: str):
    if hotspot_id:
        asset = db.get(Asset, hotspot_id)
        if asset: return asset
    q = set(terms(question)); assets = db.execute(select(Asset)).scalars().all(); ranked=[]
    for a in assets:
        score = len(q & set(terms(a.name + " " + a.description + " " + a.zone)))
        if score: ranked.append((score,a))
    ranked.sort(key=lambda x:x[0], reverse=True)
    return ranked[0][1] if ranked else None
