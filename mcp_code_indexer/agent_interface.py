"""
Agent Interface Module

Provides a unified interface for AI agents to interact with the mcp-index codebase.
This module serves as the central hub for all interactions between users, AI agents,
and the backend tools, providing a streamlined and optimized workflow.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from dataclasses import dataclass

from .config import Config
from .indexer import CodeIndexer
from .search_engine import SearchEngine
from .context_manager import ContextManager, ContextType, ContextPriority
from .agent_manager import AgentManager
from .code_analyzer import CodeAnalyzer
from .code_optimizer import CodeOptimizer

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Types of actions that can be performed by the agent interface"""
    INDEX_PROJECT = "index_project"
    SEARCH_CODE = "search_code"
    GET_CODE_CONTEXT = "get_code_context"
    ANALYZE_CODE = "analyze_code"
    FIND_SIMILAR_CODE = "find_similar_code"
    NATURAL_LANGUAGE_SEARCH = "natural_language_search"
    GET_RELATED_CODE = "get_related_code"
    GET_FILE_OVERVIEW = "get_file_overview"

@dataclass
class AgentRequest:
    """Represents a request from an AI agent to the backend system"""
    action: ActionType
    parameters: Dict[str, Any]
    request_id: str
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "action": self.action.value,
            "parameters": self.parameters,
            "request_id": self.request_id,
            "user_id": self.user_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentRequest':
        """Create from dictionary representation"""
        return cls(
            action=ActionType(data["action"]),
            parameters=data["parameters"],
            request_id=data["request_id"],
            user_id=data.get("user_id")
        )

@dataclass
class AgentResponse:
    """Represents a response from the backend system to an AI agent"""
    request_id: str
    success: bool
    data: Any
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "request_id": self.request_id,
            "success": self.success,
            "data": self.data,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentResponse':
        """Create from dictionary representation"""
        return cls(
            request_id=data["request_id"],
            success=data["success"],
            data=data["data"],
            error=data.get("error")
        )

