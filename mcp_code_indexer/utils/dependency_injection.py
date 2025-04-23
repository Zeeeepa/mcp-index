"""
Dependency injection module.

This module provides a simple dependency injection system for the codebase,
allowing for better testability and flexibility.
"""

import inspect
from typing import Dict, Any, Type, TypeVar, Generic, Optional, Callable, List, Set

T = TypeVar('T')

class DependencyContainer:
    """
    A simple dependency container for managing dependencies.
    """
    
    def __init__(self):
        """Initialize the dependency container."""
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[..., Any]] = {}
        
    def register(self, name: str, instance: Any) -> None:
        """
        Register an instance with the container.
        
        Args:
            name: The name to register the instance under
            instance: The instance to register
        """
        self._instances[name] = instance
        
    def register_factory(self, name: str, factory: Callable[..., Any]) -> None:
        """
        Register a factory function with the container.
        
        Args:
            name: The name to register the factory under
            factory: The factory function to register
        """
        self._factories[name] = factory
        
    def get(self, name: str, *args, **kwargs) -> Any:
        """
        Get an instance from the container.
        
        Args:
            name: The name of the instance to get
            *args: Positional arguments to pass to the factory function
            **kwargs: Keyword arguments to pass to the factory function
            
        Returns:
            The instance
            
        Raises:
            KeyError: If the instance is not registered
        """
        if name in self._instances:
            return self._instances[name]
        
        if name in self._factories:
            instance = self._factories[name](*args, **kwargs)
            self._instances[name] = instance
            return instance
        
        raise KeyError(f"No dependency registered for '{name}'")
        
    def has(self, name: str) -> bool:
        """
        Check if an instance is registered with the container.
        
        Args:
            name: The name to check
            
        Returns:
            True if the instance is registered, False otherwise
        """
        return name in self._instances or name in self._factories
        
    def clear(self) -> None:
        """Clear all registered instances and factories."""
        self._instances.clear()
        self._factories.clear()


# Global dependency container
_container = DependencyContainer()

def get_container() -> DependencyContainer:
    """
    Get the global dependency container.
    
    Returns:
        The global dependency container
    """
    return _container

def register(name: str, instance: Any) -> None:
    """
    Register an instance with the global container.
    
    Args:
        name: The name to register the instance under
        instance: The instance to register
    """
    _container.register(name, instance)
    
def register_factory(name: str, factory: Callable[..., Any]) -> None:
    """
    Register a factory function with the global container.
    
    Args:
        name: The name to register the factory under
        factory: The factory function to register
    """
    _container.register_factory(name, factory)
    
def get(name: str, *args, **kwargs) -> Any:
    """
    Get an instance from the global container.
    
    Args:
        name: The name of the instance to get
        *args: Positional arguments to pass to the factory function
        **kwargs: Keyword arguments to pass to the factory function
        
    Returns:
        The instance
        
    Raises:
        KeyError: If the instance is not registered
    """
    return _container.get(name, *args, **kwargs)
    
def has(name: str) -> bool:
    """
    Check if an instance is registered with the global container.
    
    Args:
        name: The name to check
        
    Returns:
        True if the instance is registered, False otherwise
    """
    return _container.has(name)
    
def clear() -> None:
    """Clear all registered instances and factories in the global container."""
    _container.clear()


class Inject:
    """
    Decorator for injecting dependencies into a function or method.
    
    Example:
        @Inject('config', 'logger')
        def my_function(config, logger, other_arg):
            # Use config and logger
            pass
    """
    
    def __init__(self, *dependencies: str):
        """
        Initialize the decorator.
        
        Args:
            *dependencies: The names of the dependencies to inject
        """
        self.dependencies = dependencies
        
    def __call__(self, func: Callable) -> Callable:
        """
        Decorate the function.
        
        Args:
            func: The function to decorate
            
        Returns:
            The decorated function
        """
        def wrapper(*args, **kwargs):
            # Get the function signature
            sig = inspect.signature(func)
            
            # Inject dependencies
            for dep_name in self.dependencies:
                if dep_name in sig.parameters and dep_name not in kwargs:
                    kwargs[dep_name] = get(dep_name)
                    
            return func(*args, **kwargs)
            
        return wrapper


class Injectable:
    """
    Decorator for making a class injectable.
    
    Example:
        @Injectable('my_service')
        class MyService:
            def __init__(self, config, logger):
                self.config = config
                self.logger = logger
    """
    
    def __init__(self, name: str, *dependencies: str):
        """
        Initialize the decorator.
        
        Args:
            name: The name to register the class under
            *dependencies: The names of the dependencies to inject
        """
        self.name = name
        self.dependencies = dependencies
        
    def __call__(self, cls: Type[T]) -> Type[T]:
        """
        Decorate the class.
        
        Args:
            cls: The class to decorate
            
        Returns:
            The decorated class
        """
        # Create a factory function for the class
        def factory():
            # Get dependencies
            deps = {dep_name: get(dep_name) for dep_name in self.dependencies}
            
            # Create an instance of the class with the dependencies
            return cls(**deps)
            
        # Register the factory
        register_factory(self.name, factory)
        
        return cls