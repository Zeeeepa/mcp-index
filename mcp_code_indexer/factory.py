"""
Factory Module
Provides factory methods for creating and initializing components
"""

from typing import Dict, Any, Optional
from .config import Config
from .indexer import CodeIndexer
from .search_engine import SearchEngine
from .agent_manager import AgentManager
from .context_manager import ContextManager
from .code_analyzer import CodeAnalyzer
from .relevant_context_retriever import ContextAwareSearchEngine, RelevantCodeContextRetriever

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

def create_context_manager(config: Config) -> ContextManager:
    """
    Create and initialize a ContextManager instance
    
    Args:
        config: Configuration object
        
    Returns:
        Initialized ContextManager instance
    """
    cache_dir = config.get("storage.cache_dir", None)
    return ContextManager(cache_dir)

def create_code_analyzer() -> CodeAnalyzer:
    """
    Create and initialize a CodeAnalyzer instance
    
    Returns:
        Initialized CodeAnalyzer instance
    """
    return CodeAnalyzer()

def create_context_aware_search(config: Config, search_engine: SearchEngine, 
                              context_manager: ContextManager) -> ContextAwareSearchEngine:
    """
    Create and initialize a ContextAwareSearchEngine instance
    
    Args:
        config: Configuration object
        search_engine: SearchEngine instance
        context_manager: ContextManager instance
        
    Returns:
        Initialized ContextAwareSearchEngine instance
    """
    return ContextAwareSearchEngine(search_engine, context_manager)

def create_relevant_context_retriever(config: Config) -> RelevantCodeContextRetriever:
    """
    Create and initialize a RelevantCodeContextRetriever instance
    
    Args:
        config: Configuration object
        
    Returns:
        Initialized RelevantCodeContextRetriever instance
    """
    return RelevantCodeContextRetriever(config)

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
    context_manager = create_context_manager(config)
    code_analyzer = create_code_analyzer()
    context_aware_search = create_context_aware_search(config, search_engine, context_manager)
    relevant_context_retriever = create_relevant_context_retriever(config)
    
    return {
        "indexer": indexer,
        "search_engine": search_engine,
        "agent_manager": agent_manager,
        "context_manager": context_manager,
        "code_analyzer": code_analyzer,
        "context_aware_search": context_aware_search,
        "relevant_context_retriever": relevant_context_retriever
    }