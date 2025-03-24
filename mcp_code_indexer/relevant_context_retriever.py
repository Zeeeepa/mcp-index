"""
Relevant Code Context Retriever Module
Provides integrated code context retrieval with enhanced relevance
"""

import os
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
import time

from .config import Config
from .indexer import CodeIndexer
from .search_engine import SearchEngine
from .context_manager import ContextManager, ContextType, ContextPriority
from .code_analyzer import CodeAnalyzer
from .agent_manager import AgentManager

logger = logging.getLogger(__name__)

class ContextAwareSearchEngine:
    """
    Enhanced search engine that integrates context awareness
    """
    
    def __init__(self, search_engine: SearchEngine, context_manager: ContextManager):
        """
        Initialize context-aware search engine
        
        Args:
            search_engine: Search engine instance
            context_manager: Context manager instance
            
        Returns:
            None
        """
        self.search_engine = search_engine
        self.context_manager = context_manager
    
    def search_with_context(self, query: str, context_file: str = None, 
                           context_line: int = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search with context awareness
        
        Args:
            query: Search query
            context_file: Current file for context
            context_line: Current line for context
            limit: Result limit
            
        Returns:
            Enhanced search results with context
        """
        # Get base search results
        results = self.search_engine.search(query, limit=limit*2)
        
        # If context is provided, enhance results
        if context_file and context_line:
            # Get current context
            current_context = self.context_manager.get_context(
                context_file, context_line, ContextType.FUNCTION
            )
            
            # Re-rank results based on context relevance
            if current_context:
                for result in results:
                    # Calculate context similarity
                    result['context_relevance'] = self._calculate_context_relevance(
                        result.get('content', ''), current_context
                    )
                
                # Sort by combined relevance
                results.sort(key=lambda x: (
                    x.get('similarity', 0) * 0.7 + 
                    x.get('context_relevance', 0) * 0.3
                ), reverse=True)
        
        return results[:limit]
    
    def _calculate_context_relevance(self, content: str, context: str) -> float:
        """
        Calculate relevance between content and current context
        
        Args:
            content: Content to compare
            context: Current context
            
        Returns:
            Relevance score (0-1)
        """
        # Implement context similarity calculation
        # This could use simple overlap or more sophisticated embedding similarity
        # For now, a simple implementation:
        content_tokens = set(content.split())
        context_tokens = set(context.split())
        
        if not content_tokens or not context_tokens:
            return 0.0
            
        intersection = len(content_tokens.intersection(context_tokens))
        union = len(content_tokens.union(context_tokens))
        
        return intersection / union if union > 0 else 0.0


class RelevantCodeContextRetriever:
    """
    Integrated system for retrieving relevant code context
    """
    
    def __init__(self, config: Config):
        """
        Initialize the retriever
        
        Args:
            config: Configuration object
        """
        # Create components
        self.config = config
        self.indexer = CodeIndexer(config)
        self.search_engine = SearchEngine(config, self.indexer)
        self.context_manager = ContextManager()
        self.code_analyzer = CodeAnalyzer()
        
        # Create enhanced components
        self.context_aware_search = ContextAwareSearchEngine(
            self.search_engine, self.context_manager
        )
        
        # Initialize agent manager if enabled
        if config.get("agents.enabled", False):
            self.agent_manager = AgentManager(
                config, self.indexer, self.search_engine
            )
        else:
            self.agent_manager = None
            
        logger.info("RelevantCodeContextRetriever initialized")
    
    def get_relevant_context(self, query: str, current_file: str = None, 
                            current_line: int = None, limit: int = 5) -> Dict[str, Any]:
        """
        Get relevant code context based on query and current position
        
        Args:
            query: Search query
            current_file: Current file (optional)
            current_line: Current line (optional)
            limit: Result limit
            
        Returns:
            Relevant code context
        """
        # Get context-aware search results
        search_results = self.context_aware_search.search_with_context(
            query, current_file, current_line, limit
        )
        
        # Extract enhanced context for each result
        enhanced_results = []
        for result in search_results:
            file_path = result.get('file_path')
            start_line = result.get('start_line')
            end_line = result.get('end_line')
            
            if file_path and start_line and end_line:
                # Get enhanced context
                enhanced_context = self._get_enhanced_context(
                    file_path, (start_line + end_line) // 2
                )
                
                if enhanced_context:
                    result['enhanced_context'] = enhanced_context
                    
                # Update context priority based on search result
                self._update_context_priority(
                    file_path, start_line, end_line, -1
                )
            
            enhanced_results.append(result)
        
        # If agent manager is available, get additional insights
        agent_insights = {}
        if self.agent_manager and current_file:
            agent_insights = self.agent_manager.analyze_code(current_file)
        
        return {
            'query': query,
            'current_context': {
                'file': current_file,
                'line': current_line
            } if current_file and current_line else None,
            'results': enhanced_results,
            'agent_insights': agent_insights
        }
    
    def _get_enhanced_context(self, file_path: str, line_number: int) -> Optional[Dict[str, Any]]:
        """
        Get enhanced context using code analyzer
        
        Args:
            file_path: File path
            line_number: Line number
            
        Returns:
            Enhanced context
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Get language
            ext = os.path.splitext(file_path)[1].lower()
            language = self._get_language(ext)
            
            # Analyze code structure
            analysis = self.code_analyzer.get_code_structure(content, language)
            
            # Find the most relevant structure containing the line
            context_block = None
            
            # Check functions
            for func in analysis['functions']:
                if func['start_line'] <= line_number <= func['end_line']:
                    # Extract function content
                    lines = content.split('\n')
                    func_content = '\n'.join(lines[func['start_line']-1:func['end_line']])
                    
                    # Get dependencies
                    dependencies = []
                    for dep in analysis['dependencies']:
                        if dep in func_content:
                            dependencies.append(dep)
                    
                    return {
                        'content': func_content,
                        'type': 'function',
                        'name': func['name'],
                        'dependencies': dependencies
                    }
            
            # Check classes if no function found
            for cls in analysis['classes']:
                if cls['start_line'] <= line_number <= cls['end_line']:
                    # Extract class content
                    lines = content.split('\n')
                    class_content = '\n'.join(lines[cls['start_line']-1:cls['end_line']])
                    
                    return {
                        'content': class_content,
                        'type': 'class',
                        'name': cls['name']
                    }
            
            # Fall back to regular context
            context = self.context_manager.get_context(file_path, line_number)
            if context:
                return {
                    'content': context,
                    'type': 'generic'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting enhanced context: {str(e)}")
            return None
    
    def _update_context_priority(self, file_path: str, start_line: int, end_line: int,
                               priority_change: int = -1):
        """
        Update context priority based on usage feedback
        
        Args:
            file_path: File path
            start_line: Start line
            end_line: End line
            priority_change: Priority change (-1 means higher priority)
            
        Returns:
            None
        """
        key = f"{file_path}:{start_line}-{end_line}"
        
        # Check if context exists in cache
        if hasattr(self.context_manager, 'cache') and hasattr(self.context_manager.cache, 'items'):
            if key in self.context_manager.cache.items:
                item = self.context_manager.cache.items[key]
                
                # Update priority (ensure it stays within enum bounds)
                current_value = item.priority.value
                new_value = max(ContextPriority.CRITICAL.value, 
                                min(ContextPriority.BACKGROUND.value, 
                                    current_value + priority_change))
                
                # Set new priority
                for priority in ContextPriority:
                    if priority.value == new_value:
                        item.priority = priority
                        break
                        
                # Update access count and timestamp
                item.access_count += 1
                item.last_used = time.time()
    
    def _get_language(self, ext: str) -> str:
        """
        Get language from file extension
        
        Args:
            ext: File extension
            
        Returns:
            Language name
        """
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.vue': 'vue',
            '.php': 'php',
            '.rs': 'rust',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.sh': 'bash',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sql': 'sql',
            '.md': 'markdown',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml'
        }
        return language_map.get(ext, 'text')
    
    def index_project(self, project_path: str, 
                     progress_callback: Optional[Callable[[str, float], None]] = None) -> str:
        """
        Index a project
        
        Args:
            project_path: Project path
            progress_callback: Progress callback
            
        Returns:
            Project ID
        """
        return self.indexer.index_project(project_path, progress_callback)
    
    def get_indexing_status(self, project_id: str) -> Tuple[str, float]:
        """
        Get indexing status
        
        Args:
            project_id: Project ID
            
        Returns:
            Tuple of (status, progress)
        """
        return self.indexer.get_indexing_status(project_id)
    
    def search(self, query: str, project_ids: Optional[List[str]] = None, 
              filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search code (direct access to search engine)
        
        Args:
            query: Search query
            project_ids: Project IDs
            filters: Filters
            limit: Result limit
            
        Returns:
            Search results
        """
        return self.search_engine.search(query, project_ids, filters, limit)
    
    def natural_language_search(self, query: str, project_ids: Optional[List[str]] = None,
                              filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> Dict[str, Any]:
        """
        Natural language search
        
        Args:
            query: Natural language query
            project_ids: Project IDs
            filters: Filters
            limit: Result limit
            
        Returns:
            Natural language search results
        """
        return self.search_engine.natural_language_search(query, project_ids, filters, limit)