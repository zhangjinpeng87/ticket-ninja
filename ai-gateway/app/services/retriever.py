from typing import List, Dict, Any, Optional

from ..models import ITIssueCategory
from .knowledge_base import get_knowledge_base_service


def retrieve_candidates(query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Retrieve candidates from both common and tenant knowledge bases using vector search.
    
    Args:
        query: Search query text
        context: Context dictionary that may contain 'tenant_id'
        
    Returns:
        List of candidate entries with metadata
    """
    tenant_id = context.get("tenant_id")
    common_categories = _parse_common_categories(context)
    kb_service = get_knowledge_base_service()
    
    # Search both knowledge bases
    search_results = kb_service.search_both(
        query=query,
        tenant_id=tenant_id,
        common_top_k=5,  # Top 5 from common KB
        tenant_top_k=5,  # Top 5 from tenant KB
        min_score=0.3,  # Minimum similarity threshold
        common_categories=common_categories if common_categories else None,
    )
    
    candidates = []
    
    # Add common KB results
    for result in search_results["common"]:
        entry = result["entry"]
        candidates.append({
            "title": entry.title,
            "url": entry.source_url,
            "source_type": entry.source_type or "common_kb",
            "score": result["score"],
            "snippet": entry.phenomenon[:200] + "..." if len(entry.phenomenon) > 200 else entry.phenomenon,
            "kb_type": "common",
            "entry_id": entry.id,
            "phenomenon": entry.phenomenon,
            "root_cause": entry.root_cause_analysis,
            "solutions": entry.solutions,
            "category": entry.category.value,
        })
    
    # Add tenant KB results
    for result in search_results["tenant"]:
        entry = result["entry"]
        candidates.append({
            "title": entry.title,
            "url": entry.source_url or (f"https://example.atlassian.net/browse/{entry.ticket_key}" if entry.ticket_key else None),
            "source_type": entry.source_type or "tenant_kb",
            "score": result["score"],
            "snippet": entry.phenomenon[:200] + "..." if len(entry.phenomenon) > 200 else entry.phenomenon,
            "kb_type": "tenant",
            "entry_id": entry.id,
            "ticket_key": entry.ticket_key,
            "phenomenon": entry.phenomenon,
            "root_cause": entry.root_cause_analysis,
            "solutions": entry.solutions,
            "category": entry.category.value,
        })
    
    # Sort by score (descending) and return
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates


def _parse_common_categories(context: Dict[str, Any]) -> List[ITIssueCategory]:
    """Parse common knowledge base categories from context"""
    raw_categories = context.get("common_categories") or context.get("common_category")
    if raw_categories is None:
        return []
    
    if isinstance(raw_categories, str):
        raw_values = [raw_categories]
    elif isinstance(raw_categories, (list, tuple, set)):
        raw_values = list(raw_categories)
    else:
        return []
    
    mapping = {
        "database": ITIssueCategory.DATABASE,
        "databases": ITIssueCategory.DATABASE,
        "db": ITIssueCategory.DATABASE,
        "kubernetes": ITIssueCategory.KUBERNETES,
        "k8s": ITIssueCategory.KUBERNETES,
        "cloud": ITIssueCategory.CLOUD_INFRA,
        "cloud_infra": ITIssueCategory.CLOUD_INFRA,
        "cloud_infrastructure": ITIssueCategory.CLOUD_INFRA,
        "ci_cd": ITIssueCategory.CI_CD,
        "ci/cd": ITIssueCategory.CI_CD,
        "cicd": ITIssueCategory.CI_CD,
        "network": ITIssueCategory.NETWORK,
        "networking": ITIssueCategory.NETWORK,
        "security": ITIssueCategory.SECURITY,
        "application": ITIssueCategory.APPLICATION,
        "applications": ITIssueCategory.APPLICATION,
        "app": ITIssueCategory.APPLICATION,
        "observability": ITIssueCategory.OBSERVABILITY,
        "monitoring": ITIssueCategory.OBSERVABILITY,
        "logging": ITIssueCategory.OBSERVABILITY,
        "storage": ITIssueCategory.STORAGE,
        "other": ITIssueCategory.OTHER,
    }
    
    parsed: List[ITIssueCategory] = []
    for value in raw_values:
        if value is None:
            continue
        normalized = str(value).strip().lower().replace("-", "_")
        if normalized in mapping:
            category = mapping[normalized]
            if category not in parsed:
                parsed.append(category)
            continue
        # Try direct enum lookup
        try:
            category = ITIssueCategory(normalized)
            if category not in parsed:
                parsed.append(category)
        except ValueError:
            continue
    return parsed
