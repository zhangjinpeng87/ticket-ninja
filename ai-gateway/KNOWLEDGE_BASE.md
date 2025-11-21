# Knowledge Base System

The Ticket Ninja AI Gateway includes a dual knowledge base system that combines:
1. **Common Knowledge Base**: Shared IT issues covering databases, Kubernetes, cloud infrastructure, etc.
2. **Tenant Knowledge Base**: Private knowledge base per tenant (enterprise) with their own product issues and historical resolved tickets.

## Architecture

### Components

1. **Knowledge Base Models** (`app/models/knowledge_base.py`)
   - `KnowledgeBaseEntry`: Represents an issue with phenomenon, root cause, and solutions
   - `KnowledgeBaseType`: Enum for COMMON vs TENANT
   - `ITIssueCategory`: Categories like DATABASE, KUBERNETES, CI_CD, CLOUD_INFRA, OBSERVABILITY, STORAGE, etc.

2. **Embedding Service** (`app/services/embeddings.py`)
   - Uses `sentence-transformers` (all-MiniLM-L6-v2 model)
   - Generates vector embeddings for semantic search

3. **Vector Store** (`app/services/vector_store.py`)
   - **Qdrant-based vector store** with cosine similarity search
   - Uses separate collections for complete tenant isolation:
     - Common KB: `kb_common_{category}` collection per category (database, kubernetes, ci_cd, etc.)
     - Tenant KB: `kb_tenant_{tenant_id}` collection per tenant
   - Automatic collection creation and management

4. **Knowledge Base Service** (`app/services/knowledge_base.py`)
   - High-level API for managing knowledge bases
   - Methods to add entries and search both KBs

5. **Retriever** (`app/services/retriever.py`)
   - Searches both common and tenant knowledge bases
   - Returns ranked results with similarity scores

6. **RAG Service** (`app/services/rag.py`)
   - Synthesizes answers from retrieved knowledge base entries
   - Combines information from both KBs intelligently

## API Endpoints

### Analyze Endpoint

**POST** `/analyze`

Analyze a query and retrieve relevant information from knowledge bases.

**Request:**
```json
{
  "query_text": "PostgreSQL connection pool exhausted",
  "tenant_id": "tenant-123",  // Optional
  "screenshot_id": "screenshot-456",  // Optional
  "context": {}
}
```

**Response:**
```json
{
  "answer": "Based on similar historical tickets...",
  "citations": [...],
  "confidence": 0.85,
  "kb_suggestions": [...],
  "debug": {
    "num_common_kb": 3,
    "num_tenant_kb": 2,
    "tenant_id": "tenant-123"
  }
}
```

### Knowledge Base Management

#### Add Common KB Entry

**POST** `/kb/common`

```json
{
  "title": "PostgreSQL Connection Pool Exhaustion",
  "phenomenon": "Error: FATAL: remaining connection slots...",
  "root_cause_analysis": "The PostgreSQL database has reached...",
  "solutions": [
    "Increase max_connections in postgresql.conf",
    "Implement connection pooling (e.g., PgBouncer)"
  ],
  "category": "database",
  "tags": ["postgresql", "connection", "pool"],
  "source_url": "https://example.com/kb/123",
  "source_type": "manual"
}
```

#### Add Tenant KB Entry

**POST** `/kb/tenant/{tenant_id}`

```json
{
  "title": "Payment Service Timeout",
  "phenomenon": "Payment service timing out after 30 seconds...",
  "root_cause_analysis": "The external payment gateway was...",
  "solutions": [
    "Increased payment gateway timeout from 5s to 10s",
    "Implemented circuit breaker pattern"
  ],
  "category": "application",
  "tags": ["payment", "timeout"],
  "ticket_key": "PROJ-1234",
  "source_type": "jira"
}
```

#### Search Knowledge Base

**GET** `/kb/search?query=postgresql+connection&tenant_id=tenant-123&common_top_k=5&tenant_top_k=5&min_score=0.3`

Returns results from both common and tenant knowledge bases.

## Data Model

Each knowledge base entry contains:

