from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field
from shared_kb.models import ITIssueCategory, KnowledgeBaseType


class IngestRequest(BaseModel):
    root_url: HttpUrl
    category: ITIssueCategory = ITIssueCategory.OTHER
    kb_type: KnowledgeBaseType = KnowledgeBaseType.COMMON
    tenant_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    max_depth: int = Field(2, ge=0, le=5)
    max_pages: int = Field(25, ge=1, le=200)
    allowed_domains: Optional[List[str]] = None
    include_subdomains: bool = True
    skip_assets: bool = True

    chunk_size: int = Field(1200, ge=200, le=4000)
    chunk_overlap: int = Field(200, ge=0, le=1000)

    class Config:
        use_enum_values = True


class IngestResponse(BaseModel):
    pages_crawled: int
    pages_skipped: int
    chunks_created: int
    entries_ingested: int
    errors: List[str] = []

    metadata: dict = {}

