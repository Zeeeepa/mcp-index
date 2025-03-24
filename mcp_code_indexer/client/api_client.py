"""
API Client Module

Provides a client library for interacting with the MCP Code Indexer API.
"""

import json
import logging
import requests
import websocket
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum

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

class MCPIndexerClient:
    """
    MCP Code Indexer API Client
    
    Provides a client library for interacting with the MCP Code Indexer API.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the API server
            
        Returns:
            None
        """
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api"
        self.ws_url = f"{self.base_url.replace('http://', 'ws://').replace('https://', 'wss://')}/ws-api/ws"
        
        # WebSocket connection
        self.ws = None
        self.ws_connected = False
        self.ws_callbacks = {}
        self.ws_lock = threading.Lock()
        
        logger.info(f"Initialized MCP Code Indexer client with base URL: {self.base_url}")
    
    def index_project(self, project_path: str, force_reindex: bool = False) -> Dict[str, Any]:
        """
        Index a project
        
        Args:
            project_path: Path to the project
            force_reindex: Whether to force reindexing
            
        Returns:
            Task information
        """
        url = f"{self.api_url}/index-project"
        data = {
            "project_path": project_path,
            "force_reindex": force_reindex
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get task status
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status
        """
        url = f"{self.api_url}/tasks/{task_id}"
        
        response = requests.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def search_code(self, query: str, project_ids: Optional[List[str]] = None,
                   filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> Dict[str, Any]:
        """
        Search code
        
        Args:
            query: Search query
            project_ids: List of project IDs to search
            filters: Filters to apply
            limit: Maximum number of results
            
        Returns:
            Search results
        """
        url = f"{self.api_url}/search-code"
        data = {
            "query": query,
            "project_ids": project_ids,
            "filters": filters,
            "limit": limit
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_code_context(self, file_path: str, line_number: int, 
                        context_lines: int = 10) -> Dict[str, Any]:
        """
        Get code context
        
        Args:
            file_path: Path to the file
            line_number: Line number
            context_lines: Number of context lines
            
        Returns:
            Code context
        """
        url = f"{self.api_url}/get-code-context"
        data = {
            "file_path": file_path,
            "line_number": line_number,
            "context_lines": context_lines
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def analyze_code(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze code
        
        Args:
            file_path: Path to the file
            
        Returns:
            Analysis results
        """
        url = f"{self.api_url}/analyze-code"
        data = {
            "file_path": file_path
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def find_similar_code(self, code: str, language: Optional[str] = None,
                         threshold: float = 0.7, limit: int = 5) -> Dict[str, Any]:
        """
        Find similar code
        
        Args:
            code: Code to find similar code for
            language: Programming language
            threshold: Similarity threshold
            limit: Maximum number of results
            
        Returns:
            Similar code results
        """
        url = f"{self.api_url}/find-similar-code"
        data = {
            "code": code,
            "language": language,
            "threshold": threshold,
            "limit": limit
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def natural_language_search(self, query: str, project_ids: Optional[List[str]] = None,
                              filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> Dict[str, Any]:
        """
        Natural language search
        
        Args:
            query: Natural language query
            project_ids: List of project IDs to search
            filters: Filters to apply
            limit: Maximum number of results
            
        Returns:
            Search results
        """
        url = f"{self.api_url}/natural-language-search"
        data = {
            "query": query,
            "project_ids": project_ids,
            "filters": filters,
            "limit": limit
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_related_code(self, code_chunk: Dict[str, Any], limit: int = 5) -> Dict[str, Any]:
        """
        Get related code
        
        Args:
            code_chunk: Code chunk to find related code for
            limit: Maximum number of results
            
        Returns:
            Related code results
        """
        url = f"{self.api_url}/get-related-code"
        data = {
            "code_chunk": code_chunk,
            "limit": limit
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_file_overview(self, file_path: str) -> Dict[str, Any]:
        """
        Get file overview
        
        Args:
            file_path: Path to the file
            
        Returns:
            File overview
        """
        url = f"{self.api_url}/get-file-overview"
        data = {
            "file_path": file_path
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_projects(self) -> Dict[str, Any]:
        """
        Get all indexed projects
        
        Returns:
            List of projects
        """
        url = f"{self.api_url}/projects"
        
        response = requests.get(url)
        response.raise_for_status()
        
        return response.json()
    
    # WebSocket methods
    def connect_ws(self, on_message: Optional[Callable[[Dict[str, Any]], None]] = None,
                  on_error: Optional[Callable[[Exception], None]] = None,
                  on_close: Optional[Callable[[], None]] = None) -> None:
        """
        Connect to the WebSocket API
        
        Args:
            on_message: Callback for messages
            on_error: Callback for errors
            on_close: Callback for connection close
            
        Returns:
            None
        """
        if self.ws_connected:
            return
        
        def on_ws_message(ws, message):
            try:
                data = json.loads(message)
                
                # Handle response messages
                if data.get("type") == "response":
                    request_id = data.get("request_id")
                    if request_id in self.ws_callbacks:
                        callback = self.ws_callbacks.pop(request_id)
                        callback(data)
                
                # Call the user's callback
                if on_message:
                    on_message(data)
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                if on_error:
                    on_error(e)
        
        def on_ws_error(ws, error):
            logger.error(f"WebSocket error: {str(error)}")
            if on_error:
                on_error(error)
        
        def on_ws_close(ws, close_status_code, close_msg):
            logger.info("WebSocket connection closed")
            self.ws_connected = False
            if on_close:
                on_close()
        
        def on_ws_open(ws):
            logger.info("WebSocket connection established")
            self.ws_connected = True
        
        # Create WebSocket connection
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=on_ws_message,
            on_error=on_ws_error,
            on_close=on_ws_close,
            on_open=on_ws_open
        )
        
        # Start WebSocket thread
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Wait for connection to establish
        for _ in range(10):
            if self.ws_connected:
                break
            time.sleep(0.1)
    
    def disconnect_ws(self) -> None:
        """
        Disconnect from the WebSocket API
        
        Returns:
            None
        """
        if self.ws:
            self.ws.close()
            self.ws = None
            self.ws_connected = False
    
    def subscribe(self, topic: str) -> None:
        """
        Subscribe to a topic
        
        Args:
            topic: Topic to subscribe to
            
        Returns:
            None
        """
        if not self.ws_connected:
            self.connect_ws()
        
        message = {
            "type": "subscribe",
            "topic": topic
        }
        
        self.ws.send(json.dumps(message))
    
    def unsubscribe(self, topic: str) -> None:
        """
        Unsubscribe from a topic
        
        Args:
            topic: Topic to unsubscribe from
            
        Returns:
            None
        """
        if not self.ws_connected:
            return
        
        message = {
            "type": "unsubscribe",
            "topic": topic
        }
        
        self.ws.send(json.dumps(message))
    
    def ws_request(self, action: Union[ActionType, str], parameters: Dict[str, Any],
                 callback: Callable[[Dict[str, Any]], None]) -> str:
        """
        Send a request via WebSocket
        
        Args:
            action: Action to perform
            parameters: Parameters for the action
            callback: Callback for the response
            
        Returns:
            Request ID
        """
        if not self.ws_connected:
            self.connect_ws()
        
        # Convert action to string if it's an enum
        if isinstance(action, ActionType):
            action = action.value
        
        # Generate request ID
        import uuid
        request_id = str(uuid.uuid4())
        
        # Register callback
        with self.ws_lock:
            self.ws_callbacks[request_id] = callback
        
        # Send request
        message = {
            "type": "request",
            "action": action,
            "parameters": parameters,
            "request_id": request_id
        }
        
        self.ws.send(json.dumps(message))
        
        return request_id