from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import os

# Global model instance (lazy loaded)
_embedding_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """Get or initialize the embedding model (lazy loading)"""
    global _embedding_model
    if _embedding_model is None:
        # Using a lightweight, fast model suitable for IT/technical content
        # all-MiniLM-L6-v2 is a good balance of speed and quality
        model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        _embedding_model = SentenceTransformer(model_name)
    return _embedding_model


def generate_embeddings(texts: List[str]) -> np.ndarray:
    """
    Generate embeddings for a list of texts

    Args:
        texts: List of text strings to embed

    Returns:
        numpy array of shape (n_texts, embedding_dim)
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings


def generate_embedding(text: str) -> np.ndarray:
    """
    Generate embedding for a single text

    Args:
        text: Text string to embed

    Returns:
        numpy array of shape (embedding_dim,)
    """
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
    return embedding

