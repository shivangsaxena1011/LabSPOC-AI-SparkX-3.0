"""Evidence-constrained Gemini answer generation. Never called without retrieved evidence."""
from .config import settings
import re


def generate_grounded_answer(question: str, evidence: list[dict], language: str = "en") -> str | None:
    if settings.llm_provider.lower() != "gemini" or not settings.gemini_api_key:
        return None
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=settings.gemini_api_key)
        evidence_text = "\n\n".join(
            f"[EVIDENCE {i+1}] Source: {item.get('filename', 'Structured lab record')}; "
            f"Page: {item.get('page') or 'n/a'}; Content: {item['text']}"
            for i, item in enumerate(evidence)
        )
        prompt = f"""You are LabSPOC AI, an assistant for the OIST Bhopal AI & ML Laboratory.
Answer the user's question using ONLY the supplied evidence. Do not use outside knowledge.
If evidence does not directly support a detail, say it is not verified in the available lab records.
Do not invent equipment specifications, availability, safety procedures, people, publications, or project outcomes.
Do not invent citations. Refer to evidence as [1], [2], etc. only when the corresponding evidence supports the statement.
Be concise, useful to a laboratory visitor, and answer in language code/name: {language}.

USER QUESTION:
{question}

APPROVED EVIDENCE:
{evidence_text}

Return only the answer text."""
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=700),
        )
        text = (response.text or "").strip()
        if not text:
            return None
        # Evidence gate: reject fabricated/out-of-range numeric source markers.
        markers = [int(x) for x in re.findall(r"\[(\d+)\]", text)]
        if any(index < 1 or index > len(evidence) for index in markers):
            return None
        abstention = any(term in text.lower() for term in ("not verified", "insufficient evidence", "cannot verify", "not available in the provided"))
        if not markers and not abstention:
            return None
        return text
    except Exception:
        # Provider failures must not break the evidence-only fallback.
        return None
