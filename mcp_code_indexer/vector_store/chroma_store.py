"""
ChromaDB Vector Store Implementation
"""

import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

import chromadb
from chromadb.config import Settings

from ..config import Config
from . import VectorStore

logger = logging.getLogger(__name__)

class ChromaDBStore(VectorStore):
    """
    ChromaDB implementation of the VectorStore interface
    """
    
    def __init__(self, config: Config):
        """
        Initialize the ChromaDB store
        
        Args:
            config: Configuration object
        """
        super().__init__(config)
        
        # Initialize vector database
        self.vector_db_path = Path(config.get("storage.vector_db_path"))
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.vector_db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        logger.info(f"ChromaDB store initialized at {self.vector_db_path}")
    
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
        try:
            collection = self.get_collection(collection_name)
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.debug(f"Added {len(documents)} documents to collection {collection_name}")
        except Exception as e:
            logger.error(f"Error adding documents to collection {collection_name}: {str(e)}")
            raise
    
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
        try:
            collection = self.get_collection(collection_name)
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where
            )
            return results
        except Exception as e:
            logger.error(f"Error searching collection {collection_name}: {str(e)}")
            return {"ids": [], "distances": [], "metadatas": [], "documents": []}
    
    def get_collection(self, name: str) -> Any:
        """
        Get a collection by name
        
        Args:
            name: Collection name
            
        Returns:
            Collection object
        """
        try:
            return self.client.get_collection(name=name)
        except Exception as e:
            logger.error(f"Error getting collection {name}: {str(e)}")
            raise
    
    def create_collection(self, name: str) -> Any:
        """
        Create a new collection
        
        Args:
            name: Collection name
            
        Returns:
            Collection object
        """
        try:
            return self.client.create_collection(name=name)
        except Exception as e:
            logger.error(f"Error creating collection {name}: {str(e)}")
            raise
    
    def delete_collection(self, name: str) -> None:
        """
        Delete a collection
        
        Args:
            name: Collection name
            
        Returns:
            None
        """
        try:
            self.client.delete_collection(name=name)
            logger.info(f"Deleted collection {name}")
        except Exception as e:
            logger.error(f"Error deleting collection {name}: {str(e)}")
            raise
    
    def list_collections(self) -> List[str]:
        """
        List all collections
        
        Returns:
            List of collection names
        """
        try:
            collections = self.client.list_collections()
            return [collection.name for collection in collections]
        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            return []
    
    def count(self, collection_name: str, where: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents in a collection
        
        Args:
            collection_name: Name of the collection
            where: Filter condition
            
        Returns:
            Number of documents
        """
        try:
            collection = self.get_collection(collection_name)
            return collection.count(where=where)
        except Exception as e:
            logger.error(f"Error counting documents in collection {collection_name}: {str(e)}")
            return 0
    
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
        try:
            collection = self.get_collection(collection_name)
            return collection.get(ids=ids, where=where, include=include)
        except Exception as e:
            logger.error(f"Error getting documents from collection {collection_name}: {str(e)}")
            return {}
    
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
        try:
            collection = self.get_collection(collection_name)
            collection.delete(ids=ids, where=where)
            logger.debug(f"Deleted documents from collection {collection_name}")
        except Exception as e:
            logger.error(f"Error deleting documents from collection {collection_name}: {str(e)}")
            raise
    
    def ensure_connection(self) -> bool:
        """
        Ensure that the connection to ChromaDB is valid
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try to list collections as a connection test
            self.client.list_collections()
            return True
        except Exception as e:
            logger.error(f"ChromaDB connection failed: {str(e)}")
            
            # Try to reinitialize
            try:
                self.client = chromadb.PersistentClient(
                    path=str(self.vector_db_path),
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                return True
            except Exception as e:
                logger.error(f"Failed to reinitialize ChromaDB connection: {str(e)}")
                return False