"""
Service Locator Module
Provides a service locator pattern for component discovery and communication
"""

from typing import Dict, Any, Type, TypeVar, Optional, List, Set, Callable
import logging
import threading
from enum import Enum

from .di_container import resolve, resolve_all, register, register_instance
from .events import EventType, Event, publish, subscribe

logger = logging.getLogger(__name__)

# Generic type for service interfaces
T = TypeVar('T')

class ServiceScope(Enum):
    """Service scope constants"""
    GLOBAL = "global"      # Available to all components
    RESTRICTED = "restricted"  # Available only to authorized components
    INTERNAL = "internal"  # Available only to internal components

class ServiceCategory(Enum):
    """Service category constants"""
    CORE = "core"          # Core system services
    INDEXING = "indexing"  # Indexing services
    SEARCH = "search"      # Search services
    ANALYSIS = "analysis"  # Code analysis services
    CONTEXT = "context"    # Context management services
    FORMATTING = "formatting"  # Formatting services
    AGENT = "agent"        # Agent services
    UTILITY = "utility"    # Utility services

class ServiceDescriptor:
    """Service descriptor for service registration"""
    
    def __init__(self, 
                 service_id: str,
                 service_type: Type,
                 implementation_type: Optional[Type] = None,
                 instance: Optional[Any] = None,
                 scope: ServiceScope = ServiceScope.GLOBAL,
                 category: ServiceCategory = ServiceCategory.UTILITY,
                 tags: Optional[Set[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize service descriptor
        
        Args:
            service_id: Service ID
            service_type: Service interface type
            implementation_type: Optional implementation type
            instance: Optional service instance
            scope: Service scope
            category: Service category
            tags: Optional tags for service categorization
            metadata: Optional metadata
        """
        self.service_id = service_id
        self.service_type = service_type
        self.implementation_type = implementation_type
        self.instance = instance
        self.scope = scope
        self.category = category
        self.tags = tags or set()
        self.metadata = metadata or {}
        self.initialized = instance is not None

class ServiceLocator:
    """Service locator for component discovery and communication"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern implementation"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ServiceLocator, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the service locator"""
        if self._initialized:
            return
            
        self._services: Dict[str, ServiceDescriptor] = {}
        self._type_map: Dict[Type, str] = {}
        self._initialized = True
        logger.info("Service locator initialized")
    
    def register_service(self, descriptor: ServiceDescriptor) -> None:
        """
        Register a service
        
        Args:
            descriptor: Service descriptor
        """
        self._services[descriptor.service_id] = descriptor
        self._type_map[descriptor.service_type] = descriptor.service_id
        
        # Register with DI container if instance is provided
        if descriptor.instance is not None:
            register_instance(descriptor.service_type, descriptor.instance, descriptor.tags)
        elif descriptor.implementation_type is not None:
            register(descriptor.service_type, descriptor.implementation_type, tags=descriptor.tags)
        
        logger.debug(f"Registered service {descriptor.service_id} of type {descriptor.service_type.__name__}")
        
        # Publish service registered event
        publish(Event(
            EventType.COMPONENT_INITIALIZED,  # Reusing existing event type
            {
                "service_id": descriptor.service_id,
                "service_type": descriptor.service_type.__name__,
                "scope": descriptor.scope.value,
                "category": descriptor.category.value
            },
            "service_locator"
        ))
    
    def get_service(self, service_id: str) -> Optional[Any]:
        """
        Get a service by ID
        
        Args:
            service_id: Service ID
            
        Returns:
            Service instance or None if not found
        """
        if service_id not in self._services:
            logger.warning(f"Service {service_id} not found")
            return None
        
        descriptor = self._services[service_id]
        
        # Return instance if already created
        if descriptor.instance is not None:
            return descriptor.instance
        
        # Resolve from DI container
        instance = resolve(descriptor.service_type)
        
        # Cache instance
        if instance is not None:
            descriptor.instance = instance
            descriptor.initialized = True
        
        return instance
    
    def get_service_by_type(self, service_type: Type[T]) -> Optional[T]:
        """
        Get a service by type
        
        Args:
            service_type: Service type
            
        Returns:
            Service instance or None if not found
        """
        if service_type not in self._type_map:
            logger.warning(f"Service of type {service_type.__name__} not found")
            return None
        
        service_id = self._type_map[service_type]
        return self.get_service(service_id)
    
    def get_services_by_category(self, category: ServiceCategory) -> List[Any]:
        """
        Get services by category
        
        Args:
            category: Service category
            
        Returns:
            List of service instances
        """
        services = []
        
        for descriptor in self._services.values():
            if descriptor.category == category:
                service = self.get_service(descriptor.service_id)
                if service is not None:
                    services.append(service)
        
        return services
    
    def get_services_by_tag(self, tag: str) -> List[Any]:
        """
        Get services by tag
        
        Args:
            tag: Service tag
            
        Returns:
            List of service instances
        """
        services = []
        
        for descriptor in self._services.values():
            if tag in descriptor.tags:
                service = self.get_service(descriptor.service_id)
                if service is not None:
                    services.append(service)
        
        return services
    
    def get_service_descriptor(self, service_id: str) -> Optional[ServiceDescriptor]:
        """
        Get a service descriptor by ID
        
        Args:
            service_id: Service ID
            
        Returns:
            Service descriptor or None if not found
        """
        return self._services.get(service_id)
    
    def get_service_descriptors_by_category(self, category: ServiceCategory) -> List[ServiceDescriptor]:
        """
        Get service descriptors by category
        
        Args:
            category: Service category
            
        Returns:
            List of service descriptors
        """
        return [descriptor for descriptor in self._services.values() if descriptor.category == category]
    
    def get_service_descriptors_by_tag(self, tag: str) -> List[ServiceDescriptor]:
        """
        Get service descriptors by tag
        
        Args:
            tag: Service tag
            
        Returns:
            List of service descriptors
        """
        return [descriptor for descriptor in self._services.values() if tag in descriptor.tags]
    
    def get_all_service_descriptors(self) -> List[ServiceDescriptor]:
        """
        Get all service descriptors
        
        Returns:
            List of all service descriptors
        """
        return list(self._services.values())

# Convenience functions for working with the service locator
def register_service(service_id: str,
                    service_type: Type,
                    implementation_type: Optional[Type] = None,
                    instance: Optional[Any] = None,
                    scope: ServiceScope = ServiceScope.GLOBAL,
                    category: ServiceCategory = ServiceCategory.UTILITY,
                    tags: Optional[Set[str]] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Register a service
    
    Args:
        service_id: Service ID
        service_type: Service interface type
        implementation_type: Optional implementation type
        instance: Optional service instance
        scope: Service scope
        category: Service category
        tags: Optional tags for service categorization
        metadata: Optional metadata
    """
    descriptor = ServiceDescriptor(
        service_id=service_id,
        service_type=service_type,
        implementation_type=implementation_type,
        instance=instance,
        scope=scope,
        category=category,
        tags=tags,
        metadata=metadata
    )
    
    ServiceLocator().register_service(descriptor)

def get_service(service_id: str) -> Optional[Any]:
    """
    Get a service by ID
    
    Args:
        service_id: Service ID
        
    Returns:
        Service instance or None if not found
    """
    return ServiceLocator().get_service(service_id)

def get_service_by_type(service_type: Type[T]) -> Optional[T]:
    """
    Get a service by type
    
    Args:
        service_type: Service type
        
    Returns:
        Service instance or None if not found
    """
    return ServiceLocator().get_service_by_type(service_type)

def get_services_by_category(category: ServiceCategory) -> List[Any]:
    """
    Get services by category
    
    Args:
        category: Service category
        
    Returns:
        List of service instances
    """
    return ServiceLocator().get_services_by_category(category)

def get_services_by_tag(tag: str) -> List[Any]:
    """
    Get services by tag
    
    Args:
        tag: Service tag
        
    Returns:
        List of service instances
    """
    return ServiceLocator().get_services_by_tag(tag)

def get_service_descriptor(service_id: str) -> Optional[ServiceDescriptor]:
    """
    Get a service descriptor by ID
    
    Args:
        service_id: Service ID
        
    Returns:
        Service descriptor or None if not found
    """
    return ServiceLocator().get_service_descriptor(service_id)

def get_service_descriptors_by_category(category: ServiceCategory) -> List[ServiceDescriptor]:
    """
    Get service descriptors by category
    
    Args:
        category: Service category
        
    Returns:
        List of service descriptors
    """
    return ServiceLocator().get_service_descriptors_by_category(category)

def get_service_descriptors_by_tag(tag: str) -> List[ServiceDescriptor]:
    """
    Get service descriptors by tag
    
    Args:
        tag: Service tag
        
    Returns:
        List of service descriptors
    """
    return ServiceLocator().get_service_descriptors_by_tag(tag)

def get_all_service_descriptors() -> List[ServiceDescriptor]:
    """
    Get all service descriptors
    
    Returns:
        List of all service descriptors
    """
    return ServiceLocator().get_all_service_descriptors()