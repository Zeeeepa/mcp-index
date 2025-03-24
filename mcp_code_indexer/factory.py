"""
Factory Module
Provides factory methods for creating and initializing components
"""

from typing import Dict, Any, Optional, Type, TypeVar, cast
from .config import Config
from .indexer import CodeIndexer
from .search_engine import SearchEngine
from .agent_manager import AgentManager
from .mcp_formatter import McpFormatter
from .context_manager import ContextManager
from .interfaces import IndexerProtocol, SearchEngineProtocol, FormatterProtocol, ContextManagerProtocol
from .events import EventType, Event, publish

# Generic type for component protocols
T = TypeVar('T')

def create_indexer(config: Config) -> IndexerProtocol:
    """
    Create and initialize a CodeIndexer instance
    
    Args:
        config: Configuration object
        
    Returns:
        Initialized CodeIndexer instance
    """
    indexer = CodeIndexer(config)
    publish(Event(EventType.COMPONENT_INITIALIZED, {"component": "indexer"}, "factory"))
    return indexer

def create_search_engine(config: Config, indexer: IndexerProtocol) -> SearchEngineProtocol:
    """
    Create and initialize a SearchEngine instance
    
    Args:
        config: Configuration object
        indexer: CodeIndexer instance
        
    Returns:
        Initialized SearchEngine instance
    """
    search_engine = SearchEngine(config, indexer)
    publish(Event(EventType.COMPONENT_INITIALIZED, {"component": "search_engine"}, "factory"))
    return search_engine

def create_formatter() -> FormatterProtocol:
    """
    Create and initialize a McpFormatter instance
    
    Returns:
        Initialized McpFormatter instance
    """
    formatter = McpFormatter()
    publish(Event(EventType.COMPONENT_INITIALIZED, {"component": "formatter"}, "factory"))
    return formatter

def create_context_manager(config: Config = None) -> ContextManagerProtocol:
    """
    Create and initialize a ContextManager instance
    
    Args:
        config: Optional configuration object
        
    Returns:
        Initialized ContextManager instance
    """
    cache_dir = config.get("storage.cache_dir") if config else None
    context_manager = ContextManager(cache_dir)
    publish(Event(EventType.COMPONENT_INITIALIZED, {"component": "context_manager"}, "factory"))
    return context_manager

def create_agent_manager(config: Config, indexer: IndexerProtocol, search_engine: SearchEngineProtocol) -> Optional[AgentManager]:
    """
    Create and initialize an AgentManager instance if enabled
    
    Args:
        config: Configuration object
        indexer: CodeIndexer instance
        search_engine: SearchEngine instance
        
    Returns:
        AgentManager instance or None if disabled
    """
    if config.get("agents.enabled", False):
        agent_manager = AgentManager(config, indexer, search_engine)
        publish(Event(EventType.COMPONENT_INITIALIZED, {"component": "agent_manager"}, "factory"))
        return agent_manager
    return None

def create_all_components(config: Config) -> Dict[str, Any]:
    """
    Create all components and return them in a dictionary
    
    Args:
        config: Configuration object
        
    Returns:
        Dictionary containing all initialized components
    """
    context_manager = create_context_manager(config)
    indexer = create_indexer(config)
    search_engine = create_search_engine(config, indexer)
    formatter = create_formatter()
    agent_manager = create_agent_manager(config, indexer, search_engine)
    
    components = {
        "indexer": indexer,
        "search_engine": search_engine,
        "formatter": formatter,
        "context_manager": context_manager,
        "agent_manager": agent_manager
    }
    
    # Notify system is ready
    publish(Event(EventType.SYSTEM_READY, {"components": list(components.keys())}, "factory"))
    
    return components

def get_component_instance(component_class: Type[T], components: Dict[str, Any]) -> Optional[T]:
    """
    Get a component instance by its class type
    
    Args:
        component_class: Component class type
        components: Dictionary of components
        
    Returns:
        Component instance or None if not found
    """
    for component in components.values():
        if isinstance(component, component_class):
            return cast(T, component)
    return None