"""
Utility functions package.

This package provides utility functions for various purposes, including
file operations, embedding operations, JSON serialization, error handling,
and dependency injection.
"""

# Export file utilities
from .file_utils import (
    is_binary_file,
    get_file_language,
    normalize_path,
    get_relative_path,
    read_file_content,
    get_file_hash
)

# Export embedding utilities
from .embedding_utils import (
    create_embeddings,
    cosine_similarity,
    normalize_embeddings,
    batch_encode_texts
)

# Export JSON utilities
from .json_utils import (
    convert_sets_to_lists,
    safe_json_serialize
)

# Export common utilities
from .common_utils import (
    ensure_dir_exists,
    get_file_extension,
    is_binary_file as common_is_binary_file,
    get_relative_path as common_get_relative_path,
    timed_cache,
    retry,
    LRUCache,
    safe_json_loads,
    safe_json_dumps
)

# Export error handling utilities
from .error_handling import (
    McpError,
    ConfigError,
    IndexingError,
    SearchError,
    DatabaseError,
    ApiError,
    safe_execute,
    format_exception,
    log_exception,
    ErrorContext
)

# Export dependency injection utilities
from .dependency_injection import (
    DependencyContainer,
    get_container,
    register,
    register_factory,
    get,
    has,
    clear,
    Inject,
    Injectable
)

__all__ = [
    # File utilities
    "is_binary_file",
    "get_file_language",
    "normalize_path",
    "get_relative_path",
    "read_file_content",
    "get_file_hash",
    
    # Embedding utilities
    "create_embeddings",
    "cosine_similarity",
    "normalize_embeddings",
    "batch_encode_texts",
    
    # JSON utilities
    "convert_sets_to_lists",
    "safe_json_serialize",
    
    # Common utilities
    "ensure_dir_exists",
    "get_file_extension",
    "timed_cache",
    "retry",
    "LRUCache",
    "safe_json_loads",
    "safe_json_dumps",
    
    # Error handling utilities
    "McpError",
    "ConfigError",
    "IndexingError",
    "SearchError",
    "DatabaseError",
    "ApiError",
    "safe_execute",
    "format_exception",
    "log_exception",
    "ErrorContext",
    
    # Dependency injection utilities
    "DependencyContainer",
    "get_container",
    "register",
    "register_factory",
    "get",
    "has",
    "clear",
    "Inject",
    "Injectable"
]