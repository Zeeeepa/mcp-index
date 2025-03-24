"""
Client Example Script

This script demonstrates how to use the MCP Code Indexer client library.
"""

import os
import sys
import time
import logging
from typing import Dict, Any

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_code_indexer.client import MCPIndexerClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function"""
    # Initialize client
    client = MCPIndexerClient(base_url="http://localhost:8000")
    
    # Example project path (replace with your own)
    project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Index the project
    logger.info(f"Indexing project: {project_path}")
    task = client.index_project(project_path=project_path, force_reindex=True)
    task_id = task["task_id"]
    
    # Poll for task completion
    while True:
        task_status = client.get_task_status(task_id)
        logger.info(f"Task status: {task_status['status']}, progress: {task_status['progress']:.2f}")
        
        if task_status["status"] in ["completed", "failed"]:
            break
        
        time.sleep(1)
    
    if task_status["status"] == "failed":
        logger.error(f"Task failed: {task_status.get('error')}")
        return
    
    # Get all indexed projects
    logger.info("Getting all indexed projects")
    projects = client.get_projects()
    logger.info(f"Found {len(projects.get('projects', []))} indexed projects")
    
    # Search for code
    logger.info("Searching for code")
    search_results = client.search_code(query="def main")
    logger.info(f"Found {search_results.get('result_count', 0)} search results")
    
    # Print the first search result
    if search_results.get("results"):
        result = search_results["results"][0]
        logger.info(f"First result: {result.get('file_path')} (lines {result.get('start_line')}-{result.get('end_line')})")
        logger.info(f"Content: {result.get('content')[:100]}...")
    
    # Get file overview
    if search_results.get("results"):
        file_path = search_results["results"][0].get("file_path")
        logger.info(f"Getting file overview for {file_path}")
        overview = client.get_file_overview(file_path=file_path)
        logger.info(f"File overview: {overview.get('file_name')}, {overview.get('line_count')} lines")
    
    # WebSocket example
    logger.info("Connecting to WebSocket")
    
    # Define WebSocket callbacks
    def on_message(data: Dict[str, Any]):
        logger.info(f"Received WebSocket message: {data}")
    
    def on_error(error: Exception):
        logger.error(f"WebSocket error: {str(error)}")
    
    def on_close():
        logger.info("WebSocket connection closed")
    
    # Connect to WebSocket
    client.connect_ws(on_message=on_message, on_error=on_error, on_close=on_close)
    
    # Subscribe to topics
    client.subscribe(topic="indexing_updates")
    client.subscribe(topic="search_updates")
    
    # Send a WebSocket request
    logger.info("Sending WebSocket request")
    
    def on_response(data: Dict[str, Any]):
        logger.info(f"Received WebSocket response: {data}")
    
    client.ws_request(
        action="search_code",
        parameters={"query": "class", "limit": 3},
        callback=on_response
    )
    
    # Wait for WebSocket response
    time.sleep(2)
    
    # Disconnect from WebSocket
    logger.info("Disconnecting from WebSocket")
    client.disconnect_ws()
    
    logger.info("Example completed")

if __name__ == "__main__":
    main()