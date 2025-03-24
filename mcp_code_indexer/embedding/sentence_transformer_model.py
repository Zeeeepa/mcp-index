"""
SentenceTransformer Embedding Model Implementation
"""

import logging
from typing import List, Dict, Any, Optional, Union
import os
import time

from sentence_transformers import SentenceTransformer
import numpy as np

from ..config import Config
from . import EmbeddingModel

logger = logging.getLogger(__name__)

class SentenceTransformerModel(EmbeddingModel):
    """
    SentenceTransformer implementation of the EmbeddingModel interface
    """
    
    def __init__(self, model_name: str, quantization: Optional[str] = None, config: Optional[Config] = None):
        """
        Initialize the SentenceTransformer model
        
        Args:
            model_name: Name of the model to load
            quantization: Quantization method (e.g., 'int8', 'int4')
            config: Configuration object
        """
        super().__init__(model_name, quantization, config)
        self.cache_dir = None
        
        if config:
            self.cache_dir = config.get("indexer.model_cache_dir", None)
        
        # Lazy loading - model will be loaded on first use
    
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
        if self.model is None:
            self._load_model()
        
        try:
            # Measure encoding time for performance monitoring
            start_time = time.time()
            
            # Use more efficient encoding settings
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress_bar,
                convert_to_tensor=False,  # Return numpy array for better compatibility
                normalize_embeddings=normalize_embeddings
            )
            
            encoding_time = time.time() - start_time
            logger.debug(f"Encoded {len(texts)} texts in {encoding_time:.2f}s ({len(texts)/encoding_time:.2f} texts/s)")
            
            # Convert to list for serialization
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error encoding texts: {str(e)}")
            # Return zero embeddings as fallback
            return [[0.0] * self.get_dimension()] * len(texts)
    
    def get_dimension(self) -> int:
        """
        Get the dimension of the embeddings
        
        Returns:
            Embedding dimension
        """
        if self.dimension is None:
            if self.model is None:
                self._load_model()
            self.dimension = self.model.get_sentence_embedding_dimension()
        
        return self.dimension
    
    def _load_model(self) -> None:
        """
        Load the embedding model
        
        Returns:
            None
        """
        try:
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            
            # Load model with cache directory if specified
            if self.cache_dir:
                os.makedirs(self.cache_dir, exist_ok=True)
                self.model = SentenceTransformer(self.model_name, cache_folder=self.cache_dir)
            else:
                self.model = SentenceTransformer(self.model_name)
            
            # Apply quantization if specified
            if self.quantization:
                self._apply_quantization()
            
            # Get dimension
            self.dimension = self.model.get_sentence_embedding_dimension()
            
            logger.info(f"SentenceTransformer model loaded successfully. Embedding dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"Error loading SentenceTransformer model: {str(e)}")
            raise
    
    def _apply_int8_quantization(self) -> None:
        """
        Apply int8 quantization to the model
        
        Returns:
            None
        """
        try:
            import torch
            
            # Check if model has modules that can be quantized
            if not hasattr(self.model, "modules"):
                logger.warning("Model does not have modules attribute, skipping quantization")
                return
            
            # Apply dynamic quantization to all linear layers
            for name, module in self.model.named_modules():
                if isinstance(module, torch.nn.Linear):
                    module_to_quantize = module
                    quantized_module = torch.quantization.quantize_dynamic(
                        module_to_quantize, 
                        {torch.nn.Linear}, 
                        dtype=torch.qint8
                    )
                    # Replace the original module with the quantized one
                    parent_name = name.rsplit('.', 1)[0] if '.' in name else ''
                    if parent_name:
                        parent = self.model.get_submodule(parent_name)
                        child_name = name.rsplit('.', 1)[1]
                        setattr(parent, child_name, quantized_module)
            
            logger.info("Applied int8 quantization to the model")
        except Exception as e:
            logger.error(f"Failed to apply int8 quantization: {str(e)}")
    
    def _apply_int4_quantization(self) -> None:
        """
        Apply int4 quantization to the model
        
        Returns:
            None
        """
        try:
            # Check if bitsandbytes is available
            try:
                import bitsandbytes as bnb
            except ImportError:
                logger.error("bitsandbytes not installed, required for int4 quantization")
                return
            
            import torch
            
            # Check if model has modules that can be quantized
            if not hasattr(self.model, "modules"):
                logger.warning("Model does not have modules attribute, skipping quantization")
                return
            
            # Apply 4-bit quantization to all linear layers
            for name, module in self.model.named_modules():
                if isinstance(module, torch.nn.Linear) and not name.endswith('out_proj'):
                    parent_name = name.rsplit('.', 1)[0] if '.' in name else ''
                    if parent_name:
                        parent = self.model.get_submodule(parent_name)
                        child_name = name.rsplit('.', 1)[1]
                        
                        # Create 4-bit quantized layer
                        quantized_module = bnb.nn.Linear4bit(
                            module.in_features,
                            module.out_features,
                            bias=module.bias is not None,
                            compute_dtype=torch.float16
                        )
                        
                        # Copy weights (with appropriate conversion)
                        quantized_module.weight = module.weight
                        if module.bias is not None:
                            quantized_module.bias = module.bias
                        
                        # Replace the original module
                        setattr(parent, child_name, quantized_module)
            
            logger.info("Applied int4 quantization to the model")
        except Exception as e:
            logger.error(f"Failed to apply int4 quantization: {str(e)}")
            logger.error("This is likely because bitsandbytes is not properly installed or configured")