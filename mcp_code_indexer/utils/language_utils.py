"""
Language utilities module
Provides common functions for language detection and file extension handling
"""

from typing import Dict, Optional, Set

# Centralized mapping of file extensions to programming languages
EXTENSION_TO_LANGUAGE: Dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".rs": "rust",
    ".sh": "bash",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sql": "sql",
    ".md": "markdown",
    ".json": "json",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".vue": "vue"
}

# Language-specific comment markers
SINGLE_LINE_COMMENT_MARKERS: Dict[str, list] = {
    'python': ['#'],
    'javascript': ['//'],
    'typescript': ['//'],
    'java': ['//'],
    'c': ['//'],
    'cpp': ['//'],
    'csharp': ['//'],
    'php': ['//'],
    'ruby': ['#'],
    'go': ['//'],
    'rust': ['//'],
    'swift': ['//'],
    'kotlin': ['//', '#']
}

def get_language_from_extension(file_path: str) -> str:
    """
    Determine the programming language based on file extension
    
    Args:
        file_path: Path to the file
        
    Returns:
        Language identifier string, defaults to "text" if unknown
    """
    import os
    _, ext = os.path.splitext(file_path.lower())
    return EXTENSION_TO_LANGUAGE.get(ext, "text")

def get_comment_markers(language: str) -> list:
    """
    Get single-line comment markers for a specific language
    
    Args:
        language: Programming language identifier
        
    Returns:
        List of comment marker strings
    """
    return SINGLE_LINE_COMMENT_MARKERS.get(language, ['#', '//'])

def get_supported_languages() -> Set[str]:
    """
    Get the set of all supported programming languages
    
    Returns:
        Set of language identifier strings
    """
    return set(EXTENSION_TO_LANGUAGE.values())

def get_supported_extensions() -> Set[str]:
    """
    Get the set of all supported file extensions
    
    Returns:
        Set of file extension strings
    """
    return set(EXTENSION_TO_LANGUAGE.keys())