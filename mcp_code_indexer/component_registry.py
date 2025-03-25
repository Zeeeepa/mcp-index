"""
Component Registry Module
Provides a centralized registry for component initialization and registration
"""

from typing import Dict, Any, Optional, List, Set, Type
import logging
import importlib
import inspect
import pkgutil
import sys
from pathlib import Path

from .config import Config
from .di_container import register, register_instance
from .service_locator import register_service, ServiceCategory, ServiceScope
from .interfaces import IndexerProtocol, SearchEngineProtocol, FormatterProtocol, ContextManagerProtocol
from .events import EventType, Event, publish, subscribe
from .indexer import CodeIndexer
from .search_engine import SearchEngine
from .mcp_formatter import McpFormatter
from .context_manager import ContextManager
from .agent_manager import AgentManager

logger = logging.getLogger(__name__)

class ComponentRegistry:
    """Component registry for initializing and registering components"""
    
    def __init__(self, config: Config):
        """
        Initialize component registry
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.components: Dict[str, Any] = {}
        self.initialized = False
    
    def initialize(self) -> None:
        """Initialize all components"""
        if self.initialized:
            return
        
        logger.info("Initializing component registry")
        
        # Register core components
        self._register_core_components()
        
        # Auto-discover and register plugins
        if self.config.get("plugins.auto_discover", False):
            self._discover_plugins()
        
        # Register explicitly configured plugins
        plugin_configs = self.config.get("plugins.enabled", [])
        for plugin_config in plugin_configs:
            self._register_plugin(plugin_config)
        
        self.initialized = True
        
        # Publish system ready event
        publish(Event(
            EventType.SYSTEM_READY,
            {"components": list(self.components.keys())},
            "component_registry"
        ))
        
        logger.info(f"Component registry initialized with {len(self.components)} components")
    
    def _register_core_components(self) -> None:
        """Register core system components"""
        # Create and register context manager
        cache_dir = self.config.get("storage.cache_dir")
        context_manager = ContextManager(cache_dir)
        self._register_component(
            "context_manager",
            context_manager,
            ContextManagerProtocol,
            ServiceCategory.CONTEXT
        )
        
        # Create and register indexer
        indexer = CodeIndexer(self.config)
        self._register_component(
            "indexer",
            indexer,
            IndexerProtocol,
            ServiceCategory.INDEXING
        )
        
        # Create and register search engine
        search_engine = SearchEngine(self.config, indexer)
        self._register_component(
            "search_engine",
            search_engine,
            SearchEngineProtocol,
            ServiceCategory.SEARCH
        )
        
        # Create and register formatter
        formatter = McpFormatter()
        self._register_component(
            "formatter",
            formatter,
            FormatterProtocol,
            ServiceCategory.FORMATTING
        )
        
        # Create and register agent manager if enabled
        if self.config.get("agents.enabled", False):
            agent_manager = AgentManager(self.config, indexer, search_engine)
            self._register_component(
                "agent_manager",
                agent_manager,
                None,  # No interface defined for AgentManager yet
                ServiceCategory.AGENT
            )
    
    def _register_component(self, 
                           component_id: str, 
                           instance: Any, 
                           interface_type: Optional[Type] = None,
                           category: ServiceCategory = ServiceCategory.UTILITY,
                           tags: Optional[Set[str]] = None) -> None:
        """
        Register a component
        
        Args:
            component_id: Component ID
            instance: Component instance
            interface_type: Optional interface type
            category: Service category
            tags: Optional tags
        """
        # Store component
        self.components[component_id] = instance
        
        # Register with DI container
        if interface_type is not None:
            register_instance(interface_type, instance, tags)
        
        # Register with service locator
        register_service(
            service_id=component_id,
            service_type=interface_type or type(instance),
            instance=instance,
            category=category,
            tags=tags
        )
        
        logger.debug(f"Registered component {component_id}")
    
    def _discover_plugins(self) -> None:
        """Auto-discover and register plugins"""
        plugin_dir = self.config.get("plugins.directory", "plugins")
        plugin_path = Path(plugin_dir)
        
        if not plugin_path.exists() or not plugin_path.is_dir():
            logger.warning(f"Plugin directory {plugin_dir} not found")
            return
        
        # Add plugin directory to Python path
        sys.path.insert(0, str(plugin_path))
        
        # Discover plugins
        for _, name, is_pkg in pkgutil.iter_modules([str(plugin_path)]):
            if is_pkg and name.startswith("mcp_"):
                try:
                    # Import plugin module
                    plugin_module = importlib.import_module(name)
                    
                    # Look for plugin registration function
                    if hasattr(plugin_module, "register_plugin"):
                        plugin_module.register_plugin(self)
                        logger.info(f"Registered plugin {name}")
                    else:
                        logger.warning(f"Plugin {name} has no register_plugin function")
                except Exception as e:
                    logger.error(f"Error loading plugin {name}: {str(e)}")
    
    def _register_plugin(self, plugin_config: Dict[str, Any]) -> None:
        """
        Register a plugin from configuration
        
        Args:
            plugin_config: Plugin configuration
        """
        plugin_name = plugin_config.get("name")
        plugin_module = plugin_config.get("module")
        
        if not plugin_name or not plugin_module:
            logger.warning("Invalid plugin configuration: missing name or module")
            return
        
        try:
            # Import plugin module
            module = importlib.import_module(plugin_module)
            
            # Look for plugin registration function
            if hasattr(module, "register_plugin"):
                module.register_plugin(self)
                logger.info(f"Registered plugin {plugin_name}")
            else:
                logger.warning(f"Plugin {plugin_name} has no register_plugin function")
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {str(e)}")
    
    def get_component(self, component_id: str) -> Optional[Any]:
        """
        Get a component by ID
        
        Args:
            component_id: Component ID
            
        Returns:
            Component instance or None if not found
        """
        return self.components.get(component_id)
    
    def get_all_components(self) -> Dict[str, Any]:
        """
        Get all registered components
        
        Returns:
            Dictionary of component ID to instance
        """
        return self.components.copy()

def initialize_components(config: Config) -> ComponentRegistry:
    """
    Initialize all components
    
    Args:
        config: Configuration object
        
    Returns:
        Component registry
    """
    registry = ComponentRegistry(config)
    registry.initialize()
    return registry