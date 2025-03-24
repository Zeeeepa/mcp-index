"""
LanceDB Vector Store Implementation
"""

import logging
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import json

import lancedb
import pyarrow as pa

from ..config import Config
from . import VectorStore

logger = logging.getLogger(__name__)

class LanceDBStore(VectorStore):
    """
    LanceDB implementation of the VectorStore interface
    """
    
    def __init__(self, config: Config):
        """
        Initialize the LanceDB store
        
        Args:
            config: Configuration object
        """
        super().__init__(config)
        
        # Initialize vector database
        self.vector_db_path = Path(config.get("storage.vector_db_path"))
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        # Create a subdirectory for LanceDB
        self.lance_db_path = self.vector_db_path / "lancedb"
        self.lance_db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize LanceDB connection
        self.db = lancedb.connect(str(self.lance_db_path))
        
        # Cache for collection schemas
        self._collection_schemas = {}
        
        logger.info(f"LanceDB store initialized at {self.lance_db_path}")
    
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
            # Prepare data for LanceDB
            data = []
            for i in range(len(ids)):
                item = {
                    "id": ids[i],
                    "document": documents[i] if i < len(documents) else "",
                    "vector": embeddings[i] if i < len(embeddings) else [],
                }
                
                # Add metadata fields
                if i < len(metadatas):
                    # Convert nested metadata to flat structure
                    for key, value in metadatas[i].items():
                        if isinstance(value, dict):
                            # For nested dictionaries, convert to JSON string
                            item[key] = json.dumps(value)
                        elif isinstance(value, list):
                            # For lists, convert to JSON string
                            item[key] = json.dumps(value)
                        else:
                            item[key] = value
                
                data.append(item)
            
            # Get or create collection
            collection = self._get_or_create_collection(collection_name, data)
            
            # Add data to collection
            collection.add(data)
            
            logger.debug(f"Added {len(documents)} documents to collection {collection_name}")
        except Exception as e:
            logger.error(f"Error adding documents to collection {collection_name}: {str(e)}")
            raise
    
    def _get_or_create_collection(self, name: str, data_sample=None):
        """
        Get or create a collection with schema inference
        
        Args:
            name: Collection name
            data_sample: Sample data for schema inference
            
        Returns:
            Collection object
        """
        try:
            # Try to get existing collection
            return self.db.open_table(name)
        except Exception:
            # Collection doesn't exist, create it
            if not data_sample:
                raise ValueError(f"Collection {name} does not exist and no data sample provided for creation")
            
            # Infer schema from data sample
            vector_dim = len(data_sample[0]["vector"])
            
            # Create collection
            return self.db.create_table(
                name,
                data=data_sample,
                mode="overwrite"
            )
    
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
            # Get collection
            collection = self.get_collection(collection_name)
            
            # Prepare results structure
            results = {
                "ids": [[] for _ in range(len(query_embeddings))],
                "distances": [[] for _ in range(len(query_embeddings))],
                "metadatas": [[] for _ in range(len(query_embeddings))],
                "documents": [[] for _ in range(len(query_embeddings))]
            }
            
            # Process each query embedding
            for i, query_vector in enumerate(query_embeddings):
                # Create query
                query = collection.search(query_vector).limit(n_results)
                
                # Add filter if provided
                if where:
                    filter_expr = self._build_filter_expression(where)
                    if filter_expr:
                        query = query.where(filter_expr)
                
                # Execute query
                query_results = query.to_pandas()
                
                if not query_results.empty:
                    # Extract results
                    results["ids"][i] = query_results["id"].tolist()
                    results["distances"][i] = query_results["_distance"].tolist()
                    results["documents"][i] = query_results["document"].tolist()
                    
                    # Extract metadata
                    metadatas = []
                    for _, row in query_results.iterrows():
                        metadata = {}
                        for col in query_results.columns:
                            if col not in ["id", "_distance", "document", "vector"]:
                                # Try to parse JSON strings back to objects
                                try:
                                    if isinstance(row[col], str) and (row[col].startswith("{") or row[col].startswith("[")):
                                        metadata[col] = json.loads(row[col])
                                    else:
                                        metadata[col] = row[col]
                                except:
                                    metadata[col] = row[col]
                        metadatas.append(metadata)
                    
                    results["metadatas"][i] = metadatas
            
            return results
        except Exception as e:
            logger.error(f"Error searching collection {collection_name}: {str(e)}")
            return {"ids": [], "distances": [], "metadatas": [], "documents": []}
    
    def _build_filter_expression(self, where: Dict[str, Any]) -> str:
        """
        Build a filter expression from a where condition
        
        Args:
            where: Filter condition
            
        Returns:
            Filter expression string
        """
        if not where:
            return ""
        
        conditions = []
        for key, value in where.items():
            if isinstance(value, str):
                conditions.append(f"{key} = '{value}'")
            elif isinstance(value, (int, float, bool)):
                conditions.append(f"{key} = {value}")
            elif value is None:
                conditions.append(f"{key} IS NULL")
        
        return " AND ".join(conditions)
    
    def get_collection(self, name: str) -> Any:
        """
        Get a collection by name
        
        Args:
            name: Collection name
            
        Returns:
            Collection object
        """
        try:
            return self.db.open_table(name)
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
            # Create a minimal schema for an empty collection
            sample_data = [{
                "id": "placeholder",
                "document": "",
                "vector": [0.0] * 1536  # Default dimension, will be overwritten on first add
            }]
            
            collection = self.db.create_table(
                name,
                data=sample_data,
                mode="overwrite"
            )
            
            # Remove the placeholder
            collection.delete("id = 'placeholder'")
            
            return collection
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
            self.db.drop_table(name)
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
            return [table.name for table in self.db.list_tables()]
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
            
            # Create query
            query = collection
            
            # Add filter if provided
            if where:
                filter_expr = self._build_filter_expression(where)
                if filter_expr:
                    query = query.filter(filter_expr)
            
            # Count records
            return len(query.to_pandas())
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
            
            # Build query
            if ids:
                # Convert ids to a SQL IN clause
                ids_str = ", ".join([f"'{id}'" for id in ids])
                query = collection.filter(f"id IN ({ids_str})")
            else:
                query = collection
            
            # Add filter if provided
            if where:
                filter_expr = self._build_filter_expression(where)
                if filter_expr:
                    query = query.filter(filter_expr)
            
            # Execute query
            df = query.to_pandas()
            
            # Prepare results
            result = {
                "ids": df["id"].tolist() if not df.empty else [],
                "documents": df["document"].tolist() if "document" in df.columns and not df.empty else [],
            }
            
            # Include embeddings if requested
            if include and "embeddings" in include and "vector" in df.columns:
                result["embeddings"] = df["vector"].tolist()
            
            # Extract metadata
            if not df.empty:
                metadatas = []
                for _, row in df.iterrows():
                    metadata = {}
                    for col in df.columns:
                        if col not in ["id", "document", "vector"]:
                            # Try to parse JSON strings back to objects
                            try:
                                if isinstance(row[col], str) and (row[col].startswith("{") or row[col].startswith("[")):
                                    metadata[col] = json.loads(row[col])
                                else:
                                    metadata[col] = row[col]
                            except:
                                metadata[col] = row[col]
                    metadatas.append(metadata)
                
                result["metadatas"] = metadatas
            else:
                result["metadatas"] = []
            
            return result
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
            
            # Build filter expression
            if ids:
                # Convert ids to a SQL IN clause
                ids_str = ", ".join([f"'{id}'" for id in ids])
                filter_expr = f"id IN ({ids_str})"
            elif where:
                filter_expr = self._build_filter_expression(where)
            else:
                # Delete all documents
                filter_expr = "1=1"
            
            # Execute delete
            if filter_expr:
                collection.delete(filter_expr)
                logger.debug(f"Deleted documents from collection {collection_name}")
        except Exception as e:
            logger.error(f"Error deleting documents from collection {collection_name}: {str(e)}")
            raise