class AgentInterface:
    """
    Agent Interface class
    
    Provides a unified interface for AI agents to interact with the mcp-index codebase.
    This class serves as the central hub for all interactions between users, AI agents,
    and the backend tools.
    """
    
    def __init__(self, config: Config):
        """
        Initialize Agent Interface
        
        Args:
            config: Configuration object
            
        Returns:
            None
        """
        self.config = config
        
        # Initialize core components
        self.indexer = CodeIndexer(config)
        self.search_engine = SearchEngine(config, self.indexer)
        self.agent_manager = AgentManager(config, self.indexer, self.search_engine)
        self.context_manager = ContextManager()
        self.code_analyzer = CodeAnalyzer()
        self.code_optimizer = CodeOptimizer()
        
        # Register action handlers
        self.action_handlers = {
            ActionType.INDEX_PROJECT: self._handle_index_project,
            ActionType.SEARCH_CODE: self._handle_search_code,
            ActionType.GET_CODE_CONTEXT: self._handle_get_code_context,
            ActionType.ANALYZE_CODE: self._handle_analyze_code,
            ActionType.FIND_SIMILAR_CODE: self._handle_find_similar_code,
            ActionType.NATURAL_LANGUAGE_SEARCH: self._handle_natural_language_search,
            ActionType.GET_RELATED_CODE: self._handle_get_related_code,
            ActionType.GET_FILE_OVERVIEW: self._handle_get_file_overview
        }
        
        logger.info("Agent Interface initialized")
    
    def process_request(self, request: Union[AgentRequest, Dict[str, Any]]) -> AgentResponse:
        """
        Process a request from an AI agent
        
        Args:
            request: Agent request object or dictionary
            
        Returns:
            Agent response object
        """
        # Convert dictionary to AgentRequest if needed
        if isinstance(request, dict):
            try:
                request = AgentRequest.from_dict(request)
            except Exception as e:
                return AgentResponse(
                    request_id=request.get("request_id", "unknown"),
                    success=False,
                    data=None,
                    error=f"Invalid request format: {str(e)}"
                )
        
        # Log the request
        logger.info(f"Processing request: {request.action.value}, ID: {request.request_id}")
        
        # Get the appropriate handler for the action
        handler = self.action_handlers.get(request.action)
        if not handler:
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                data=None,
                error=f"Unknown action: {request.action.value}"
            )
        
        # Execute the handler
        try:
            result = handler(request.parameters)
            return AgentResponse(
                request_id=request.request_id,
                success=True,
                data=result,
                error=None
            )
        except Exception as e:
            logger.error(f"Error processing request {request.request_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                data=None,
                error=str(e)
            )
    
    def _handle_index_project(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle index project request"""
        project_path = parameters.get("project_path")
        if not project_path:
            raise ValueError("Missing required parameter: project_path")
        
        force_reindex = parameters.get("force_reindex", False)
        
        # Define progress callback if provided
        progress_callback = None
        if "callback_url" in parameters:
            callback_url = parameters["callback_url"]
            
            def callback(status: str, progress: float):
                # This would typically send an HTTP request to the callback URL
                # For now, we just log it
                logger.info(f"Indexing progress: {status}, {progress:.2f}")
            
            progress_callback = callback
        
        # Start indexing
        project_id = self.indexer.index_project(
            project_path=project_path,
            progress_callback=progress_callback,
            force_reindex=force_reindex
        )
        
        # Get initial status
        status, progress = self.indexer.get_indexing_status(project_id)
        
        return {
            "project_id": project_id,
            "status": status,
            "progress": progress
        }
    
    def _handle_search_code(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search code request"""
        query = parameters.get("query")
        if not query:
            raise ValueError("Missing required parameter: query")
        
        project_ids = parameters.get("project_ids")
        filters = parameters.get("filters")
        limit = parameters.get("limit", 10)
        
        results = self.search_engine.search(
            query=query,
            project_ids=project_ids,
            filters=filters,
            limit=limit
        )
        
        return {
            "query": query,
            "results": results,
            "result_count": len(results)
        }
    
    def _handle_get_code_context(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get code context request"""
        file_path = parameters.get("file_path")
        line_number = parameters.get("line_number")
        
        if not file_path:
            raise ValueError("Missing required parameter: file_path")
        if not line_number:
            raise ValueError("Missing required parameter: line_number")
        
        context_lines = parameters.get("context_lines", 10)
        
        context = self.search_engine.get_code_context(
            file_path=file_path,
            line_number=line_number,
            context_lines=context_lines
        )
        
        return context
    
    def _handle_analyze_code(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analyze code request"""
        file_path = parameters.get("file_path")
        if not file_path:
            raise ValueError("Missing required parameter: file_path")
        
        analysis_results = self.agent_manager.analyze_code(file_path)
        
        return analysis_results
    
    def _handle_find_similar_code(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle find similar code request"""
        code = parameters.get("code")
        if not code:
            raise ValueError("Missing required parameter: code")
        
        language = parameters.get("language")
        threshold = parameters.get("threshold", 0.7)
        limit = parameters.get("limit", 5)
        
        similar_code = self.search_engine.find_similar_code(
            code=code,
            language=language,
            threshold=threshold,
            limit=limit
        )
        
        return {
            "similar_code": similar_code,
            "result_count": len(similar_code)
        }
    
    def _handle_natural_language_search(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle natural language search request"""
        query = parameters.get("query")
        if not query:
            raise ValueError("Missing required parameter: query")
        
        project_ids = parameters.get("project_ids")
        filters = parameters.get("filters")
        limit = parameters.get("limit", 10)
        
        results = self.search_engine.natural_language_search(
            query=query,
            project_ids=project_ids,
            filters=filters,
            limit=limit
        )
        
        return results
    
    def _handle_get_related_code(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get related code request"""
        code_chunk = parameters.get("code_chunk")
        if not code_chunk:
            raise ValueError("Missing required parameter: code_chunk")
        
        limit = parameters.get("limit", 5)
        
        related_code = self.search_engine.get_related_code(
            code_chunk=code_chunk,
            limit=limit
        )
        
        return {
            "related_code": related_code,
            "result_count": len(related_code)
        }
    
    def _handle_get_file_overview(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get file overview request"""
        file_path = parameters.get("file_path")
        if not file_path:
            raise ValueError("Missing required parameter: file_path")
        
        overview = self.search_engine.get_file_overview(file_path)
        
        return overview

# Example usage:
"""
# Initialize the agent interface
config = Config()
agent_interface = AgentInterface(config)

# Create a request
request = AgentRequest(
    action=ActionType.SEARCH_CODE,
    parameters={
        "query": "function process_data",
        "limit": 5
    },
    request_id="req-123"
)

# Process the request
response = agent_interface.process_request(request)

# Access the response data
if response.success:
    results = response.data
    print(f"Found {len(results['results'])} results")
else:
    print(f"Error: {response.error}")
"""