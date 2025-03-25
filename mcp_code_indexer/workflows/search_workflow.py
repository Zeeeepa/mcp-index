"""
Search Workflow Module
Provides a workflow for searching code
"""

from typing import Dict, List, Any, Optional
import logging
import time
from dataclasses import dataclass, field

from ..workflow import (
    Workflow, WorkflowStep, FunctionStep, ComponentStep, ParallelStep, ConditionalStep,
    WorkflowContext, StepContext, register_workflow
)
from ..interfaces import IndexerProtocol, SearchEngineProtocol, FormatterProtocol
from ..service_locator import get_service_by_type, ServiceCategory
from ..events import EventType, Event, publish, subscribe

logger = logging.getLogger(__name__)

@dataclass
class SearchData:
    """Data for search workflow"""
    query: str
    project_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
    results: List[Dict[str, Any]] = field(default_factory=list)
    formatted_results: Optional[Dict[str, Any]] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    stats: Dict[str, Any] = field(default_factory=dict)

def validate_query(context: StepContext[SearchData]) -> bool:
    """Validate search query"""
    data = context.workflow_context.data
    
    # Check if query is empty
    if not data.query or not data.query.strip():
        context.error = "Search query cannot be empty"
        return False
    
    return True

def search_code(context: StepContext[SearchData]) -> List[Dict[str, Any]]:
    """Search code"""
    data = context.workflow_context.data
    
    # Get search engine
    search_engine = get_service_by_type(SearchEngineProtocol)
    if search_engine is None:
        raise ValueError("Search engine service not found")
    
    # Set start time
    data.start_time = time.time()
    
    # Search code
    try:
        results = search_engine.search(
            data.query,
            project_ids=data.project_ids,
            filters=data.filters,
            limit=data.limit
        )
        
        # Set results
        data.results = results
        data.success = True
        
        return results
    except Exception as e:
        data.error = str(e)
        data.success = False
        raise
    finally:
        # Set end time
        data.end_time = time.time()

def format_results(context: StepContext[SearchData]) -> Dict[str, Any]:
    """Format search results"""
    data = context.workflow_context.data
    
    # Get formatter
    formatter = get_service_by_type(FormatterProtocol)
    if formatter is None:
        raise ValueError("Formatter service not found")
    
    # Format results
    formatted_results = formatter.format_search_results(
        data.results,
        data.query
    )
    
    # Set formatted results
    data.formatted_results = formatted_results
    
    return formatted_results

def collect_stats(context: StepContext[SearchData]) -> Dict[str, Any]:
    """Collect search statistics"""
    data = context.workflow_context.data
    
    # Collect stats
    stats = {
        "query": data.query,
        "duration": data.end_time - data.start_time,
        "result_count": len(data.results),
        "project_count": len(data.project_ids) if data.project_ids else 0
    }
    
    # Set stats
    data.stats = stats
    
    return stats

def handle_error(context: StepContext[SearchData]) -> None:
    """Handle search error"""
    data = context.workflow_context.data
    
    logger.error(f"Search failed: {data.error}")
    
    # Publish error event
    publish(Event(
        EventType.SEARCH_FAILED,
        {
            "query": data.query,
            "error": data.error
        },
        "search_workflow"
    ))

def create_search_workflow() -> Workflow[SearchData, Dict[str, Any]]:
    """Create search workflow"""
    # Create workflow
    workflow = Workflow[SearchData, Dict[str, Any]](
        workflow_id="search",
        name="Code Search Workflow",
        description="Workflow for searching code"
    )
    
    # Create steps
    validate_step = FunctionStep(
        step_id="validate",
        name="Validate Query",
        func=validate_query,
        description="Validate search query"
    )
    
    search_step = FunctionStep(
        step_id="search",
        name="Search Code",
        func=search_code,
        description="Search code"
    )
    
    format_step = FunctionStep(
        step_id="format",
        name="Format Results",
        func=format_results,
        description="Format search results"
    )
    
    stats_step = FunctionStep(
        step_id="stats",
        name="Collect Statistics",
        func=collect_stats,
        description="Collect search statistics"
    )
    
    error_step = FunctionStep(
        step_id="error",
        name="Handle Error",
        func=handle_error,
        description="Handle search error"
    )
    
    # Connect steps
    validate_step.on_success(search_step).on_error(error_step)
    search_step.on_success(format_step).on_error(error_step)
    format_step.on_success(stats_step)
    
    # Set start step
    workflow.set_start_step(validate_step)
    
    return workflow

def search_with_workflow(query: str, project_ids=None, filters=None, limit: int = 10) -> Dict[str, Any]:
    """
    Search code using the search workflow
    
    Args:
        query: Search query
        project_ids: Optional list of project IDs to search
        filters: Optional search filters
        limit: Maximum number of results
        
    Returns:
        Search result
    """
    # Create workflow
    workflow = create_search_workflow()
    
    # Create data
    data = SearchData(
        query=query,
        project_ids=project_ids,
        filters=filters,
        limit=limit
    )
    
    # Execute workflow
    try:
        formatted_results = workflow.execute(data)
        
        # Return result
        return {
            "success": True,
            "results": formatted_results,
            "stats": data.stats
        }
    except Exception as e:
        # Return error
        return {
            "success": False,
            "error": str(e)
        }

# Register workflow
register_workflow(create_search_workflow())