"""
Common utility functions module.

This module provides centralized utility functions used across the codebase,
eliminating redundancy and ensuring consistent implementations.
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Set, Optional, Union, Callable, TypeVar, Generic

# Type variables for generic functions
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

logger = logging.getLogger(__name__)

def convert_sets_to_lists(obj: Any) -> Any:
    """
    Convert all sets in an object to lists for JSON serialization.
    
    Args:
        obj: The object to convert
        
    Returns:
        The converted object with all sets replaced by lists
    """
    if isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, dict):
        return {k: convert_sets_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_sets_to_lists(item) for item in obj]
    else:
        return obj

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely load a JSON string, returning a default value if parsing fails.
    
    Args:
        json_str: The JSON string to parse
        default: The default value to return if parsing fails
        
    Returns:
        The parsed JSON object or the default value
    """
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.debug(f"JSON parsing failed: {str(e)}")
        return default

def safe_json_dumps(obj: Any, default: str = "{}", indent: Optional[int] = None) -> str:
    """
    Safely dump an object to a JSON string, returning a default string if serialization fails.
    
    Args:
        obj: The object to serialize
        default: The default string to return if serialization fails
        indent: The indentation level for the JSON string
        
    Returns:
        The JSON string or the default string
    """
    try:
        # Convert sets to lists before serialization
        serializable_obj = convert_sets_to_lists(obj)
        return json.dumps(serializable_obj, indent=indent, ensure_ascii=False)
    except Exception as e:
        logger.debug(f"JSON serialization failed: {str(e)}")
        return default

def ensure_dir_exists(directory: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: The directory path
        
    Returns:
        True if the directory exists or was created, False otherwise
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {str(e)}")
        return False

def get_file_extension(file_path: str) -> str:
    """
    Get the extension of a file.
    
    Args:
        file_path: The file path
        
    Returns:
        The file extension (including the dot) or an empty string if no extension
    """
    _, ext = os.path.splitext(file_path.lower())
    return ext

def is_binary_file(file_path: str) -> bool:
    """
    Check if a file is binary.
    
    Args:
        file_path: The file path
        
    Returns:
        True if the file is binary, False otherwise
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\0' in chunk
    except Exception:
        return False

def get_relative_path(base_path: str, full_path: str) -> str:
    """
    Get the relative path from a base path.
    
    Args:
        base_path: The base path
        full_path: The full path
        
    Returns:
        The relative path
    """
    try:
        return os.path.relpath(full_path, base_path)
    except Exception:
        # If relpath fails, return the full path
        return full_path

def timed_cache(seconds: int = 300):
    """
    Decorator that caches a function's return value for a specified duration.
    
    Args:
        seconds: The cache duration in seconds
        
    Returns:
        The decorated function
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            current_time = time.time()
            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp < seconds:
                    return result
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)
            return result
            
        return wrapper
    return decorator

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, 
          exceptions: tuple = (Exception,)):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier
        exceptions: Exceptions to catch and retry
        
    Returns:
        The decorated function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            mtries, mdelay = max_attempts, delay
            while mtries > 1:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(f"Retrying {func.__name__} after error: {str(e)}")
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator

class LRUCache(Generic[K, V]):
    """
    A simple LRU (Least Recently Used) cache implementation.
    """
    
    def __init__(self, capacity: int = 100):
        """
        Initialize the LRU cache.
        
        Args:
            capacity: The maximum number of items to store
        """
        self.capacity = capacity
        self.cache: Dict[K, V] = {}
        self.usage: List[K] = []
        
    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        Get an item from the cache.
        
        Args:
            key: The key to look up
            default: The default value to return if the key is not found
            
        Returns:
            The cached value or the default value
        """
        if key in self.cache:
            # Move the key to the end of the usage list
            self.usage.remove(key)
            self.usage.append(key)
            return self.cache[key]
        return default
        
    def put(self, key: K, value: V) -> None:
        """
        Put an item in the cache.
        
        Args:
            key: The key
            value: The value
        """
        if key in self.cache:
            # Update existing item
            self.cache[key] = value
            self.usage.remove(key)
            self.usage.append(key)
        else:
            # Add new item
            if len(self.cache) >= self.capacity:
                # Remove least recently used item
                lru_key = self.usage.pop(0)
                del self.cache[lru_key]
            self.cache[key] = value
            self.usage.append(key)
            
    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        self.usage.clear()
        
    def __len__(self) -> int:
        """Get the number of items in the cache."""
        return len(self.cache)