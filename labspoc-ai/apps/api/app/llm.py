"""Evidence-constrained Gemini answer generation and Evidence Gate verification."""
from .config import settings
import re

def generate_grounded_answer(
    question: str,
    evidence: list[dict],
    language: str = "en",
    history: list[dict] | None = None
) -> dict:
    """
    Returns a dict with:
    {
        "answer": str | None,
        "gate_passed": bool,
        "abstention_triggered": bool,
        "reason": str,
        "citations": list[int]
    }
    """
    if settings.llm_provider.lower() != "gemini" or not settings.gemini_api_key:
        return {
            "answer": None,
            "gate_passed": False,
            "abstention_triggered": False,
            "reason": "gemini_provider_unconfigured",
            "citations": []
        }

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)

        evidence_text = "\n\n".join(
            f"[EVIDENCE {i+1}] Source: {item.get('filename', 'Structured lab record')}; "
            f"Page: {item.get('page') or 'n/a'}; Content: {item['text']}"
            for i, item in enumerate(evidence)
        )

        history_text = ""
        if history:
            turns = []
            for h in history[-4:]:  # last 4 turns for context window efficiency
                turns.append(f"Visitor: {h.get('question', '')}\nLabSPOC: {h.get('answer', '')}")
            history_text = "\nPREVIOUS CONVERSATION TURNS:\n" + "\n\n".join(turns) + "\n"

        lang_instruction = "English"
        if language == "hi" or language.startswith("hi"):
            lang_instruction = "Hindi (हिन्दी) in Devanagari script"
        elif language == "bn":
            lang_instruction = "Bengali (বাংলা)"
        elif language == "ta":
            lang_instruction = "Tamil (தமிழ்)"
        elif language == "te":
            lang_instruction = "Telugu (తెలుగు)"
        elif language == "mr":
            lang_instruction = "Marathi (मराठी)"

        prompt = f"""You are LabSPOC AI, the official virtual laboratory ambassador for the AI & ML Laboratory at Oriental Institute of Science & Technology (OIST), Bhopal.
Answer the visitor's question using ONLY the supplied approved evidence. Do not use outside knowledge or hallucinate institutional details.
If the supplied evidence does not directly support an answer or specification, you MUST state clearly that the detail is not verified in available laboratory records.
Do not invent specifications, equipment models, safety procedures, personnel, research publications, or student project outcomes.
Do not invent citation numbers. Refer to evidence strictly as [1], [2], etc., matching the exact evidence item supporting your statement.
Be polite, professional, and clear.
Target output language: {lang_instruction}.
{history_text}
VISITOR QUESTION:
{question}

APPROVED EVIDENCE:
{evidence_text}

Return only your verified answer text with appropriate citation brackets [1], [2] where facts are stated."""

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=800),
        )

        text = (response.text or "").strip()
        if not text:
            return {
                "answer": None,
                "gate_passed": False,
                "abstention_triggered": True,
                "reason": "empty_model_response",
                "citations": []
            }

        # Evidence Gate: Verify citations
        markers = [int(x) for x in re.findall(r"\[(\d+)\]", text)]
        invalid_markers = [x for x in markers if x < 1 or x > len(evidence)]
        if invalid_markers:
            return {
                "answer": None,
                "gate_passed": False,
                "abstention_triggered": False,
                "reason": f"invalid_citation_indices_{invalid_markers}",
                "citations": markers
            }

        abstention = any(term in text.lower() for term in (
            "not verified", "insufficient evidence", "cannot verify",
            "not available in the provided", "not found in the approved records",
            "no approved record", "उपलब्ध रिकॉर्ड में सत्यापित नहीं", "जानकारी उपलब्ध नहीं"
        ))

        if not markers and not abstention:
            # Rejection: factual statement made without citing any evidence or abstaining
            return {
                "answer": None,
                "gate_passed": False,
                "abstention_triggered": False,
                "reason": "uncited_factual_claim",
                "citations": []
            }

        return {
            "answer": text,
            "gate_passed": True,
            "abstention_triggered": abstention,
            "reason": "gate_passed_with_citations" if markers else "gate_passed_with_abstention",
            "citations": sorted(list(set(markers)))
        }

    except Exception as e:
        return {
            "answer": None,
            "gate_passed": False,
            "abstention_triggered": False,
            "reason": f"provider_error_{type(e).__name__}",
            "citations": []
        }
