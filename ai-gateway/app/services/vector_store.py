from typing import List, Dict, Any, Optional
import uuid
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from ..models.knowledge_base import KnowledgeBaseEntry, KnowledgeBaseType, ITIssueCategory
from .embeddings import generate_embedding, generate_embeddings, get_embedding_model


class VectorStore:
    """
    Qdrant-based vector store for knowledge base entries.
    Uses separate collections for common KB and each tenant's private KB.
    """
    
    # Collection name patterns
    COMMON_COLLECTION_PREFIX = "kb_common_"
    TENANT_COLLECTION_PREFIX = "kb_tenant_"
    
    def __init__(self, qdrant_url: Optional[str] = None, qdrant_api_key: Optional[str] = None):
        """
        Initialize Qdrant client
        
        Args:
            qdrant_url: Qdrant server URL (default: http://localhost:6333)
            qdrant_api_key: Optional API key for Qdrant Cloud
        """
        qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = qdrant_api_key or os.getenv("QDRANT_API_KEY")
        
        if qdrant_api_key:
            self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            self.client = QdrantClient(url=qdrant_url)
        
        # Get embedding dimension from model
        embedding_model = get_embedding_model()
        self.embedding_dim = embedding_model.get_sentence_embedding_dimension()
        
        # Ensure collections exist for all defined common categories
        for category in ITIssueCategory:
            self._ensure_collection(self._get_common_collection_name(category))

    def _get_common_collection_name(self, category: ITIssueCategory) -> str:
        """Get collection name for a common KB category"""
        return f"{self.COMMON_COLLECTION_PREFIX}{category.value}"
    
    def _get_tenant_collection_name(self, tenant_id: str) -> str:
        """Get collection name for a tenant"""
        return f"{self.TENANT_COLLECTION_PREFIX}{tenant_id}"
    
    def _ensure_collection(self, collection_name: str) -> None:
        """Ensure a collection exists, create if it doesn't"""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE,
                    ),
                )
        except Exception as e:
            # If collection already exists or other error, log and continue
            # In production, you might want to handle this more gracefully
            pass

    def _get_existing_common_collection_names(self) -> List[str]:
        """List existing common knowledge base collections"""
        try:
            collections = self.client.get_collections().collections
            return [
                col.name
                for col in collections
                if col.name.startswith(self.COMMON_COLLECTION_PREFIX)
            ]
        except Exception:
            return []
    
    def add_entry(self, entry: KnowledgeBaseEntry) -> str:
        """
        Add a knowledge base entry to the vector store
        
        Args:
            entry: Knowledge base entry to add
            
        Returns:
            Entry ID
        """
        if entry.id is None:
            entry.id = str(uuid.uuid4())
        
        # Generate embedding from searchable text
        searchable_text = entry.to_searchable_text()
        embedding = generate_embedding(searchable_text)
        
        # Determine collection name
        if entry.kb_type == KnowledgeBaseType.COMMON:
            if not entry.category:
                raise ValueError("category is required for common knowledge base entries")
            collection_name = self._get_common_collection_name(entry.category)
            self._ensure_collection(collection_name)
        else:  # TENANT
            if not entry.tenant_id:
                raise ValueError("tenant_id is required for tenant knowledge base entries")
            collection_name = self._get_tenant_collection_name(entry.tenant_id)
            self._ensure_collection(collection_name)
        
        # Prepare payload (metadata)
        payload = entry.to_dict()
        
        # Add point to Qdrant
        self.client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=entry.id,
                    vector=embedding.tolist(),
                    payload=payload,
                )
            ],
        )
        
        return entry.id
    
    def add_entries(self, entries: List[KnowledgeBaseEntry]) -> List[str]:
        """Add multiple entries efficiently"""
        if not entries:
            return []
        
        # Group entries by collection
        entries_by_collection: Dict[str, List[KnowledgeBaseEntry]] = {}
        for entry in entries:
            if entry.id is None:
                entry.id = str(uuid.uuid4())
            
            if entry.kb_type == KnowledgeBaseType.COMMON:
                if not entry.category:
                    raise ValueError("category is required for common knowledge base entries")
                collection_name = self._get_common_collection_name(entry.category)
            else:
                if not entry.tenant_id:
                    raise ValueError("tenant_id is required for tenant knowledge base entries")
                collection_name = self._get_tenant_collection_name(entry.tenant_id)
                self._ensure_collection(collection_name)
            
            if entry.kb_type == KnowledgeBaseType.COMMON:
                self._ensure_collection(collection_name)
            
            if collection_name not in entries_by_collection:
                entries_by_collection[collection_name] = []
            entries_by_collection[collection_name].append(entry)
        
        # Batch generate embeddings and add to Qdrant
        entry_ids = []
        for collection_name, collection_entries in entries_by_collection.items():
            # Generate embeddings in batch
            texts = [entry.to_searchable_text() for entry in collection_entries]
            embeddings = generate_embeddings(texts)
            
            # Prepare points
            points = [
                PointStruct(
                    id=entry.id,
                    vector=embedding.tolist(),
                    payload=entry.to_dict(),
                )
                for entry, embedding in zip(collection_entries, embeddings)
            ]
            
            # Batch upsert
            self.client.upsert(
                collection_name=collection_name,
                points=points,
            )
            
            entry_ids.extend([entry.id for entry in collection_entries])
        
        return entry_ids
    
    def search(
        self,
        query: str,
        kb_type: KnowledgeBaseType,
        tenant_id: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 0.0,
        category: Optional[ITIssueCategory] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar entries using vector similarity
        
        Args:
            query: Search query text
            kb_type: Type of knowledge base to search
            tenant_id: Tenant ID for tenant-specific search (required if kb_type is TENANT)
            category: Specific category to search (common KB only). If None, searches all categories.
            top_k: Number of top results to return
            min_score: Minimum similarity score threshold
            
        Returns:
            List of results with entry data and similarity scores
        """
        # Generate query embedding
        query_embedding = generate_embedding(query)
        
        # Determine collection name(s)
        if kb_type == KnowledgeBaseType.TENANT:
            if tenant_id is None:
                return []  # Tenant ID required for tenant KB
            collection_names = [self._get_tenant_collection_name(tenant_id)]
        else:  # COMMON
            if category:
                collection_names = [self._get_common_collection_name(category)]
            else:
                collection_names = self._get_existing_common_collection_names()
                if not collection_names:
                    # Fall back to all defined categories (may be empty collections)
                    collection_names = [
                        self._get_common_collection_name(cat) for cat in ITIssueCategory
                    ]
        
        # Search in relevant collections
        results = []
        for collection_name in collection_names:
            try:
                search_results = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding.tolist(),
                    limit=top_k,
                    score_threshold=min_score,
                )
            except Exception:
                continue
            
            for result in search_results:
                payload = result.payload if isinstance(result.payload, dict) else dict(result.payload)
                entry = KnowledgeBaseEntry.from_dict(payload)
                results.append({
                    "entry": entry,
                    "score": float(result.score),
                    "entry_id": str(result.id),
                })
        
        # Sort combined results and limit to top_k
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]
    
    def get_entry(self, entry_id: str, kb_type: KnowledgeBaseType, tenant_id: Optional[str] = None) -> Optional[KnowledgeBaseEntry]:
        """Get a specific entry by ID"""
        # Determine collection name
        if kb_type == KnowledgeBaseType.TENANT:
            if tenant_id is None:
                return None
            collection_names = [self._get_tenant_collection_name(tenant_id)]
        else:
            collection_names = self._get_existing_common_collection_names()
            if not collection_names:
                collection_names = [
                    self._get_common_collection_name(cat) for cat in ITIssueCategory
                ]
        
        for collection_name in collection_names:
            try:
                result = self.client.retrieve(
                    collection_name=collection_name,
                    ids=[entry_id],
                )
                if result and len(result) > 0:
                    payload = result[0].payload if isinstance(result[0].payload, dict) else dict(result[0].payload)
                    return KnowledgeBaseEntry.from_dict(payload)
            except Exception:
                continue
        
        return None
    
    def delete_entry(self, entry_id: str, kb_type: KnowledgeBaseType, tenant_id: Optional[str] = None) -> bool:
        """Delete an entry"""
        # Determine collection name
        if kb_type == KnowledgeBaseType.TENANT:
            if tenant_id is None:
                return False
            collection_names = [self._get_tenant_collection_name(tenant_id)]
        else:
            collection_names = self._get_existing_common_collection_names()
            if not collection_names:
                collection_names = [
                    self._get_common_collection_name(cat) for cat in ITIssueCategory
                ]
        
        success = False
        for collection_name in collection_names:
            try:
                self.client.delete(
                    collection_name=collection_name,
                    points_selector=[entry_id],
                )
                success = True
            except Exception:
                continue
        return success
    
    def count_entries(self, kb_type: KnowledgeBaseType, tenant_id: Optional[str] = None) -> int:
        """Count entries in a knowledge base"""
        # Determine collection name
        if kb_type == KnowledgeBaseType.TENANT:
            if tenant_id is None:
                # Count all tenant collections
                collections = self.client.get_collections().collections
                total = 0
                for col in collections:
                    if col.name.startswith(self.TENANT_COLLECTION_PREFIX):
                        try:
                            info = self.client.get_collection(col.name)
                            total += info.points_count
                        except Exception:
                            pass
                return total
            collection_name = self._get_tenant_collection_name(tenant_id)
            try:
                info = self.client.get_collection(collection_name)
                return info.points_count
            except Exception:
                return 0
        else:
            collection_names = self._get_existing_common_collection_names()
            if not collection_names:
                collection_names = [
                    self._get_common_collection_name(cat) for cat in ITIssueCategory
                ]
            total = 0
            for collection_name in collection_names:
                try:
                    info = self.client.get_collection(collection_name)
                    total += info.points_count
                except Exception:
                    continue
            return total
    
    def list_tenant_collections(self) -> List[str]:
        """List all tenant collection names"""
        collections = self.client.get_collections().collections
        tenant_collections = []
        for col in collections:
            if col.name.startswith(self.TENANT_COLLECTION_PREFIX):
                # Extract tenant_id from collection name
                tenant_id = col.name[len(self.TENANT_COLLECTION_PREFIX):]
                tenant_collections.append(tenant_id)
        return tenant_collections
    
    def delete_tenant_collection(self, tenant_id: str) -> bool:
        """Delete a tenant's entire collection"""
        collection_name = self._get_tenant_collection_name(tenant_id)
        try:
            self.client.delete_collection(collection_name=collection_name)
            return True
        except Exception:
            return False


# Global vector store instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the global vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
