# Data Foundry Service

On-demand documentation ingestion service that crawls technical product docs, extracts readable content, chunks text, generates embeddings, and stores the chunks in the shared Qdrant knowledge base used by Ticket Ninja.

## Features

- Crawl a root documentation URL (HTML or XML) with depth and page limits.
- Extract readable text, strip boilerplate, and chunk into overlapping segments.
- Convert each chunk into a `KnowledgeBaseEntry` (common or tenant) with category metadata (database, kubernetes, ci/cd, etc.).
- Generate embeddings via `sentence-transformers` and persist to Qdrant collections (same layout as AI Gateway).

## Run Locally

```bash
cd data-foundry
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Ensure Qdrant is running (e.g. docker run -p 6333:6333 qdrant/qdrant)

uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `QDRANT_URL` | Qdrant endpoint | `http://localhost:6333` |
| `QDRANT_API_KEY` | Qdrant API key for cloud deployments | _unset_ |
| `EMBEDDING_MODEL` | Sentence-transformers model | `sentence-transformers/all-MiniLM-L6-v2` |

## API

### `POST /ingest`

```json
{
  "root_url": "https://example.com/docs",
  "category": "kubernetes",
  "kb_type": "common",
  "tenant_id": null,
  "tags": ["product-docs"],
  "max_depth": 2,
  "max_pages": 20,
  "chunk_size": 1200,
  "chunk_overlap": 200
}
```

**Response**

```json
{
  "pages_crawled": 5,
  "pages_skipped": 1,
  "chunks_created": 42,
  "entries_ingested": 42,
  "errors": [],
  "metadata": {
    "root_url": "https://example.com/docs",
    "category": "kubernetes",
    "kb_type": "common",
    "tenant_id": null
  }
}
```

## Collections

- Common knowledge base chunks are inserted into the same per-category collections (e.g., `kb_common_database`, `kb_common_kubernetes`).
- Tenant-specific ingestions go into `kb_tenant_{tenantId}` collections.

## Examples

### WebCrawler Usage

See `examples/crawler_example.py` for comprehensive examples of using the `WebCrawler` class directly:

```bash
cd data-foundry
python examples/crawler_example.py
```

The examples demonstrate:
- Basic crawling with default settings
- Restricting to specific domains
- Controlling subdomain inclusion
- Deep crawling with higher depth limits
- Error handling and inspection
- Content preview before processing

### Quick WebCrawler Example

```python
from app.services.crawler import WebCrawler

async def crawl_docs():
    crawler = WebCrawler(timeout=15.0)
    pages, errors = await crawler.crawl(
        root_url="https://docs.example.com",
        max_depth=2,
        max_pages=10,
        allowed_domains=["docs.example.com"],
        include_subdomains=True,
        skip_assets=True,
    )
    
    print(f"Crawled {len(pages)} pages")
    for page in pages:
        print(f"  - {page.title}: {page.url}")

# Run with: asyncio.run(crawl_docs())
```

## Notes

- Respect target sites' robots.txt and usage policies.
- Keep `max_pages` and `max_depth` conservative to avoid heavy crawling.
- Extend `ContentProcessor` if you need richer parsing (Markdown, code blocks, etc.).
- The `WebCrawler` can be used independently of the ingestion service for testing and inspection.

