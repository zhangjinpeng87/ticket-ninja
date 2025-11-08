from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from ..services.intent import classify_intent
from ..services.retriever import retrieve_candidates
from ..services.rag import synthesize_answer
from ..services.screenshot import parse_screenshot

router = APIRouter()

class Citation(BaseModel):
    title: str
    url: Optional[str] = None
    source_type: Optional[str] = None

class AnalyzeRequest(BaseModel):
    query_text: Optional[str] = None
    screenshot_id: Optional[str] = None
    tenant_id: Optional[str] = None  # Tenant ID for tenant-specific knowledge base search
    context: Dict[str, Any] = {}

class AnalyzeResponse(BaseModel):
    answer: str
    citations: List[Citation]
    confidence: float
    kb_suggestions: List[Citation] = []
    debug: Dict[str, Any] = {}

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    text = req.query_text or ""

    screenshot_insights = None
    if req.screenshot_id:
        screenshot_insights = await parse_screenshot(req.screenshot_id)
        # Optionally merge insights into text
        if screenshot_insights and screenshot_insights.get("error_summary"):
            text = (text + "\n\n" + screenshot_insights["error_summary"]).strip()

    # Merge tenant_id into context if provided
    context = req.context.copy()
    if req.tenant_id:
        context["tenant_id"] = req.tenant_id

    intent = classify_intent(text)
    candidates = retrieve_candidates(text, context)
    synth = synthesize_answer(text, candidates, intent)

    return AnalyzeResponse(
        answer=synth["answer"],
        citations=[Citation(**c) for c in synth.get("citations", [])],
        confidence=synth.get("confidence", 0.5),
        kb_suggestions=[Citation(**c) for c in synth.get("kb_suggestions", [])],
        debug={
            "intent": intent,
            "num_candidates": len(candidates),
            "num_common_kb": len([c for c in candidates if c.get("kb_type") == "common"]),
            "num_tenant_kb": len([c for c in candidates if c.get("kb_type") == "tenant"]),
            "screenshot": screenshot_insights,
            "tenant_id": req.tenant_id,
        },
    )
