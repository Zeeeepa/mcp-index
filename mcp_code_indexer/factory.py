"""
Factory Module
Provides factory methods for creating and initializing components
"""

from typing import Dict, Any, Optional
from .config import Config
from .indexer import CodeIndexer
from .search_engine import SearchEngine
from .agent_manager import AgentManager

def create_indexer(config: Config) -> CodeIndexer:
    """
    Create and initialize a CodeIndexer instance
    
    Args:
        config: Configuration object
        
    Returns:
        Initialized CodeIndexer instance
    """
    return CodeIndexer(config)

def create_search_engine(config: Config, indexer: CodeIndexer) -> SearchEngine:
    """
    Create and initialize a SearchEngine instance
    
    Args:
        config: Configuration object
        indexer: CodeIndexer instance
        
    Returns:
        Initialized SearchEngine instance
    """
    return SearchEngine(config, indexer)

def create_agent_manager(config: Config, indexer: CodeIndexer, search_engine: SearchEngine) -> Optional[AgentManager]:
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
        return AgentManager(config, indexer, search_engine)
    return None

def create_all_components(config: Config) -> Dict[str, Any]:
    """
    Create all components and return them in a dictionary
    
    Args:
        config: Configuration object
        
    Returns:
        Dictionary containing all initialized components
    """
    indexer = create_indexer(config)
    search_engine = create_search_engine(config, indexer)
    agent_manager = create_agent_manager(config, indexer, search_engine)
    
    return {
        "indexer": indexer,
        "search_engine": search_engine,
        "agent_manager": agent_manager
    }