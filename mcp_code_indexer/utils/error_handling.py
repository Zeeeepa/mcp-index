"""
Error handling module.

This module provides standardized error handling mechanisms for the codebase,
including custom exceptions and error handling utilities.
"""

import logging
import traceback
import sys
from typing import Any, Optional, Dict, Callable, TypeVar, Generic, Union

logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

class McpError(Exception):
    """Base exception class for all MCP-related errors."""
    
    def __init__(self, message: str, code: str = "UNKNOWN", details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.
        
        Args:
            message: The error message
            code: The error code
            details: Additional error details
        """
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the exception to a dictionary.
        
        Returns:
            A dictionary representation of the exception
        """
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "details": self.details
        }
        
    def __str__(self) -> str:
        """
        Get a string representation of the exception.
        
        Returns:
            A string representation of the exception
        """
        if self.details:
            return f"{self.code}: {self.message} - {self.details}"
        return f"{self.code}: {self.message}"


class ConfigError(McpError):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.
        
        Args:
            message: The error message
            details: Additional error details
        """
        super().__init__(message, "CONFIG_ERROR", details)


class IndexingError(McpError):
    """Exception raised for indexing errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.
        
        Args:
            message: The error message
            details: Additional error details
        """
        super().__init__(message, "INDEXING_ERROR", details)


class SearchError(McpError):
    """Exception raised for search errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.
        
        Args:
            message: The error message
            details: Additional error details
        """
        super().__init__(message, "SEARCH_ERROR", details)


class DatabaseError(McpError):
    """Exception raised for database errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.
        
        Args:
            message: The error message
            details: Additional error details
        """
        super().__init__(message, "DATABASE_ERROR", details)


class ApiError(McpError):
    """Exception raised for API errors."""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.
        
        Args:
            message: The error message
            status_code: The HTTP status code
            details: Additional error details
        """
        details = details or {}
        details["status_code"] = status_code
        super().__init__(message, "API_ERROR", details)


def safe_execute(func: Callable[..., T], *args, default: Optional[R] = None, 
                 error_message: str = "Function execution failed", 
                 log_exception: bool = True, **kwargs) -> Union[T, R]:
    """
    Safely execute a function, returning a default value if an exception occurs.
    
    Args:
        func: The function to execute
        *args: Positional arguments to pass to the function
        default: The default value to return if an exception occurs
        error_message: The error message to log
        log_exception: Whether to log the exception
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The function result or the default value
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_exception:
            logger.error(f"{error_message}: {str(e)}")
            logger.debug(traceback.format_exc())
        return default


def format_exception(e: Exception) -> Dict[str, Any]:
    """
    Format an exception as a dictionary.
    
    Args:
        e: The exception to format
        
    Returns:
        A dictionary representation of the exception
    """
    if isinstance(e, McpError):
        return e.to_dict()
    
    return {
        "error": True,
        "code": e.__class__.__name__,
        "message": str(e),
        "details": {
            "type": e.__class__.__name__,
            "module": e.__class__.__module__
        }
    }


def log_exception(e: Exception, level: int = logging.ERROR, include_traceback: bool = True) -> None:
    """
    Log an exception.
    
    Args:
        e: The exception to log
        level: The logging level
        include_traceback: Whether to include the traceback
    """
    message = str(e)
    if isinstance(e, McpError):
        message = f"{e.code}: {e.message}"
    
    logger.log(level, message)
    
    if include_traceback:
        logger.log(level, traceback.format_exc())


class ErrorContext:
    """Context manager for error handling."""
    
    def __init__(self, error_message: str, error_type: type = McpError, 
                 log_level: int = logging.ERROR, reraise: bool = True):
        """
        Initialize the error context.
        
        Args:
            error_message: The error message
            error_type: The error type to raise
            log_level: The logging level
            reraise: Whether to reraise the exception
        """
        self.error_message = error_message
        self.error_type = error_type
        self.log_level = log_level
        self.reraise = reraise
        
    def __enter__(self):
        """Enter the context manager."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager.
        
        Args:
            exc_type: The exception type
            exc_val: The exception value
            exc_tb: The exception traceback
            
        Returns:
            True if the exception was handled, False otherwise
        """
        if exc_type is not None:
            # Log the exception
            logger.log(self.log_level, f"{self.error_message}: {str(exc_val)}")
            if self.log_level <= logging.ERROR:
                logger.debug(traceback.format_exc())
            
            # Reraise as the specified error type if requested
            if self.reraise:
                if issubclass(exc_type, McpError):
                    # Don't wrap McpError exceptions
                    return False
                
                details = {
                    "original_error": str(exc_val),
                    "original_type": exc_type.__name__
                }
                
                raise self.error_type(self.error_message, details=details) from exc_val
            
            # Suppress the exception
            return True
        
        return False