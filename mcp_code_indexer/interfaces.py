"""
Component interfaces module
Defines interfaces for standardized component communication
"""

from typing import List, Dict, Any, Optional, Protocol, Set, Tuple
from enum import Enum

class IndexingStatus(Enum):
    """Indexing status constants"""
    NEW = "new"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    UPDATING = "updating"

class CodeChunkProtocol(Protocol):
    """Interface for code chunks"""
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    type: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        ...
    
    def get_id(self) -> str:
        """Get unique identifier"""
        ...

class IndexerProtocol(Protocol):
    """Interface for code indexer"""
    
    def index_project(self, project_path: str, 
                     progress_callback: Optional[Any] = None,
                     force_reindex: bool = False) -> str:
        """
        Index a project
        
        Args:
            project_path: Path to the project
            progress_callback: Callback for progress updates
            force_reindex: Whether to force reindexing
            
        Returns:
            Project ID
        """
        ...
    
    def search(self, project_id: str, query: str, 
              limit: int = 10, timeout: int = 30) -> List[Dict[str, Any]]:
        """
        Search for code
        
        Args:
            project_id: Project ID
            query: Search query
            limit: Maximum number of results
            timeout: Search timeout in seconds
            
        Returns:
            List of code chunks
        """
        ...
    
    def get_indexing_status(self, project_id: str) -> Tuple[str, float]:
        """
        Get indexing status
        
        Args:
            project_id: Project ID
            
        Returns:
            Tuple of (status, progress)
        """
        ...
    
    def get_indexed_projects(self) -> List[Dict[str, Any]]:
        """
        Get all indexed projects
        
        Returns:
            List of project information dictionaries
        """
        ...
    
    def delete_project_index(self, project_id: str) -> bool:
        """
        Delete a project index
        
        Args:
            project_id: Project ID
            
        Returns:
            Success flag
        """
        ...

class SearchEngineProtocol(Protocol):
    """Interface for search engine"""
    
    def search(self, query: str, project_ids: Optional[List[str]] = None, 
              filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for code
        
        Args:
            query: Search query
            project_ids: List of project IDs to search
            filters: Search filters
            limit: Maximum number of results
            
        Returns:
            List of code chunks
        """
        ...
    
    def search_by_file(self, file_path: str, project_id: Optional[str] = None, 
                      limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search by file path
        
        Args:
            file_path: File path
            project_id: Project ID
            limit: Maximum number of results
            
        Returns:
            List of code chunks
        """
        ...
    
    def get_code_context(self, file_path: str, line_number: int, 
                        context_lines: int = 10) -> Dict[str, Any]:
        """
        Get code context
        
        Args:
            file_path: File path
            line_number: Line number
            context_lines: Number of context lines
            
        Returns:
            Code context dictionary
        """
        ...
    
    def find_similar_code(self, code: str, language: str = None,
                         threshold: float = 0.7, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar code
        
        Args:
            code: Code snippet
            language: Programming language
            threshold: Similarity threshold
            limit: Maximum number of results
            
        Returns:
            List of similar code chunks
        """
        ...
    
    def natural_language_search(self, query: str, project_ids: Optional[List[str]] = None,
                              filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> Dict[str, Any]:
        """
        Natural language search
        
        Args:
            query: Natural language query
            project_ids: List of project IDs to search
            filters: Search filters
            limit: Maximum number of results
            
        Returns:
            Search results with LLM-generated answer
        """
        ...

class ContextManagerProtocol(Protocol):
    """Interface for context manager"""
    
    def get_context(self, file_path: str, line_number: int, 
                   context_type: Any = None,
                   priority: Any = None) -> Optional[str]:
        """
        Get code context
        
        Args:
            file_path: File path
            line_number: Line number
            context_type: Context type
            priority: Context priority
            
        Returns:
            Context content
        """
        ...
    
    def get_module_context(self, file_path: str,
                          priority: Any = None) -> Optional[str]:
        """
        Get module context
        
        Args:
            file_path: File path
            priority: Context priority
            
        Returns:
            Module context content
        """
        ...

class FormatterProtocol(Protocol):
    """Interface for MCP formatter"""
    
    def format_search_results(self, results: List[Dict[str, Any]], 
                             query: str, confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Format search results
        
        Args:
            results: Search results
            query: Original query
            confidence_threshold: Confidence threshold
            
        Returns:
            Formatted MCP response
        """
        ...
    
    def format_project_info(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format project information
        
        Args:
            project_info: Project information dictionary
            
        Returns:
            Formatted MCP response
        """
        ...
    
    def format_code_context(self, code_context: Dict[str, Any], 
                           related_blocks: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format code context
        
        Args:
            code_context: Code context dictionary
            related_blocks: Related code blocks
            
        Returns:
            Formatted MCP response
        """
        ...
    
    def format_error(self, error_message: str, query: str = None) -> Dict[str, Any]:
        """
        Format error
        
        Args:
            error_message: Error message
            query: Original query
            
        Returns:
            Formatted MCP error response
        """
        ...
    
    def format_indexing_status(self, project_id: str, status: str, 
                              progress: float, message: str = None) -> Dict[str, Any]:
        """
        Format indexing status
        
        Args:
            project_id: Project ID
            status: Indexing status
            progress: Indexing progress
            message: Status message
            
        Returns:
            Formatted MCP response
        """
        ...