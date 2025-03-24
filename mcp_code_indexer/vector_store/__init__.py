"""
Vector Store Abstraction Layer
Provides a unified interface for different vector database backends
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from ..config import Config

class VectorStore:
    """
    Abstract base class for vector stores
    
    This class defines the interface that all vector store implementations must follow.
    """
    
    @classmethod
    def create(cls, config: Config) -> 'VectorStore':
        """
        Factory method to create a vector store instance based on configuration
        
        Args:
            config: Configuration object
            
        Returns:
            VectorStore instance
        """
        backend = config.get("vector_store.backend", "chroma")
        
        if backend == "lancedb":
            from .lancedb_store import LanceDBStore
            return LanceDBStore(config)
        elif backend == "qdrant":
            from .qdrant_store import QdrantStore
            return QdrantStore(config)
        else:
            from .chroma_store import ChromaDBStore
            return ChromaDBStore(config)
    
    def __init__(self, config: Config):
        """
        Initialize the vector store
        
        Args:
            config: Configuration object
        """
        self.config = config
        
    def add(self, 
            collection_name: str,
            documents: List[str],
            embeddings: List[List[float]],
            metadatas: List[Dict[str, Any]],
            ids: List[str]) -> None:
        """
        Add documents to the vector store
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
            ids: List of document IDs
            
        Returns:
            None
        """
        raise NotImplementedError("Subclasses must implement add()")
    
    def search(self,
              collection_name: str,
              query_embeddings: List[List[float]],
              n_results: int = 10,
              where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search for similar documents
        
        Args:
            collection_name: Name of the collection
            query_embeddings: List of query embedding vectors
            n_results: Number of results to return
            where: Filter condition
            
        Returns:
            Dictionary with search results
        """
        raise NotImplementedError("Subclasses must implement search()")
    
    def get_collection(self, name: str) -> Any:
        """
        Get a collection by name
        
        Args:
            name: Collection name
            
        Returns:
            Collection object
        """
        raise NotImplementedError("Subclasses must implement get_collection()")
    
    def create_collection(self, name: str) -> Any:
        """
        Create a new collection
        
        Args:
            name: Collection name
            
        Returns:
            Collection object
        """
        raise NotImplementedError("Subclasses must implement create_collection()")
    
    def delete_collection(self, name: str) -> None:
        """
        Delete a collection
        
        Args:
            name: Collection name
            
        Returns:
            None
        """
        raise NotImplementedError("Subclasses must implement delete_collection()")
    
    def list_collections(self) -> List[str]:
        """
        List all collections
        
        Returns:
            List of collection names
        """
        raise NotImplementedError("Subclasses must implement list_collections()")
    
    def count(self, collection_name: str, where: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents in a collection
        
        Args:
            collection_name: Name of the collection
            where: Filter condition
            
        Returns:
            Number of documents
        """
        raise NotImplementedError("Subclasses must implement count()")
    
    def get(self, 
           collection_name: str,
           ids: Optional[List[str]] = None,
           where: Optional[Dict[str, Any]] = None,
           include: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get documents from a collection
        
        Args:
            collection_name: Name of the collection
            ids: List of document IDs to retrieve
            where: Filter condition
            include: List of fields to include in the response
            
        Returns:
            Dictionary with documents
        """
        raise NotImplementedError("Subclasses must implement get()")
    
    def delete(self,
              collection_name: str,
              ids: Optional[List[str]] = None,
              where: Optional[Dict[str, Any]] = None) -> None:
        """
        Delete documents from a collection
        
        Args:
            collection_name: Name of the collection
            ids: List of document IDs to delete
            where: Filter condition
            
        Returns:
            None
        """
        raise NotImplementedError("Subclasses must implement delete()")
    
    def migrate_from(self, source_store: 'VectorStore') -> None:
        """
        Migrate data from another vector store
        
        Args:
            source_store: Source vector store
            
        Returns:
            None
        """
        # Get all collections from source
        collections = source_store.list_collections()
        
        # Migrate each collection
        for collection_name in collections:
            # Get all documents from source collection
            docs = source_store.get(collection_name, include=["documents", "embeddings", "metadatas", "ids"])
            
            # Skip if no documents
            if not docs or not docs.get("ids"):
                continue
                
            # Create collection in target
            collection = self.create_collection(collection_name)
            
            # Add documents to target collection
            self.add(
                collection_name=collection_name,
                documents=docs.get("documents", []),
                embeddings=docs.get("embeddings", []),
                metadatas=docs.get("metadatas", []),
                ids=docs.get("ids", [])
            )