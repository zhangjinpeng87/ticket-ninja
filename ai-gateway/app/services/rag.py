from typing import Dict, Any, List

# Placeholder synthesizer; replace with LangChain + LLM

def synthesize_answer(query: str, candidates: List[Dict[str, Any]], intent_scores: Dict[str, float]) -> Dict[str, Any]:
    top = candidates[:2]
    answer = (
        "Based on retrieved results, this likely relates to a resolved issue or knowledge base article. "
        "Please review the citations and try the suggested steps."
    )
    citations = [
        {"title": c["title"], "url": c.get("url"), "source_type": c.get("source_type")}
        for c in top
    ]
    kb_suggestions = [c for c in citations if c.get("source_type") == "confluence"]
    confidence = max(intent_scores.values()) if intent_scores else 0.5
    return {
        "answer": answer,
        "citations": citations,
        "kb_suggestions": kb_suggestions,
        "confidence": min(0.95, max(0.5, confidence)),
    }
