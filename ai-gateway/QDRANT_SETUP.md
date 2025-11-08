# Qdrant Vector Database Setup

The knowledge base system now uses Qdrant as the vector database backend, with separate collections for each tenant to ensure complete isolation.

## Architecture

### Collection Structure

- **Common Knowledge Base**: Category-specific collections named `kb_common_{category}`  
  e.g., `kb_common_database`, `kb_common_kubernetes`, `kb_common_ci_cd`
- **Tenant Knowledge Bases**: Separate collection per tenant named `kb_tenant_{tenant_id}`

This design ensures:
- ✅ Complete tenant isolation (each tenant has their own collection)
- ✅ Easy tenant data management (delete entire tenant KB by dropping collection)
- ✅ Scalability (collections can be distributed across Qdrant clusters)
- ✅ Security (tenant data is physically separated)

## Setup Options

### Option 1: Local Qdrant (Development)

1. **Install Qdrant using Docker:**
   ```bash
   docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
   ```

2. **Or use Docker Compose:**
   ```yaml
   # Add to docker/docker-compose.yml
   qdrant:
     image: qdrant/qdrant
     ports:
       - "6333:6333"
       - "6334:6334"
     volumes:
       - qdrant_storage:/qdrant/storage
   ```

3. **Set environment variable (optional):**
   ```bash
   export QDRANT_URL=http://localhost:6333
   ```

### Option 2: Qdrant Cloud (Production)

1. **Sign up at [Qdrant Cloud](https://cloud.qdrant.io/)**

2. **Create a cluster and get:**
   - Cluster URL
   - API Key

3. **Set environment variables:**
   ```bash
   export QDRANT_URL=https://your-cluster-url.qdrant.io
   export QDRANT_API_KEY=your-api-key
   ```

### Option 3: Self-Hosted Qdrant

Follow the [Qdrant documentation](https://qdrant.tech/documentation/guides/installation/) for installation on your infrastructure.

## Configuration

The system automatically detects Qdrant configuration from environment variables:

- `QDRANT_URL`: Qdrant server URL (default: `http://localhost:6333`)
- `QDRANT_API_KEY`: Optional API key for Qdrant Cloud

## Collection Management

Collections are automatically created when first entry is added. The system:

1. **Common KB**: Creates `kb_common_{category}` collection for each defined category (database, kubernetes, ci_cd, observability, etc.)
2. **Tenant KB**: Creates `kb_tenant_{tenant_id}` collection when first entry is added for that tenant

### Collection Configuration

- **Vector Size**: Automatically determined from embedding model (384 for all-MiniLM-L6-v2)
- **Distance Metric**: Cosine similarity
- **Payload**: Full knowledge base entry data (JSON)

## API Endpoints for Tenant Management

### List All Tenants

```bash
GET /kb/tenants
```

Returns list of all tenant IDs that have knowledge base collections.

### Get Tenant Statistics

```bash
GET /kb/tenants/{tenant_id}/stats
```

Returns entry count for a tenant's knowledge base.

### Delete Tenant Collection

```bash
DELETE /kb/tenants/{tenant_id}
```

Deletes the entire knowledge base collection for a tenant. **Use with caution!**

## Migration from In-Memory Store

If you were using the in-memory store, you'll need to:

1. **Start Qdrant** (see setup options above)

2. **Re-populate knowledge base:**
   ```bash
   python scripts/populate_kb_examples.py
   ```

3. **Verify collections:**
   ```bash
   # Check Qdrant dashboard at http://localhost:6333/dashboard
   # Or use API:
   curl http://localhost:6333/collections
   ```

## Monitoring

### Qdrant Dashboard

Access the Qdrant dashboard at:
- Local: `http://localhost:6333/dashboard`
- Cloud: Your cluster dashboard URL

### Collection Information

```bash
# List all collections
curl http://localhost:6333/collections

# Get collection info (replace {category} with database, kubernetes, ci_cd, etc.)
curl http://localhost:6333/collections/kb_common_{category}

# Get collection stats
curl http://localhost:6333/collections/kb_common_{category}/stats
```

## Performance Considerations

1. **Batch Operations**: Use `add_entries()` for bulk inserts (more efficient)

2. **Collection Size**: Each tenant collection is independent, so large tenants don't affect others

3. **Indexing**: Qdrant automatically indexes vectors. No manual index management needed.

4. **Scaling**: 
   - For high load, consider Qdrant Cloud or cluster setup
   - Collections can be distributed across Qdrant nodes

## Backup and Recovery

### Backup Collections

```bash
# Export collection (using Qdrant CLI or API)
curl -X POST http://localhost:6333/collections/kb_common_{category}/snapshots
```

### Restore Collections

Use Qdrant's snapshot restore functionality. See [Qdrant documentation](https://qdrant.tech/documentation/guides/snapshots/).

## Security

1. **API Key**: Always use API keys in production (Qdrant Cloud or self-hosted with auth)

2. **Network**: Restrict Qdrant access to your application servers only

3. **Tenant Isolation**: Collections provide natural isolation, but ensure application-level access control

## Troubleshooting

### Connection Issues

```python
# Test connection
from qdrant_client import QdrantClient
client = QdrantClient(url="http://localhost:6333")
print(client.get_collections())
```

### Collection Not Found

Collections are created automatically. If you see "collection not found" errors:
1. Check Qdrant is running
2. Verify QDRANT_URL is correct
3. Try adding an entry to trigger collection creation

### Performance Issues

1. Check collection size: `GET /collections/{name}/stats`
2. Monitor Qdrant logs
3. Consider increasing Qdrant resources or using Qdrant Cloud

## Example: Working with Tenant Collections

```python
from app.services.knowledge_base import get_knowledge_base_service
from app.models.knowledge_base import ITIssueCategory

kb_service = get_knowledge_base_service()

# Add entry to tenant KB (creates collection automatically)
entry_id = kb_service.add_tenant_entry(
    tenant_id="acme-corp",
    title="Payment Gateway Timeout",
    phenomenon="Payment service timing out...",
    root_cause_analysis="External gateway latency...",
    solutions=["Increase timeout", "Add circuit breaker"],
    category=ITIssueCategory.APPLICATION,
    ticket_key="ACME-1234"
)

# Search tenant KB
results = kb_service.search_tenant_kb(
    tenant_id="acme-corp",
    query="payment timeout",
    top_k=5
)

# List all tenants
from app.services.vector_store import get_vector_store
vector_store = get_vector_store()
tenants = vector_store.list_tenant_collections()
print(f"Tenants: {tenants}")
```

