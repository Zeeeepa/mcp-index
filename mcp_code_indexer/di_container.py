"""
Dependency Injection Container Module
Provides a centralized container for managing component dependencies and lifecycle
"""

from typing import Dict, Any, Type, TypeVar, Optional, Callable, List, Set
import logging
import threading
from enum import Enum

from .interfaces import IndexerProtocol, SearchEngineProtocol, FormatterProtocol, ContextManagerProtocol
from .events import EventType, Event, publish, subscribe

logger = logging.getLogger(__name__)

# Generic type for component interfaces
T = TypeVar('T')
R = TypeVar('R')

class ComponentScope(Enum):
    """Component lifecycle scopes"""
    SINGLETON = "singleton"  # One instance for the entire application
    TRANSIENT = "transient"  # New instance created each time
    SCOPED = "scoped"        # One instance per scope (e.g., request)

class ComponentLifecycle(Enum):
    """Component lifecycle events"""
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    STARTED = "started"
    STOPPING = "stopping"
    STOPPED = "stopped"
    DISPOSING = "disposing"
    DISPOSED = "disposed"

class ComponentRegistration:
    """Component registration information"""
    
    def __init__(self, 
                 interface_type: Type, 
                 implementation_type: Type, 
                 factory: Optional[Callable[..., Any]] = None,
                 scope: ComponentScope = ComponentScope.SINGLETON,
                 dependencies: Optional[List[Type]] = None,
                 tags: Optional[Set[str]] = None):
        """
        Initialize component registration
        
        Args:
            interface_type: Interface type
            implementation_type: Implementation type
            factory: Optional factory function
            scope: Component lifecycle scope
            dependencies: List of dependency types
            tags: Optional tags for component categorization
        """
        self.interface_type = interface_type
        self.implementation_type = implementation_type
        self.factory = factory
        self.scope = scope
        self.dependencies = dependencies or []
        self.tags = tags or set()
        self.instance = None
        self.initialized = False

