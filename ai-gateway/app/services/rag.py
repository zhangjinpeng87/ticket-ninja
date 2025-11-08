from typing import Dict, Any, List

# Placeholder synthesizer; replace with LangChain + LLM in production


def synthesize_answer(query: str, candidates: List[Dict[str, Any]], intent_scores: Dict[str, float]) -> Dict[str, Any]:
    """
    Synthesize an answer from retrieved knowledge base candidates.
    Combines information from both common and tenant knowledge bases.
    """
    if not candidates:
        return {
            "answer": "I couldn't find any relevant information in the knowledge base. Please provide more details about the issue.",
            "citations": [],
            "kb_suggestions": [],
            "confidence": 0.2,
        }
    
    # Separate common and tenant results
    common_candidates = [c for c in candidates if c.get("kb_type") == "common"]
    tenant_candidates = [c for c in candidates if c.get("kb_type") == "tenant"]
    
    # Use top candidates for synthesis
    top_common = common_candidates[:2] if common_candidates else []
    top_tenant = tenant_candidates[:2] if tenant_candidates else []
    top_all = candidates[:3]  # Top 3 overall for citations
    
    # Build answer from knowledge base entries
    answer_parts = []
    
    if top_tenant:
        answer_parts.append("Based on similar historical tickets in your organization:")
        for candidate in top_tenant[:1]:  # Use top tenant result
            answer_parts.append(f"\n**{candidate['title']}**")
            if candidate.get("root_cause"):
                answer_parts.append(f"\nRoot Cause: {candidate['root_cause']}")
            if candidate.get("solutions"):
                answer_parts.append("\nSolutions:")
                for i, solution in enumerate(candidate["solutions"][:3], 1):
                    answer_parts.append(f"{i}. {solution}")
    
    if top_common:
        if answer_parts:
            answer_parts.append("\n\nAdditionally, from the common knowledge base:")
        else:
            answer_parts.append("Based on common IT issue patterns:")
        
        for candidate in top_common[:1]:  # Use top common result
            answer_parts.append(f"\n**{candidate['title']}**")
            if candidate.get("root_cause"):
                answer_parts.append(f"\nRoot Cause: {candidate['root_cause']}")
            if candidate.get("solutions"):
                answer_parts.append("\nSolutions:")
                for i, solution in enumerate(candidate["solutions"][:3], 1):
                    answer_parts.append(f"{i}. {solution}")
    
    if not answer_parts:
        answer_parts.append("Found some relevant information. Please review the citations below.")
    
    answer = "\n".join(answer_parts)
    
    # Build citations
    citations = []
    for c in top_all:
        citations.append({
            "title": c["title"],
            "url": c.get("url"),
            "source_type": c.get("source_type", "kb"),
        })
    
    # KB suggestions (prioritize tenant KB entries)
    kb_suggestions = [
        {"title": c["title"], "url": c.get("url"), "source_type": c.get("source_type")}
        for c in top_tenant[:2] + top_common[:1]
    ]
    
    # Calculate confidence based on top scores and intent
    top_score = candidates[0]["score"] if candidates else 0.0
    intent_confidence = max(intent_scores.values()) if intent_scores else 0.5
    # Combine scores: higher if both KBs have results
    has_tenant = len(top_tenant) > 0
    has_common = len(top_common) > 0
    kb_bonus = 0.1 if (has_tenant and has_common) else 0.0
    
    confidence = min(0.95, max(0.3, (top_score * 0.6 + intent_confidence * 0.3 + kb_bonus)))
    
    return {
        "answer": answer,
        "citations": citations,
        "kb_suggestions": kb_suggestions,
        "confidence": confidence,
    }
