# MCP-Index Static Analysis and Improvement Plan

## System Overview

The MCP-Index project is a sophisticated code indexing and retrieval system designed to provide relevant code context to language models. It uses vector embeddings and semantic search to enable context-aware code retrieval.

### Core Components

1. **CodeIndexer** (indexer.py)
   - Scans and indexes code repositories
   - Generates vector embeddings using sentence transformers
   - Manages incremental indexing and updates
   - Stores code chunks in ChromaDB vector database

2. **SearchEngine** (search_engine.py)
   - Provides semantic code search capabilities
   - Supports various search methods (similarity, context-aware, natural language)
   - Implements sophisticated code similarity algorithms
   - Integrates with LLM processors for enhanced results

3. **CodeAnalyzer** (code_analyzer.py)
   - Uses tree-sitter to parse and analyze code structure
   - Extracts functions, classes, imports, and dependencies
   - Builds code structure trees for navigation
   - Supports multiple programming languages

4. **ContextManager** (context_manager.py)
   - Manages code context with caching and compression
   - Prioritizes context based on relevance
   - Optimizes memory usage with eviction strategies
   - Provides efficient context retrieval

5. **AgentManager** (agent_manager.py)
   - Coordinates multiple specialized agents
   - Implements a multi-agent system for code analysis
   - Uses an environment for agent communication
   - Provides high-level analysis capabilities

6. **Factory** (factory.py)
   - Creates and initializes components
   - Manages component dependencies
   - Provides a clean interface for system setup

## Current Data Flow Analysis

The current data flow in the system follows these general patterns:

1. **Indexing Flow**:
   ```
   Project Files → CodeIndexer → Code Chunks → Vector Embeddings → ChromaDB
   ```

2. **Search Flow**:
   ```
   Query → SearchEngine → Vector Embedding → ChromaDB Search → Ranked Results
   ```

3. **Context Retrieval Flow**:
   ```
   File/Line → ContextManager → Cache Check → Context Extraction → Optimized Context
   ```

4. **Agent Analysis Flow**:
   ```
   Analysis Request → AgentManager → Specialized Agents → Environment → Aggregated Results
   ```

## Component Interconnection Analysis

### Strengths

1. **Modular Design**: The system has a well-defined separation of concerns with specialized components.
2. **Factory Pattern**: The factory.py module provides clean component initialization and dependency injection.
3. **Caching Mechanisms**: The ContextManager implements efficient caching for improved performance.
4. **Multi-Agent Architecture**: The AgentManager enables parallel processing of different analysis tasks.

### Weaknesses

1. **Limited Integration Between Context and Search**: The ContextManager and SearchEngine operate somewhat independently.
2. **No Direct Connection Between Analyzer and Context**: The CodeAnalyzer results aren't directly used by the ContextManager.
3. **Manual Component Wiring**: Components must be explicitly connected through the Factory.
4. **Limited Feedback Loop**: Search results don't inform the context prioritization.

## Improvement Plan for RelevantCodeContextRetriever

To enhance the system's functionality as a RelevantCodeContextRetriever, we propose the following improvements:

### 1. Context-Aware Search Integration

Create a new `ContextAwareSearchEngine` class that combines the capabilities of the SearchEngine and ContextManager:

```python
class ContextAwareSearchEngine:
    """
    Enhanced search engine that integrates context awareness
    """
    
    def __init__(self, search_engine: SearchEngine, context_manager: ContextManager):
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
        """Calculate relevance between content and current context"""
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
```

### 2. Analyzer-Informed Context Management

Enhance the ContextManager to use CodeAnalyzer results for better context extraction:

```python
# Add to ContextManager class
def get_enhanced_context(self, file_path: str, line_number: int,
                        analyzer: CodeAnalyzer) -> Optional[str]:
    """
    Get enhanced context using code analyzer
    
    Args:
        file_path: File path
        line_number: Line number
        analyzer: Code analyzer instance
        
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
        analysis = analyzer.get_code_structure(content, language)
        
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
        return self.get_context(file_path, line_number)
        
    except Exception as e:
        logger.error(f"Error getting enhanced context: {str(e)}")
        return self.get_context(file_path, line_number)
```

### 3. Feedback-Driven Context Prioritization

Implement a feedback mechanism to improve context prioritization based on search results:

```python
# Add to ContextManager class
def update_context_priority(self, file_path: str, start_line: int, end_line: int,
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
    if key in self.cache.items:
        item = self.cache.items[key]
        
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
```

### 4. Integrated RelevantCodeContextRetriever

Create a new class that serves as the main entry point for relevant code context retrieval:

```python
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
                enhanced_context = self.context_manager.get_enhanced_context(
                    file_path, (start_line + end_line) // 2, self.code_analyzer
                )
                
                if enhanced_context:
                    result['enhanced_context'] = enhanced_context
                    
                # Update context priority based on search result
                self.context_manager.update_context_priority(
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
    
    def index_project(self, project_path: str, 
                     progress_callback: Optional[Callable] = None) -> str:
        """
        Index a project
        
        Args:
            project_path: Project path
            progress_callback: Progress callback
            
        Returns:
            Project ID
        """
        return self.indexer.index_project(project_path, progress_callback)
```

### 5. Factory Integration

Update the factory.py module to support the new integrated components:

```python
# Add to factory.py
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
```

## Implementation Plan

1. **Phase 1: Component Enhancement**
   - Implement the ContextAwareSearchEngine class
   - Add enhanced context methods to ContextManager
   - Implement feedback-driven context prioritization

2. **Phase 2: Integration**
   - Create the RelevantCodeContextRetriever class
   - Update the factory.py module
   - Ensure backward compatibility

3. **Phase 3: Testing and Optimization**
   - Test with various codebases
   - Optimize performance bottlenecks
   - Fine-tune relevance algorithms

## Expected Benefits

1. **Improved Context Relevance**: By combining search and context capabilities, the system will provide more relevant code context.

2. **Smarter Context Prioritization**: The feedback mechanism will continuously improve context prioritization based on usage.

3. **Enhanced Code Understanding**: The integration with CodeAnalyzer will provide richer context with structural information.

4. **Unified Interface**: The RelevantCodeContextRetriever provides a clean, high-level interface for the entire system.

5. **Better Agent Integration**: The improved system will make better use of the multi-agent capabilities for enhanced insights.

## Conclusion

The proposed improvements will transform the MCP-Index system into a more effective RelevantCodeContextRetriever by better interconnecting its components and implementing feedback-driven context prioritization. The enhanced system will provide more relevant code context to language models, improving their understanding and generation capabilities for code-related tasks.