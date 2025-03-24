"""
Error handling utilities module
Provides standardized error handling and custom exceptions
"""

import logging
import traceback
from typing import Optional, Dict, Any, Type

logger = logging.getLogger(__name__)

class McpError(Exception):
    """Base exception class for MCP-Index errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception
        
        Args:
            message: Error message
            details: Additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the exception to a dictionary
        
        Returns:
            Dictionary representation of the exception
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }

class IndexingError(McpError):
    """Exception raised for errors during indexing"""
    pass

class SearchError(McpError):
    """Exception raised for errors during search"""
    pass

class ConfigError(McpError):
    """Exception raised for configuration errors"""
    pass

class StorageError(McpError):
    """Exception raised for storage-related errors"""
    pass

class ParsingError(McpError):
    """Exception raised for code parsing errors"""
    pass

class ContextError(McpError):
    """Exception raised for context-related errors"""
    pass

class ApiError(McpError):
    """Exception raised for API-related errors"""
    pass

def handle_exception(exception: Exception, component: str = None) -> Dict[str, Any]:
    """
    Handle an exception and return a standardized error response
    
    Args:
        exception: The exception to handle
        component: The component where the exception occurred
        
    Returns:
        Standardized error response dictionary
    """
    # Get exception details
    error_type = type(exception).__name__
    error_message = str(exception)
    error_traceback = traceback.format_exc()
    
    # Log the error
    logger.error(f"Error in {component or 'unknown'}: {error_type}: {error_message}")
    logger.debug(error_traceback)
    
    # Create error response
    error_response = {
        "error": True,
        "error_type": error_type,
        "message": error_message,
        "component": component
    }
    
    # Add additional details for McpError exceptions
    if isinstance(exception, McpError):
        error_response.update(exception.details)
    
    return error_response

def safe_execute(func, *args, component: str = None, default_return: Any = None, **kwargs):
    """
    Execute a function safely, handling any exceptions
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        component: Component name for error logging
        default_return: Default return value if an exception occurs
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result or default_return if an exception occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_exception(e, component)
        return default_return