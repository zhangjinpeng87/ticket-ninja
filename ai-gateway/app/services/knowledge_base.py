from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.knowledge_base import KnowledgeBaseEntry, KnowledgeBaseType, ITIssueCategory
from .vector_store import get_vector_store


class KnowledgeBaseService:
    """Service for managing common and tenant-specific knowledge bases"""
    
    def __init__(self):
        self.vector_store = get_vector_store()
    
    def add_common_entry(
        self,
        title: str,
        phenomenon: str,
        root_cause_analysis: str,
        solutions: List[str],
        category: ITIssueCategory,
        tags: Optional[List[str]] = None,
        source_url: Optional[str] = None,
        source_type: Optional[str] = None,
    ) -> str:
        """
        Add an entry to the common knowledge base
        
        Returns:
            Entry ID
        """
        entry = KnowledgeBaseEntry(
            kb_type=KnowledgeBaseType.COMMON,
            title=title,
            phenomenon=phenomenon,
            root_cause_analysis=root_cause_analysis,
            solutions=solutions,
            category=category,
            tags=tags or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            source_url=source_url,
            source_type=source_type,
        )
        return self.vector_store.add_entry(entry)
    
    def add_tenant_entry(
        self,
        tenant_id: str,
        title: str,
        phenomenon: str,
        root_cause_analysis: str,
        solutions: List[str],
        category: ITIssueCategory,
        tags: Optional[List[str]] = None,
        source_url: Optional[str] = None,
        source_type: Optional[str] = None,
        ticket_key: Optional[str] = None,
        ticket_id: Optional[str] = None,
    ) -> str:
        """
        Add an entry to a tenant's knowledge base
        
        Returns:
            Entry ID
        """
        entry = KnowledgeBaseEntry(
            tenant_id=tenant_id,
            kb_type=KnowledgeBaseType.TENANT,
            title=title,
            phenomenon=phenomenon,
            root_cause_analysis=root_cause_analysis,
            solutions=solutions,
            category=category,
            tags=tags or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            source_url=source_url,
            source_type=source_type,
            ticket_key=ticket_key,
            ticket_id=ticket_id,
        )
        return self.vector_store.add_entry(entry)
    
    def search_common_kb(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.3,
        category: Optional[ITIssueCategory] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search the common knowledge base
        
        Returns:
            List of search results with entries and scores
        """
        return self.vector_store.search(
            query=query,
            kb_type=KnowledgeBaseType.COMMON,
            top_k=top_k,
            min_score=min_score,
            category=category,
        )
    
    def search_tenant_kb(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Search a tenant's knowledge base
        
        Returns:
            List of search results with entries and scores
        """
        return self.vector_store.search(
            query=query,
            kb_type=KnowledgeBaseType.TENANT,
            tenant_id=tenant_id,
            top_k=top_k,
            min_score=min_score
        )
    
    def search_both(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        common_top_k: int = 5,
        tenant_top_k: int = 5,
        min_score: float = 0.3,
        common_categories: Optional[List[ITIssueCategory]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search both common and tenant knowledge bases
        
        Returns:
            Dictionary with 'common' and 'tenant' keys containing search results
        """
        if common_categories:
            combined_common_results: List[Dict[str, Any]] = []
            for category in common_categories:
                combined_common_results.extend(
                    self.search_common_kb(
                        query,
                        top_k=common_top_k,
                        min_score=min_score,
                        category=category,
                    )
                )
            # Deduplicate by entry_id while preserving highest score
            deduped: Dict[str, Dict[str, Any]] = {}
            for result in combined_common_results:
                entry_id = result.get("entry_id")
                if not entry_id:
                    continue
                if entry_id not in deduped or result["score"] > deduped[entry_id]["score"]:
                    deduped[entry_id] = result
            common_results = sorted(deduped.values(), key=lambda r: r["score"], reverse=True)[:common_top_k]
        else:
            common_results = self.search_common_kb(query, top_k=common_top_k, min_score=min_score)

        results = {
            "common": common_results,
            "tenant": [],
        }
        
        if tenant_id:
            results["tenant"] = self.search_tenant_kb(
                tenant_id, query, top_k=tenant_top_k, min_score=min_score
            )
        
        return results
    
    def get_entry(
        self,
        entry_id: str,
        kb_type: KnowledgeBaseType,
        tenant_id: Optional[str] = None
    ) -> Optional[KnowledgeBaseEntry]:
        """Get a specific entry by ID"""
        return self.vector_store.get_entry(entry_id, kb_type, tenant_id)
    
    def delete_entry(
        self,
        entry_id: str,
        kb_type: KnowledgeBaseType,
        tenant_id: Optional[str] = None
    ) -> bool:
        """Delete an entry"""
        return self.vector_store.delete_entry(entry_id, kb_type, tenant_id)


# Global service instance
_kb_service: Optional[KnowledgeBaseService] = None


def get_knowledge_base_service() -> KnowledgeBaseService:
    """Get or create the global knowledge base service instance"""
    global _kb_service
    if _kb_service is None:
        _kb_service = KnowledgeBaseService()
    return _kb_service

