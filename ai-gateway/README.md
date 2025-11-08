# AI Gateway (FastAPI)

FastAPI service that powers Ticket Ninja's AI features: intent classification, retrieval across a **common** and **tenant-specific** knowledge base, RAG synthesis, and screenshot parsing.

## Prerequisites

- Python 3.10+
- [Qdrant](https://qdrant.tech/) (vector database)
- Optional: OCR service (for screenshot parsing)

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start Qdrant (local docker)
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# (Optional) start OCR service from repo root:
# docker-compose up ocr-service

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Using docker-compose

From the repo root:

```bash
cd docker
docker-compose up
```

This launches Qdrant, OCR service, and the AI Gateway with the correct networking defaults.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `QDRANT_URL` | Qdrant endpoint | `http://localhost:6333` |
| `QDRANT_API_KEY` | Qdrant API key (for cloud deployments) | _unset_ |
| `OCR_SERVICE_URL` | OCR service endpoint | _required if screenshots used_ |
| `EMBEDDING_MODEL` | Sentence-transformers model | `sentence-transformers/all-MiniLM-L6-v2` |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/analyze` | POST | Analyze query (and optional screenshot) |
| `/kb/common` | POST | Add to common knowledge base |
| `/kb/tenant/{tenant_id}` | POST | Add to tenant knowledge base |
| `/kb/search` | GET | Search both common and tenant KBs |
| `/kb/tenants` | GET | List tenants with KB data |
| `/kb/tenants/{tenant_id}/stats` | GET | Tenant KB statistics |
| `/kb/tenants/{tenant_id}` | DELETE | Delete tenant KB collection |

### `/analyze` response shape

```json
{
  "answer": "string",
  "citations": [{ "title": "string", "url": "string", "source_type": "jira|confluence|kb|tenant_kb" }],
  "confidence": 0.0,
  "kb_suggestions": [{ "title": "string", "url": "string" }],
  "debug": {
    "intent": {},
    "num_common_kb": 0,
    "num_tenant_kb": 0,
    "tenant_id": "string"
  }
}
```

## Knowledge Base Docs

- [Knowledge Base Overview](./KNOWLEDGE_BASE.md)
- [Qdrant Setup Guide](./QDRANT_SETUP.md)
- [Qdrant Migration Notes](./QDRANT_MIGRATION.md)

## Notes

- Retrieval uses Qdrant with one collection per tenant (`kb_tenant_{tenant_id}`) and category-specific collections for the common knowledge base (`kb_common_{category}`).
- Replace the placeholder RAG synthesizer with your preferred LLM orchestration (e.g. LangChain + OpenAI).
- OCR service (`ocr-service/`) is provided separately for screenshot text extraction.
