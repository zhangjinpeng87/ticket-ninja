from fastapi import APIRouter, HTTPException

from shared_kb.models import KnowledgeBaseType
from ..models.ingest import IngestRequest, IngestResponse
from ..services.ingest import DataFoundryService

router = APIRouter(prefix="/ingest", tags=["data-foundry"])
service = DataFoundryService()


@router.post("", response_model=IngestResponse)
async def ingest_documents(req: IngestRequest) -> IngestResponse:
    if req.kb_type == KnowledgeBaseType.TENANT and not req.tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required when kb_type is 'tenant'")
    stats = await service.run_ingest(req)
    return IngestResponse(
        pages_crawled=stats.pages_crawled,
        pages_skipped=stats.pages_skipped,
        chunks_created=stats.chunks_created,
        entries_ingested=stats.entries_ingested,
        errors=stats.errors,
        metadata={
            "root_url": str(req.root_url),
            "category": req.category.value,
            "kb_type": req.kb_type.value,
            "tenant_id": req.tenant_id,
        },
    )

