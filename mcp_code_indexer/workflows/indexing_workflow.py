"""
Indexing Workflow Module
Provides a workflow for indexing projects
"""

from typing import Dict, Any, Optional
import logging
import time
from dataclasses import dataclass

from ..workflow import (
    Workflow, WorkflowStep, FunctionStep, ComponentStep, ParallelStep, ConditionalStep,
    WorkflowContext, StepContext, register_workflow
)
from ..interfaces import IndexerProtocol, SearchEngineProtocol
from ..service_locator import get_service_by_type, ServiceCategory
from ..events import EventType, Event, publish, subscribe

logger = logging.getLogger(__name__)

@dataclass
class IndexingData:
    """Data for indexing workflow"""
    project_path: str
    force_reindex: bool = False
    project_id: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    stats: Dict[str, Any] = None

def validate_project_path(context: StepContext[IndexingData]) -> bool:
    """Validate project path"""
    import os
    
    project_path = context.workflow_context.data.project_path
    
    # Check if path exists
    if not os.path.exists(project_path):
        context.error = f"Project path does not exist: {project_path}"
        return False
    
    # Check if path is a directory
    if not os.path.isdir(project_path):
        context.error = f"Project path is not a directory: {project_path}"
        return False
    
    return True

def index_project(context: StepContext[IndexingData]) -> str:
    """Index project"""
    data = context.workflow_context.data
    
    # Get indexer
    indexer = get_service_by_type(IndexerProtocol)
    if indexer is None:
        raise ValueError("Indexer service not found")
    
    # Set start time
    data.start_time = time.time()
    
    # Index project
    try:
        project_id = indexer.index_project(
            data.project_path,
            force_reindex=data.force_reindex
        )
        
        # Set project ID
        data.project_id = project_id
        data.success = True
        
        return project_id
    except Exception as e:
        data.error = str(e)
        data.success = False
        raise
    finally:
        # Set end time
        data.end_time = time.time()

def collect_stats(context: StepContext[IndexingData]) -> Dict[str, Any]:
    """Collect indexing statistics"""
    data = context.workflow_context.data
    
    # Get indexer
    indexer = get_service_by_type(IndexerProtocol)
    if indexer is None:
        raise ValueError("Indexer service not found")
    
    # Get project info
    projects = indexer.get_indexed_projects()
    project_info = next((p for p in projects if p.get("id") == data.project_id), None)
    
    if project_info is None:
        raise ValueError(f"Project not found: {data.project_id}")
    
    # Collect stats
    stats = {
        "project_id": data.project_id,
        "duration": data.end_time - data.start_time,
        "file_count": project_info.get("file_count", 0),
        "chunk_count": project_info.get("chunk_count", 0),
        "size": project_info.get("size", 0)
    }
    
    # Set stats
    data.stats = stats
    
    return stats

def handle_error(context: StepContext[IndexingData]) -> None:
    """Handle indexing error"""
    data = context.workflow_context.data
    
    logger.error(f"Indexing failed: {data.error}")
    
    # Publish error event
    publish(Event(
        EventType.INDEXING_FAILED,
        {
            "project_path": data.project_path,
            "error": data.error
        },
        "indexing_workflow"
    ))

def create_indexing_workflow() -> Workflow[IndexingData, str]:
    """Create indexing workflow"""
    # Create workflow
    workflow = Workflow[IndexingData, str](
        workflow_id="indexing",
        name="Project Indexing Workflow",
        description="Workflow for indexing projects"
    )
    
    # Create steps
    validate_step = FunctionStep(
        step_id="validate",
        name="Validate Project Path",
        func=validate_project_path,
        description="Validate project path"
    )
    
    index_step = FunctionStep(
        step_id="index",
        name="Index Project",
        func=index_project,
        description="Index project"
    )
    
    stats_step = FunctionStep(
        step_id="stats",
        name="Collect Statistics",
        func=collect_stats,
        description="Collect indexing statistics"
    )
    
    error_step = FunctionStep(
        step_id="error",
        name="Handle Error",
        func=handle_error,
        description="Handle indexing error"
    )
    
    # Connect steps
    validate_step.on_success(index_step).on_error(error_step)
    index_step.on_success(stats_step).on_error(error_step)
    
    # Set start step
    workflow.set_start_step(validate_step)
    
    return workflow

def index_project_with_workflow(project_path: str, force_reindex: bool = False) -> Dict[str, Any]:
    """
    Index a project using the indexing workflow
    
    Args:
        project_path: Path to the project
        force_reindex: Whether to force reindexing
        
    Returns:
        Indexing result
    """
    # Create workflow
    workflow = create_indexing_workflow()
    
    # Create data
    data = IndexingData(
        project_path=project_path,
        force_reindex=force_reindex
    )
    
    # Execute workflow
    try:
        project_id = workflow.execute(data)
        
        # Return result
        return {
            "success": True,
            "project_id": project_id,
            "stats": data.stats
        }
    except Exception as e:
        # Return error
        return {
            "success": False,
            "error": str(e)
        }

# Register workflow
register_workflow(create_indexing_workflow())