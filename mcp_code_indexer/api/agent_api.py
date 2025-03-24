"""
Agent API Module

Provides a REST API for interacting with the mcp-index codebase.
This module exposes the AgentInterface functionality through a FastAPI server.
"""

import os
import logging
import uuid
from typing import Dict, List, Any, Optional, Union
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..config import Config
from ..agent_interface import AgentInterface, AgentRequest, AgentResponse, ActionType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Code Indexer API",
    description="API for interacting with the MCP Code Indexer",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize config and agent interface
config = Config()
agent_interface = AgentInterface(config)

# Background tasks storage
background_tasks = {}

# Pydantic models for API requests and responses
class IndexProjectRequest(BaseModel):
    project_path: str
    force_reindex: bool = False

class SearchCodeRequest(BaseModel):
    query: str
    project_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10

class GetCodeContextRequest(BaseModel):
    file_path: str
    line_number: int
    context_lines: int = 10

class AnalyzeCodeRequest(BaseModel):
    file_path: str

class FindSimilarCodeRequest(BaseModel):
    code: str
    language: Optional[str] = None
    threshold: float = 0.7
    limit: int = 5

class NaturalLanguageSearchRequest(BaseModel):
    query: str
    project_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10

class GetRelatedCodeRequest(BaseModel):
    code_chunk: Dict[str, Any]
    limit: int = 5

class GetFileOverviewRequest(BaseModel):
    file_path: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Helper functions
def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get the status of a background task"""
    if task_id not in background_tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return background_tasks[task_id]

def update_task_status(task_id: str, status: str, progress: float = 0.0, 
                      result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
    """Update the status of a background task"""
    background_tasks[task_id] = {
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "result": result,
        "error": error
    }

def process_request_background(action: ActionType, parameters: Dict[str, Any], task_id: str) -> None:
    """Process a request in the background"""
    try:
        # Create agent request
        request = AgentRequest(
            action=action,
            parameters=parameters,
            request_id=task_id
        )
        
        # Process request
        response = agent_interface.process_request(request)
        
        # Update task status
        if response.success:
            update_task_status(task_id, "completed", 1.0, response.data)
        else:
            update_task_status(task_id, "failed", 0.0, None, response.error)
    except Exception as e:
        logger.error(f"Error processing background task {task_id}: {str(e)}")
        update_task_status(task_id, "failed", 0.0, None, str(e))

# API endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "MCP Code Indexer API"}

@app.post("/index-project", response_model=TaskStatusResponse)
async def index_project(request: IndexProjectRequest, background_tasks: BackgroundTasks):
    """Index a project"""
    task_id = str(uuid.uuid4())
    
    # Initialize task status
    update_task_status(task_id, "pending")
    
    # Start background task
    background_tasks.add_task(
        process_request_background,
        ActionType.INDEX_PROJECT,
        request.dict(),
        task_id
    )
    
    return get_task_status(task_id)

@app.post("/search-code")
async def search_code(request: SearchCodeRequest):
    """Search code"""
    agent_request = AgentRequest(
        action=ActionType.SEARCH_CODE,
        parameters=request.dict(),
        request_id=str(uuid.uuid4())
    )
    
    response = agent_interface.process_request(agent_request)
    
    if response.success:
        return response.data
    else:
        raise HTTPException(status_code=400, detail=response.error)

@app.post("/get-code-context")
async def get_code_context(request: GetCodeContextRequest):
    """Get code context"""
    agent_request = AgentRequest(
        action=ActionType.GET_CODE_CONTEXT,
        parameters=request.dict(),
        request_id=str(uuid.uuid4())
    )
    
    response = agent_interface.process_request(agent_request)
    
    if response.success:
        return response.data
    else:
        raise HTTPException(status_code=400, detail=response.error)

@app.post("/analyze-code")
async def analyze_code(request: AnalyzeCodeRequest):
    """Analyze code"""
    agent_request = AgentRequest(
        action=ActionType.ANALYZE_CODE,
        parameters=request.dict(),
        request_id=str(uuid.uuid4())
    )
    
    response = agent_interface.process_request(agent_request)
    
    if response.success:
        return response.data
    else:
        raise HTTPException(status_code=400, detail=response.error)

@app.post("/find-similar-code")
async def find_similar_code(request: FindSimilarCodeRequest):
    """Find similar code"""
    agent_request = AgentRequest(
        action=ActionType.FIND_SIMILAR_CODE,
        parameters=request.dict(),
        request_id=str(uuid.uuid4())
    )
    
    response = agent_interface.process_request(agent_request)
    
    if response.success:
        return response.data
    else:
        raise HTTPException(status_code=400, detail=response.error)

@app.post("/natural-language-search")
async def natural_language_search(request: NaturalLanguageSearchRequest):
    """Natural language search"""
    agent_request = AgentRequest(
        action=ActionType.NATURAL_LANGUAGE_SEARCH,
        parameters=request.dict(),
        request_id=str(uuid.uuid4())
    )
    
    response = agent_interface.process_request(agent_request)
    
    if response.success:
        return response.data
    else:
        raise HTTPException(status_code=400, detail=response.error)

@app.post("/get-related-code")
async def get_related_code(request: GetRelatedCodeRequest):
    """Get related code"""
    agent_request = AgentRequest(
        action=ActionType.GET_RELATED_CODE,
        parameters=request.dict(),
        request_id=str(uuid.uuid4())
    )
    
    response = agent_interface.process_request(agent_request)
    
    if response.success:
        return response.data
    else:
        raise HTTPException(status_code=400, detail=response.error)

@app.post("/get-file-overview")
async def get_file_overview(request: GetFileOverviewRequest):
    """Get file overview"""
    agent_request = AgentRequest(
        action=ActionType.GET_FILE_OVERVIEW,
        parameters=request.dict(),
        request_id=str(uuid.uuid4())
    )
    
    response = agent_interface.process_request(agent_request)
    
    if response.success:
        return response.data
    else:
        raise HTTPException(status_code=400, detail=response.error)

@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task(task_id: str):
    """Get task status"""
    return get_task_status(task_id)

@app.get("/projects")
async def get_projects():
    """Get all indexed projects"""
    try:
        projects = agent_interface.indexer.get_indexed_projects()
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

# Run the API server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)