from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class KnowledgeBaseType(str, Enum):
    """Type of knowledge base"""
    COMMON = "common"  # Shared IT issues knowledge base
    TENANT = "tenant"  # Tenant-specific knowledge base


class ITIssueCategory(str, Enum):
    """Categories for IT issues"""
    DATABASE = "database"
    KUBERNETES = "kubernetes"
    CLOUD_INFRA = "cloud_infrastructure"
    CI_CD = "ci_cd"
    NETWORK = "network"
    SECURITY = "security"
    APPLICATION = "application"
    OBSERVABILITY = "observability"
    STORAGE = "storage"
    OTHER = "other"


class KnowledgeBaseEntry(BaseModel):
    """Represents a knowledge base entry with phenomenon, root cause, and solutions"""
    id: Optional[str] = None
    tenant_id: Optional[str] = None  # None for common KB, tenant ID for tenant-specific KB
    kb_type: KnowledgeBaseType

    # Core content
    title: str
    phenomenon: str  # Error logs, symptoms, error messages
    root_cause_analysis: str
    solutions: List[str]  # List of solution steps

    # Metadata
    category: ITIssueCategory
    tags: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Source information (for tenant KB, this might be a Jira ticket)
    source_url: Optional[str] = None
    source_type: Optional[str] = None  # "jira", "confluence", "manual", etc.

    # For tenant KB: reference to original ticket
    ticket_key: Optional[str] = None
    ticket_id: Optional[str] = None

    def to_searchable_text(self) -> str:
        """Convert entry to searchable text for embedding"""
        solutions_text = "\n".join([f"- {sol}" for sol in self.solutions])
        return f"""
Title: {self.title}
Phenomenon: {self.phenomenon}
Root Cause: {self.root_cause_analysis}
Solutions:
{solutions_text}
Tags: {', '.join(self.tags)}
Category: {self.category.value}
""".strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "kb_type": self.kb_type.value,
            "title": self.title,
            "phenomenon": self.phenomenon,
            "root_cause_analysis": self.root_cause_analysis,
            "solutions": self.solutions,
            "category": self.category.value,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "source_url": self.source_url,
            "source_type": self.source_type,
            "ticket_key": self.ticket_key,
            "ticket_id": self.ticket_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeBaseEntry":
        """Create from dictionary"""
        data = data.copy()
        if "created_at" in data and data["created_at"]:
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and data["updated_at"]:
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        data["kb_type"] = KnowledgeBaseType(data["kb_type"])
        data["category"] = ITIssueCategory(data["category"])
        return cls(**data)

