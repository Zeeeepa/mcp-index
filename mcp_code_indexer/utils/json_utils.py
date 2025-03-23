"""
JSON Utilities Module

Provides utility functions for working with JSON data and serialization.
"""

from typing import Any, Dict, List, Set, Union


def convert_sets_to_lists(obj: Any) -> Any:
    """
    Recursively convert sets to lists in a nested data structure for JSON serialization.
    
    Args:
        obj: The object to convert, which may contain sets, lists, dictionaries, or other types
        
    Returns:
        The converted object with all sets replaced by lists
    
    Examples:
        >>> convert_sets_to_lists({'a': {1, 2, 3}, 'b': [4, 5, {6, 7}]})
        {'a': [1, 2, 3], 'b': [4, 5, [6, 7]]}
    """
    if isinstance(obj, dict):
        return {k: convert_sets_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, list):
        return [convert_sets_to_lists(item) for item in obj]
    else:
        return obj


def safe_json_serialize(obj: Any) -> Dict[str, Any]:
    """
    Safely serialize an object to a JSON-compatible dictionary.
    
    Args:
        obj: The object to serialize
        
    Returns:
        A JSON-compatible dictionary
    """
    return convert_sets_to_lists(obj)