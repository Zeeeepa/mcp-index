"""
Event system module
Provides a simple event system for asynchronous component communication
"""

from typing import Dict, List, Any, Callable, Optional
import logging
import threading
import time
from enum import Enum

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Event types for system-wide events"""
    # Indexing events
    INDEXING_STARTED = "indexing_started"
    INDEXING_PROGRESS = "indexing_progress"
    INDEXING_COMPLETED = "indexing_completed"
    INDEXING_FAILED = "indexing_failed"
    
    # Search events
    SEARCH_STARTED = "search_started"
    SEARCH_COMPLETED = "search_completed"
    SEARCH_FAILED = "search_failed"
    
    # System events
    SYSTEM_READY = "system_ready"
    SYSTEM_ERROR = "system_error"
    SYSTEM_SHUTDOWN = "system_shutdown"
    
    # Component events
    COMPONENT_INITIALIZED = "component_initialized"
    COMPONENT_ERROR = "component_error"

class Event:
    """Event class for the event system"""
    
    def __init__(self, event_type: EventType, data: Dict[str, Any] = None, source: str = None):
        """
        Initialize an event
        
        Args:
            event_type: Type of the event
            data: Event data
            source: Source component of the event
        """
        self.event_type = event_type
        self.data = data or {}
        self.source = source
        self.timestamp = time.time()
    
    def __str__(self) -> str:
        """String representation of the event"""
        return f"Event({self.event_type.value}, source={self.source}, data={self.data})"

class EventBus:
    """Event bus for publishing and subscribing to events"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern implementation"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the event bus"""
        if self._initialized:
            return
            
        self._subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._initialized = True
        logger.info("Event bus initialized")
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to an event type
        
        Args:
            event_type: Type of event to subscribe to
            callback: Callback function to be called when the event occurs
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            logger.debug(f"Subscribed to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Unsubscribe from an event type
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Callback function to remove
        """
        if event_type in self._subscribers and callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
            logger.debug(f"Unsubscribed from {event_type.value}")
    
    def publish(self, event: Event) -> None:
        """
        Publish an event
        
        Args:
            event: Event to publish
        """
        if event.event_type not in self._subscribers:
            return
            
        for callback in self._subscribers[event.event_type]:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {str(e)}")
        
        logger.debug(f"Published event: {event}")
    
    def publish_async(self, event: Event) -> None:
        """
        Publish an event asynchronously
        
        Args:
            event: Event to publish
        """
        threading.Thread(target=self.publish, args=(event,), daemon=True).start()

# Convenience functions for working with the event bus
def subscribe(event_type: EventType, callback: Callable[[Event], None]) -> None:
    """
    Subscribe to an event type
    
    Args:
        event_type: Type of event to subscribe to
        callback: Callback function to be called when the event occurs
    """
    EventBus().subscribe(event_type, callback)

def unsubscribe(event_type: EventType, callback: Callable[[Event], None]) -> None:
    """
    Unsubscribe from an event type
    
    Args:
        event_type: Type of event to unsubscribe from
        callback: Callback function to remove
    """
    EventBus().unsubscribe(event_type, callback)

def publish(event: Event) -> None:
    """
    Publish an event
    
    Args:
        event: Event to publish
    """
    EventBus().publish(event)

def publish_async(event: Event) -> None:
    """
    Publish an event asynchronously
    
    Args:
        event: Event to publish
    """
    EventBus().publish_async(event)