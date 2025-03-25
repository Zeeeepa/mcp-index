"""
MCP Code Indexer
A code indexing and retrieval system for AI models
"""

import logging
from typing import Dict, Any, Optional

from .config import Config
from .component_registry import initialize_components, ComponentRegistry
from .service_locator import get_service_by_type
from .interfaces import IndexerProtocol, SearchEngineProtocol, FormatterProtocol, ContextManagerProtocol
from .events import EventType, Event, publish, subscribe

# For backward compatibility
from .indexer import CodeIndexer
from .project_identity import ProjectIdentifier
from .search_engine import SearchEngine
from .mcp_formatter import McpFormatter

__version__ = "0.1.0"
__author__ = "MCP Team"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

class MCPCodeIndexer:
    """Main entry point for the MCP Code Indexer system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the MCP Code Indexer
        
        Args:
            config: Optional configuration dictionary
        """
        # Create configuration
        self.config = Config(config or {})
        
        # Initialize components
        self.registry = initialize_components(self.config)
        
        logger.info(f"MCP Code Indexer v{__version__} initialized")
    
    @property
    def indexer(self) -> IndexerProtocol:
        """Get the code indexer component"""
        return get_service_by_type(IndexerProtocol)
    
    @property
    def search_engine(self) -> SearchEngineProtocol:
        """Get the search engine component"""
        return get_service_by_type(SearchEngineProtocol)
    
    @property
    def formatter(self) -> FormatterProtocol:
        """Get the MCP formatter component"""
        return get_service_by_type(FormatterProtocol)
    
    @property
    def context_manager(self) -> ContextManagerProtocol:
        """Get the context manager component"""
        return get_service_by_type(ContextManagerProtocol)
    
    def index_project(self, project_path: str, force_reindex: bool = False) -> str:
        """
        Index a project
        
        Args:
            project_path: Path to the project
            force_reindex: Whether to force reindexing
            
        Returns:
            Project ID
        """
        return self.indexer.index_project(project_path, force_reindex=force_reindex)
    
    def search(self, query: str, project_ids=None, filters=None, limit: int = 10) -> Dict[str, Any]:
        """
        Search for code
        
        Args:
            query: Search query
            project_ids: Optional list of project IDs to search
            filters: Optional search filters
            limit: Maximum number of results
            
        Returns:
            Formatted search results
        """
        results = self.search_engine.search(query, project_ids, filters, limit)
        return self.formatter.format_search_results(results, query)
    
    def get_code_context(self, file_path: str, line_number: int, context_lines: int = 10) -> Dict[str, Any]:
        """
        Get code context
        
        Args:
            file_path: File path
            line_number: Line number
            context_lines: Number of context lines
            
        Returns:
            Formatted code context
        """
        context = self.search_engine.get_code_context(file_path, line_number, context_lines)
        return self.formatter.format_code_context(context)
    
    def find_similar_code(self, code: str, language: str = None, threshold: float = 0.7, limit: int = 5) -> Dict[str, Any]:
        """
        Find similar code
        
        Args:
            code: Code snippet
            language: Programming language
            threshold: Similarity threshold
            limit: Maximum number of results
            
        Returns:
            Formatted similar code results
        """
        results = self.search_engine.find_similar_code(code, language, threshold, limit)
        return self.formatter.format_search_results(results, code)
    
    def natural_language_search(self, query: str, project_ids=None, filters=None, limit: int = 10) -> Dict[str, Any]:
        """
        Natural language search
        
        Args:
            query: Natural language query
            project_ids: Optional list of project IDs to search
            filters: Optional search filters
            limit: Maximum number of results
            
        Returns:
            Formatted natural language search results
        """
        return self.search_engine.natural_language_search(query, project_ids, filters, limit)
    
    def get_indexed_projects(self) -> Dict[str, Any]:
        """
        Get all indexed projects
        
        Returns:
            Formatted project information
        """
        projects = self.indexer.get_indexed_projects()
        return self.formatter.format_project_info({"projects": projects})
    
    def delete_project_index(self, project_id: str) -> bool:
        """
        Delete a project index
        
        Args:
            project_id: Project ID
            
        Returns:
            Success flag
        """
        return self.indexer.delete_project_index(project_id)
    
    def shutdown(self) -> None:
        """Shutdown the system"""
        logger.info("Shutting down MCP Code Indexer")
        publish(Event(EventType.SYSTEM_SHUTDOWN, {}, "mcp_code_indexer"))

# Create default instance
default_instance = MCPCodeIndexer()

# Convenience functions
def index_project(project_path: str, force_reindex: bool = False) -> str:
    """
    Index a project
    
    Args:
        project_path: Path to the project
        force_reindex: Whether to force reindexing
        
    Returns:
        Project ID
    """
    return default_instance.index_project(project_path, force_reindex)

def search(query: str, project_ids=None, filters=None, limit: int = 10) -> Dict[str, Any]:
    """
    Search for code
    
    Args:
        query: Search query
        project_ids: Optional list of project IDs to search
        filters: Optional search filters
        limit: Maximum number of results
        
    Returns:
        Formatted search results
    """
    return default_instance.search(query, project_ids, filters, limit)

def get_code_context(file_path: str, line_number: int, context_lines: int = 10) -> Dict[str, Any]:
    """
    Get code context
    
    Args:
        file_path: File path
        line_number: Line number
        context_lines: Number of context lines
        
    Returns:
        Formatted code context
    """
    return default_instance.get_code_context(file_path, line_number, context_lines)

def find_similar_code(code: str, language: str = None, threshold: float = 0.7, limit: int = 5) -> Dict[str, Any]:
    """
    Find similar code
    
    Args:
        code: Code snippet
        language: Programming language
        threshold: Similarity threshold
        limit: Maximum number of results
        
    Returns:
        Formatted similar code results
    """
    return default_instance.find_similar_code(code, language, threshold, limit)

def natural_language_search(query: str, project_ids=None, filters=None, limit: int = 10) -> Dict[str, Any]:
    """
    Natural language search
    
    Args:
        query: Natural language query
        project_ids: Optional list of project IDs to search
        filters: Optional search filters
        limit: Maximum number of results
        
    Returns:
        Formatted natural language search results
    """
    return default_instance.natural_language_search(query, project_ids, filters, limit)

def get_indexed_projects() -> Dict[str, Any]:
    """
    Get all indexed projects
    
    Returns:
        Formatted project information
    """
    return default_instance.get_indexed_projects()

def delete_project_index(project_id: str) -> bool:
    """
    Delete a project index
    
    Args:
        project_id: Project ID
        
    Returns:
        Success flag
    """
    return default_instance.delete_project_index(project_id)

def shutdown() -> None:
    """Shutdown the system"""
    default_instance.shutdown()

# Export for backward compatibility
__all__ = [
    "CodeIndexer",
    "ProjectIdentifier", 
    "SearchEngine",
    "McpFormatter",
    "Config",
    "MCPCodeIndexer",
    "index_project",
    "search",
    "get_code_context",
    "find_similar_code",
    "natural_language_search",
    "get_indexed_projects",
    "delete_project_index",
    "shutdown"
]