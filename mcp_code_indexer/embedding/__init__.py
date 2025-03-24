"""
Embedding Model Abstraction Layer
Provides a unified interface for different embedding models
"""

from typing import List, Dict, Any, Optional, Union
import logging

from ..config import Config

logger = logging.getLogger(__name__)

class EmbeddingModel:
    """
    Abstract base class for embedding models
    
    This class defines the interface that all embedding model implementations must follow.
    """
    
    @classmethod
    def create(cls, config: Config) -> 'EmbeddingModel':
        """
        Factory method to create an embedding model instance based on configuration
        
        Args:
            config: Configuration object
            
        Returns:
            EmbeddingModel instance
        """
        model_name = config.get("indexer.embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
        quantization = config.get("indexer.quantization", None)
        
        if model_name.startswith("intfloat/e5-"):
            from .e5_model import E5EmbeddingModel
            return E5EmbeddingModel(model_name, quantization, config)
        elif model_name.startswith("BAAI/bge-"):
            from .bge_model import BGEEmbeddingModel
            return BGEEmbeddingModel(model_name, quantization, config)
        elif model_name.startswith("thenlper/gte-"):
            from .gte_model import GTEEmbeddingModel
            return GTEEmbeddingModel(model_name, quantization, config)
        else:
            from .sentence_transformer_model import SentenceTransformerModel
            return SentenceTransformerModel(model_name, quantization, config)
    
    def __init__(self, model_name: str, quantization: Optional[str] = None, config: Optional[Config] = None):
        """
        Initialize the embedding model
        
        Args:
            model_name: Name of the model to load
            quantization: Quantization method (e.g., 'int8', 'int4')
            config: Configuration object
        """
        self.model_name = model_name
        self.quantization = quantization
        self.config = config
        self.model = None
        self.dimension = None
        
    def encode(self, 
              texts: List[str], 
              batch_size: int = 32, 
              show_progress_bar: bool = False,
              normalize_embeddings: bool = True) -> List[List[float]]:
        """
        Encode texts into embeddings
        
        Args:
            texts: List of texts to encode
            batch_size: Batch size for encoding
            show_progress_bar: Whether to show a progress bar
            normalize_embeddings: Whether to normalize embeddings
            
        Returns:
            List of embedding vectors
        """
        raise NotImplementedError("Subclasses must implement encode()")
    
    def get_dimension(self) -> int:
        """
        Get the dimension of the embeddings
        
        Returns:
            Embedding dimension
        """
        raise NotImplementedError("Subclasses must implement get_dimension()")
    
    def _load_model(self) -> None:
        """
        Load the embedding model
        
        Returns:
            None
        """
        raise NotImplementedError("Subclasses must implement _load_model()")
    
    def _apply_quantization(self) -> None:
        """
        Apply quantization to the model
        
        Returns:
            None
        """
        if not self.quantization:
            return
        
        try:
            if self.quantization == "int8":
                self._apply_int8_quantization()
            elif self.quantization == "int4":
                self._apply_int4_quantization()
            else:
                logger.warning(f"Unsupported quantization method: {self.quantization}")
        except Exception as e:
            logger.error(f"Failed to apply quantization: {str(e)}")
    
    def _apply_int8_quantization(self) -> None:
        """
        Apply int8 quantization to the model
        
        Returns:
            None
        """
        raise NotImplementedError("Subclasses must implement _apply_int8_quantization()")
    
    def _apply_int4_quantization(self) -> None:
        """
        Apply int4 quantization to the model
        
        Returns:
            None
        """
        raise NotImplementedError("Subclasses must implement _apply_int4_quantization()")