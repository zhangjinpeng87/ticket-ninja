from dataclasses import dataclass
from typing import List
from datetime import datetime, timezone

from shared_kb.models import KnowledgeBaseEntry, KnowledgeBaseType
from shared_kb.vector_store import get_vector_store

from ..models.ingest import IngestRequest
from .crawler import WebCrawler
from .parser import ContentProcessor


@dataclass
class IngestStats:
    pages_crawled: int = 0
    pages_skipped: int = 0
    chunks_created: int = 0
    entries_ingested: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class DataFoundryService:
    def __init__(self):
        self.crawler = WebCrawler()
        self.processor = ContentProcessor()
        self.vector_store = get_vector_store()

    async def run_ingest(self, req: IngestRequest) -> IngestStats:
        stats = IngestStats()
        pages, crawl_errors = await self.crawler.crawl(
            root_url=str(req.root_url),
            max_depth=req.max_depth,
            max_pages=req.max_pages,
            allowed_domains=req.allowed_domains,
            include_subdomains=req.include_subdomains,
            skip_assets=req.skip_assets,
        )
        stats.pages_crawled = len(pages)
        stats.errors.extend(crawl_errors)

        for page in pages:
            text = self.processor.extract_text(page.html)
            if not text:
                stats.pages_skipped += 1
                continue

            chunks = self.processor.chunk_text(text, chunk_size=req.chunk_size, overlap=req.chunk_overlap)
            stats.chunks_created += len(chunks)

            for idx, chunk in enumerate(chunks, start=1):
                entry = self._chunk_to_entry(
                    chunk_text=chunk,
                    page_title=page.title,
                    page_url=page.url,
                    chunk_index=idx,
                    req=req,
                )
                try:
                    self.vector_store.add_entry(entry)
                    stats.entries_ingested += 1
                except Exception as exc:
                    stats.errors.append(f"Failed to store chunk {page.url}#{idx}: {exc}")

        return stats

    def _chunk_to_entry(
        self,
        chunk_text: str,
        page_title: str,
        page_url: str,
        chunk_index: int,
        req: IngestRequest,
    ) -> KnowledgeBaseEntry:
        summary = self.processor.summarize(chunk_text)
        solutions = self.processor.chunk_to_solutions(chunk_text)

        kb_type = req.kb_type
        tenant_id = req.tenant_id if kb_type == KnowledgeBaseType.TENANT else None

        now = datetime.now(timezone.utc)

        title_suffix = f" (chunk {chunk_index})" if chunk_index > 1 else ""
        entry = KnowledgeBaseEntry(
            kb_type=kb_type,
            tenant_id=tenant_id,
            title=f"{page_title}{title_suffix}",
            phenomenon=summary,
            root_cause_analysis=chunk_text,
            solutions=solutions,
            category=req.category,
            tags=list(dict.fromkeys(req.tags + ["documentation"])),
            created_at=now,
            updated_at=now,
            source_url=page_url,
            source_type="documentation",
        )
        return entry

