from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from ..services.knowledge_base import get_knowledge_base_service
from ..models.knowledge_base import ITIssueCategory

router = APIRouter(prefix="/kb", tags=["knowledge-base"])


class CommonKBEntryRequest(BaseModel):
    title: str
    phenomenon: str
    root_cause_analysis: str
    solutions: List[str]
    category: ITIssueCategory
    tags: Optional[List[str]] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None


class TenantKBEntryRequest(BaseModel):
    title: str
    phenomenon: str
    root_cause_analysis: str
    solutions: List[str]
    category: ITIssueCategory
    tags: Optional[List[str]] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    ticket_key: Optional[str] = None
    ticket_id: Optional[str] = None


class KBEntryResponse(BaseModel):
    entry_id: str
    message: str


@router.post("/common", response_model=KBEntryResponse)
async def add_common_entry(entry: CommonKBEntryRequest) -> KBEntryResponse:
    """Add an entry to the common knowledge base"""
    kb_service = get_knowledge_base_service()
    entry_id = kb_service.add_common_entry(
        title=entry.title,
        phenomenon=entry.phenomenon,
        root_cause_analysis=entry.root_cause_analysis,
        solutions=entry.solutions,
        category=entry.category,
        tags=entry.tags,
        source_url=entry.source_url,
        source_type=entry.source_type,
    )
    return KBEntryResponse(
        entry_id=entry_id,
        message=f"Successfully added entry to common knowledge base"
    )


@router.post("/tenant/{tenant_id}", response_model=KBEntryResponse)
async def add_tenant_entry(tenant_id: str, entry: TenantKBEntryRequest) -> KBEntryResponse:
    """Add an entry to a tenant's knowledge base"""
    kb_service = get_knowledge_base_service()
    entry_id = kb_service.add_tenant_entry(
        tenant_id=tenant_id,
        title=entry.title,
        phenomenon=entry.phenomenon,
        root_cause_analysis=entry.root_cause_analysis,
        solutions=entry.solutions,
        category=entry.category,
        tags=entry.tags,
        source_url=entry.source_url,
        source_type=entry.source_type,
        ticket_key=entry.ticket_key,
        ticket_id=entry.ticket_id,
    )
    return KBEntryResponse(
        entry_id=entry_id,
        message=f"Successfully added entry to tenant {tenant_id} knowledge base"
    )


@router.get("/search")
async def search_knowledge_base(
    query: str,
    tenant_id: Optional[str] = None,
    common_top_k: int = 5,
    tenant_top_k: int = 5,
    min_score: float = 0.3,
    common_categories: Optional[List[ITIssueCategory]] = Query(
        None,
        description="Filter common KB search to specific categories (e.g., database, k8s, ci_cd)",
    ),
):
    """Search both common and tenant knowledge bases"""
    kb_service = get_knowledge_base_service()
    results = kb_service.search_both(
        query=query,
        tenant_id=tenant_id,
        common_top_k=common_top_k,
        tenant_top_k=tenant_top_k,
        min_score=min_score,
        common_categories=common_categories,
    )
    
    # Format results for response
    formatted_results = {
        "common": [
            {
                "entry_id": r["entry_id"],
                "title": r["entry"].title,
                "phenomenon": r["entry"].phenomenon,
                "root_cause": r["entry"].root_cause_analysis,
                "solutions": r["entry"].solutions,
                "category": r["entry"].category.value,
                "score": r["score"],
            }
            for r in results["common"]
        ],
        "tenant": [
            {
                "entry_id": r["entry_id"],
                "title": r["entry"].title,
                "phenomenon": r["entry"].phenomenon,
                "root_cause": r["entry"].root_cause_analysis,
                "solutions": r["entry"].solutions,
                "category": r["entry"].category.value,
                "ticket_key": r["entry"].ticket_key,
                "score": r["score"],
            }
            for r in results["tenant"]
        ],
    }
    
    return formatted_results


@router.get("/tenants")
async def list_tenants():
    """List all tenants that have knowledge base collections"""
    from ..services.vector_store import get_vector_store
    vector_store = get_vector_store()
    tenant_ids = vector_store.list_tenant_collections()
    return {"tenants": tenant_ids}


@router.get("/tenants/{tenant_id}/stats")
async def get_tenant_stats(tenant_id: str):
    """Get statistics for a tenant's knowledge base"""
    from ..services.vector_store import get_vector_store
    from ..models.knowledge_base import KnowledgeBaseType
    
    vector_store = get_vector_store()
    count = vector_store.count_entries(KnowledgeBaseType.TENANT, tenant_id=tenant_id)
    return {
        "tenant_id": tenant_id,
        "entry_count": count,
    }


@router.delete("/tenants/{tenant_id}")
async def delete_tenant_collection(tenant_id: str):
    """Delete a tenant's entire knowledge base collection"""
    from ..services.vector_store import get_vector_store
    vector_store = get_vector_store()
    success = vector_store.delete_tenant_collection(tenant_id)
    if success:
        return {"message": f"Successfully deleted knowledge base for tenant {tenant_id}"}
    else:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} knowledge base not found")

