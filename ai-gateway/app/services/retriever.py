from typing import List, Dict, Any

# Placeholder retriever returning mock candidates

def retrieve_candidates(query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    # In real implementation, call vector DB (Milvus/Weaviate) with embeddings
    return [
        {
            "title": "Resolved: NullPointerException in Payment Service",
            "url": "https://example.atlassian.net/browse/PRJ-123",
            "source_type": "jira",
            "score": 0.82,
            "snippet": "NPE due to missing config in prod...",
        },
        {
            "title": "KB: Handling 500 errors with retry policy",
            "url": "https://example.atlassian.net/wiki/spaces/KB/pages/42",
            "source_type": "confluence",
            "score": 0.74,
            "snippet": "Introduce exponential backoff for transient failures...",
        },
    ]