- **Phenomenon**: Error logs, symptoms, error messages
- **Root Cause Analysis**: Explanation of why the issue occurred
- **Solutions**: List of solution steps
- **Category**: ITIssueCategory (database, kubernetes, ci_cd, cloud_infrastructure, observability, storage, etc.)
- **Tags**: Additional metadata for filtering
- **Source Information**: URL, type (jira/confluence/manual), ticket references

## Usage Example

### 1. Populate Knowledge Base

```python
from app.services.knowledge_base import get_knowledge_base_service
from app.models.knowledge_base import ITIssueCategory

kb_service = get_knowledge_base_service()

# Add to common KB
kb_service.add_common_entry(
    title="PostgreSQL Connection Pool Exhaustion",
    phenomenon="Error: FATAL: remaining connection slots...",
    root_cause_analysis="The PostgreSQL database has reached...",
    solutions=["Increase max_connections", "Use PgBouncer"],
    category=ITIssueCategory.DATABASE,
    tags=["postgresql", "connection"]
)

# Add to tenant KB
kb_service.add_tenant_entry(
    tenant_id="tenant-123",
    title="Payment Service Timeout",
    phenomenon="Service timing out...",
    root_cause_analysis="External gateway latency...",
    solutions=["Increase timeout", "Add circuit breaker"],
    category=ITIssueCategory.APPLICATION,
    ticket_key="PROJ-1234"
)
```

### 2. Search Knowledge Base

```python
# Search both KBs
results = kb_service.search_both(
    query="postgresql connection pool exhausted",
    tenant_id="tenant-123",
    common_top_k=5,
    tenant_top_k=5
)

# Access results
for result in results["common"]:
    entry = result["entry"]
    score = result["score"]
    print(f"{entry.title} (score: {score})")
```

### 3. Use in Analyze Endpoint

When a request comes to `/analyze`:
1. The retriever searches both common and tenant KBs using vector similarity
2. Results are ranked by similarity score
3. The RAG service synthesizes an answer combining information from both KBs
4. Response includes citations and confidence score

## Populating Sample Data

Run the sample population script:

```bash
cd ai-gateway
python scripts/populate_kb_examples.py
```

This will add example entries to both common and tenant knowledge bases.

## Qdrant Setup

The system uses **Qdrant** as the vector database. See [QDRANT_SETUP.md](./QDRANT_SETUP.md) for detailed setup instructions.

**Quick Start:**
```bash
# Using Docker
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Or use docker-compose (includes Qdrant)
cd docker
docker-compose up
```

## Production Considerations

1. **Vector Database**: ✅ **Qdrant is already integrated!**
   - Collections provide natural tenant isolation
   - Automatic collection management
   - Supports both local and cloud deployments
   - See [QDRANT_SETUP.md](./QDRANT_SETUP.md) for production setup

2. **Persistence**: ✅ **Qdrant provides persistent storage!**
   - All data is persisted in Qdrant
   - Collections are stored on disk (or cloud)
   - No additional database needed for vector storage
   - Consider adding metadata database for advanced queries if needed

3. **Embedding Model**: Consider domain-specific models:
   - For IT/technical content: `sentence-transformers/all-mpnet-base-v2`
   - For code: `microsoft/codebert-base`
   - Fine-tune on your specific IT issue data

## Data Foundry Ingestion

- The `data-foundry/` service can crawl technical documentation sites, extract readable content, chunk the text, and convert each chunk into a `KnowledgeBaseEntry`.
- Use the `/ingest` endpoint (see `data-foundry/README.md`) to populate either the common knowledge base (per category collection) or a tenant-specific collection.
- Data Foundry uses the same shared `shared_kb` modules, so ingested documents are immediately retrievable by the AI Gateway.

4. **Scaling**: 
   - Batch embedding generation
   - Async indexing for new entries
   - Caching frequently accessed entries

5. **Security**:
   - Add authentication/authorization for KB management endpoints
   - Ensure tenant isolation
   - Audit logging for KB changes

6. **LLM Integration**: Replace placeholder RAG with:
   - LangChain for orchestration
   - OpenAI GPT-4 or similar for answer synthesis
   - Better prompt engineering for combining KB results

## Environment Variables

- `EMBEDDING_MODEL`: Override default embedding model (default: `sentence-transformers/all-MiniLM-L6-v2`)