class DIContainer:
    """Dependency Injection Container"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern implementation"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DIContainer, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the container"""
        if self._initialized:
            return
            
        self._registrations: Dict[Type, ComponentRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self._initialized = True
        logger.info("DI Container initialized")
        
        # Subscribe to system shutdown event to dispose components
        subscribe(EventType.SYSTEM_SHUTDOWN, self._handle_system_shutdown)
    
    def register(self, 
                interface_type: Type[T], 
                implementation_type: Type,
                factory: Optional[Callable[..., T]] = None,
                scope: ComponentScope = ComponentScope.SINGLETON,
                dependencies: Optional[List[Type]] = None,
                tags: Optional[Set[str]] = None) -> None:
        """
        Register a component
        
        Args:
            interface_type: Interface type
            implementation_type: Implementation type
            factory: Optional factory function
            scope: Component lifecycle scope
            dependencies: List of dependency types
            tags: Optional tags for component categorization
        """
        registration = ComponentRegistration(
            interface_type=interface_type,
            implementation_type=implementation_type,
            factory=factory,
            scope=scope,
            dependencies=dependencies,
            tags=tags
        )
        
        self._registrations[interface_type] = registration
        logger.debug(f"Registered {interface_type.__name__} -> {implementation_type.__name__}")
    
    def register_instance(self, interface_type: Type[T], instance: T, tags: Optional[Set[str]] = None) -> None:
        """
        Register an existing instance
        
        Args:
            interface_type: Interface type
            instance: Component instance
            tags: Optional tags for component categorization
        """
        registration = ComponentRegistration(
            interface_type=interface_type,
            implementation_type=type(instance),
            scope=ComponentScope.SINGLETON,
            tags=tags
        )
        
        registration.instance = instance
        registration.initialized = True
        
        self._registrations[interface_type] = registration
        self._instances[interface_type] = instance
        
        logger.debug(f"Registered instance of {interface_type.__name__}")
    
    def resolve(self, interface_type: Type[T]) -> Optional[T]:
        """
        Resolve a component by interface type
        
        Args:
            interface_type: Interface type
            
        Returns:
            Component instance or None if not registered
        """
        # Check if already instantiated for singleton scope
        if interface_type in self._instances:
            return self._instances[interface_type]
        
        # Check if registered
        if interface_type not in self._registrations:
            logger.warning(f"No registration found for {interface_type.__name__}")
            return None
        
        registration = self._registrations[interface_type]
        
        # Publish lifecycle event
        self._publish_lifecycle_event(registration, ComponentLifecycle.INITIALIZING)
        
        # Create instance
        instance = self._create_instance(registration)
        
        if instance is not None:
            # Store instance for singleton scope
            if registration.scope == ComponentScope.SINGLETON:
                self._instances[interface_type] = instance
            
            # Mark as initialized
            registration.initialized = True
            
            # Publish lifecycle event
            self._publish_lifecycle_event(registration, ComponentLifecycle.INITIALIZED)
        
        return instance
    
    def resolve_all(self, interface_type: Type[T]) -> List[T]:
        """
        Resolve all components implementing an interface
        
        Args:
            interface_type: Interface type
            
        Returns:
            List of component instances
        """
        instances = []
        
        for reg_type, registration in self._registrations.items():
            if issubclass(registration.implementation_type, interface_type):
                instance = self.resolve(reg_type)
                if instance is not None:
                    instances.append(instance)
        
        return instances
    
    def resolve_by_tag(self, tag: str) -> List[Any]:
        """
        Resolve components by tag
        
        Args:
            tag: Component tag
            
        Returns:
            List of component instances
        """
        instances = []
        
        for reg_type, registration in self._registrations.items():
            if tag in registration.tags:
                instance = self.resolve(reg_type)
                if instance is not None:
                    instances.append(instance)
        
        return instances
    
    def _create_instance(self, registration: ComponentRegistration) -> Optional[Any]:
        """
        Create a component instance
        
        Args:
            registration: Component registration
            
        Returns:
            Component instance or None if creation failed
        """
        try:
            # Use factory if provided
            if registration.factory is not None:
                # Resolve dependencies
                dependencies = [self.resolve(dep_type) for dep_type in registration.dependencies]
                
                # Create instance using factory
                instance = registration.factory(*dependencies)
            else:
                # Resolve dependencies
                dependencies = [self.resolve(dep_type) for dep_type in registration.dependencies]
                
                # Create instance using constructor
                instance = registration.implementation_type(*dependencies)
            
            return instance
        except Exception as e:
            logger.error(f"Error creating instance of {registration.implementation_type.__name__}: {str(e)}")
            
            # Publish component error event
            publish(Event(
                EventType.COMPONENT_ERROR, 
                {
                    "component": registration.implementation_type.__name__,
                    "error": str(e)
                }, 
                "di_container"
            ))
            
            return None
    
    def _publish_lifecycle_event(self, registration: ComponentRegistration, lifecycle: ComponentLifecycle) -> None:
        """
        Publish component lifecycle event
        
        Args:
            registration: Component registration
            lifecycle: Lifecycle event
        """
        publish(Event(
            EventType.COMPONENT_INITIALIZED if lifecycle == ComponentLifecycle.INITIALIZED else EventType.COMPONENT_ERROR,
            {
                "component": registration.implementation_type.__name__,
                "lifecycle": lifecycle.value
            },
            "di_container"
        ))
    
    def _handle_system_shutdown(self, event: Event) -> None:
        """
        Handle system shutdown event
        
        Args:
            event: System shutdown event
        """
        logger.info("Shutting down components...")
        
        # Dispose components in reverse registration order
        for interface_type, registration in reversed(list(self._registrations.items())):
            if registration.initialized and interface_type in self._instances:
                instance = self._instances[interface_type]
                
                # Publish lifecycle event
                self._publish_lifecycle_event(registration, ComponentLifecycle.DISPOSING)
                
                # Call dispose method if available
                if hasattr(instance, "dispose") and callable(getattr(instance, "dispose")):
                    try:
                        instance.dispose()
                    except Exception as e:
                        logger.error(f"Error disposing {registration.implementation_type.__name__}: {str(e)}")
                
                # Publish lifecycle event
                self._publish_lifecycle_event(registration, ComponentLifecycle.DISPOSED)
        
        # Clear instances
        self._instances.clear()

# Convenience functions for working with the DI container
def register(interface_type: Type[T], 
            implementation_type: Type,
            factory: Optional[Callable[..., T]] = None,
            scope: ComponentScope = ComponentScope.SINGLETON,
            dependencies: Optional[List[Type]] = None,
            tags: Optional[Set[str]] = None) -> None:
    """
    Register a component
    
    Args:
        interface_type: Interface type
        implementation_type: Implementation type
        factory: Optional factory function
        scope: Component lifecycle scope
        dependencies: List of dependency types
        tags: Optional tags for component categorization
    """
    DIContainer().register(interface_type, implementation_type, factory, scope, dependencies, tags)

def register_instance(interface_type: Type[T], instance: T, tags: Optional[Set[str]] = None) -> None:
    """
    Register an existing instance
    
    Args:
        interface_type: Interface type
        instance: Component instance
        tags: Optional tags for component categorization
    """
    DIContainer().register_instance(interface_type, instance, tags)

def resolve(interface_type: Type[T]) -> Optional[T]:
    """
    Resolve a component by interface type
    
    Args:
        interface_type: Interface type
        
    Returns:
        Component instance or None if not registered
    """
    return DIContainer().resolve(interface_type)

def resolve_all(interface_type: Type[T]) -> List[T]:
    """
    Resolve all components implementing an interface
    
    Args:
        interface_type: Interface type
        
    Returns:
        List of component instances
    """
    return DIContainer().resolve_all(interface_type)

def resolve_by_tag(tag: str) -> List[Any]:
    """
    Resolve components by tag
    
    Args:
        tag: Component tag
        
    Returns:
        List of component instances
    """
    return DIContainer().resolve_by_tag(tag)