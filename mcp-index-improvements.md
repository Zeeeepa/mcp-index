# MCP-Index: Improving Integration Options and Search Capabilities

This document outlines recommendations for enhancing the integration options and search capabilities of the mcp-index project, a sophisticated code indexing and retrieval system.

## Current System Overview

MCP-Index is a powerful code indexing system that uses vector embeddings to enable semantic code search. The system consists of several key components:

1. **CodeIndexer**: Manages the indexing process using sentence transformers
2. **CodeAnalyzer**: Uses tree-sitter to parse and analyze code structure
3. **SearchEngine**: Provides semantic code search capabilities
4. **ContextManager**: Handles code context with caching and compression

The system currently supports basic integration through direct API calls and offers several search capabilities including semantic search, function/class search, and similarity detection.

## Improved Integration Options

### 1. REST API Layer

**Current Limitation**: The system lacks a standardized API interface for external services to interact with.

**Recommendation**: Implement a RESTful API layer that exposes the core functionality:

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

from mcp_code_indexer.config import Config
from mcp_code_indexer.indexer import CodeIndexer
from mcp_code_indexer.search_engine import SearchEngine

app = FastAPI(title="MCP-Index API", description="Code indexing and search API")

# Models for request/response
class SearchRequest(BaseModel):
    query: str
    project_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10

class IndexProjectRequest(BaseModel):
    project_path: str
    force_reindex: bool = False

# Initialize components
config = Config()
indexer = CodeIndexer(config)
search_engine = SearchEngine(config, indexer)

# Endpoints
@app.post("/search", response_model=List[Dict[str, Any]])
async def search_code(request: SearchRequest):
    try:
        results = search_engine.search(
            query=request.query,
            project_ids=request.project_ids,
            filters=request.filters,
            limit=request.limit
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index", response_model=Dict[str, Any])
async def index_project(request: IndexProjectRequest):
    try:
        project_id = indexer.index_project(
            project_path=request.project_path,
            force_reindex=request.force_reindex
        )
        return {"project_id": project_id, "status": "indexing_started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the API server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. WebSocket Support for Real-time Updates

**Current Limitation**: No real-time feedback during indexing or search operations.

**Recommendation**: Add WebSocket support to provide real-time updates:

```python
from fastapi import WebSocket, WebSocketDisconnect

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# WebSocket endpoint for indexing progress
@app.websocket("/ws/indexing/{project_id}")
async def websocket_indexing_endpoint(websocket: WebSocket, project_id: str):
    await manager.connect(websocket)
    try:
        # Progress callback function
        async def progress_callback(status: str, progress: float):
            await manager.send_personal_message(
                json.dumps({"status": status, "progress": progress}),
                websocket
            )
        
        # Start indexing with progress updates
        indexer.index_project(
            project_path=project_path,
            progress_callback=progress_callback
        )
        
        # Keep connection open for updates
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### 3. Language Server Protocol (LSP) Integration

**Current Limitation**: No direct integration with code editors.

**Recommendation**: Implement a Language Server Protocol adapter to integrate with code editors like VS Code, Neovim, etc.:

```python
from pygls.server import LanguageServer
from pygls.lsp.methods import (
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_SAVE
)
from pygls.lsp.types import (
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
    DidSaveTextDocumentParams
)

# Initialize MCP-Index components
config = Config()
indexer = CodeIndexer(config)
search_engine = SearchEngine(config, indexer)

# Create LSP server
server = LanguageServer('mcp-index-server', 'v0.1')

@server.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls, params: DidOpenTextDocumentParams):
    """Index the file when opened"""
    document = ls.workspace.get_document(params.text_document.uri)
    # Process the document...

@server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(ls, params: DidSaveTextDocumentParams):
    """Re-index the file when saved"""
    document = ls.workspace.get_document(params.text_document.uri)
    # Update the index...

# Custom commands for search
@server.command('mcp.search')
def mcp_search(ls, *args):
    """Search code using MCP-Index"""
    query = args[0]
    results = search_engine.search(query=query)
    # Return results to the editor...
```

### 4. CI/CD Integration

**Current Limitation**: No automated integration with development workflows.

**Recommendation**: Create GitHub Actions and other CI/CD integrations:

```yaml
# .github/workflows/mcp-index.yml
name: MCP-Index Code Indexing

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  index:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install mcp-index
      
      - name: Index code
        run: |
          python -m mcp_code_indexer.cli index --path . --output ./mcp-index
      
      - name: Upload index
        uses: actions/upload-artifact@v2
        with:
          name: code-index
          path: ./mcp-index
```

### 5. Plugin System

**Current Limitation**: Limited extensibility for custom integrations.

**Recommendation**: Implement a plugin system to allow custom extensions:

```python
# mcp_code_indexer/plugin_manager.py
import importlib
import pkgutil
from typing import Dict, Any, List, Type

class PluginInterface:
    """Base interface for all plugins"""
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with configuration"""
        pass
    
    def on_index_start(self, project_id: str, project_path: str) -> None:
        """Called when indexing starts"""
        pass
    
    def on_index_complete(self, project_id: str, project_path: str) -> None:
        """Called when indexing completes"""
        pass
    
    def on_search(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Called during search, can modify results"""
        return results

class PluginManager:
    """Manages MCP-Index plugins"""
    
    def __init__(self, plugins_path: str = "mcp_plugins"):
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugins_path = plugins_path
        self._discover_plugins()
    
    def _discover_plugins(self) -> None:
        """Discover and load all plugins"""
        try:
            plugins_package = importlib.import_module(self.plugins_path)
            for _, name, is_pkg in pkgutil.iter_modules(plugins_package.__path__, f"{self.plugins_path}."):
                if is_pkg:
                    plugin_module = importlib.import_module(name)
                    for item_name in dir(plugin_module):
                        item = getattr(plugin_module, item_name)
                        if (isinstance(item, type) and 
                            issubclass(item, PluginInterface) and 
                            item is not PluginInterface):
                            plugin_instance = item()
                            self.plugins[name] = plugin_instance
        except ImportError:
            # No plugins package found
            pass
    
    def initialize_plugins(self, config: Dict[str, Any]) -> None:
        """Initialize all plugins with config"""
        for plugin in self.plugins.values():
            plugin.initialize(config)
    
    def on_index_start(self, project_id: str, project_path: str) -> None:
        """Notify all plugins that indexing has started"""
        for plugin in self.plugins.values():
            plugin.on_index_start(project_id, project_path)
    
    def on_index_complete(self, project_id: str, project_path: str) -> None:
        """Notify all plugins that indexing has completed"""
        for plugin in self.plugins.values():
            plugin.on_index_complete(project_id, project_path)
    
    def on_search(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Allow plugins to modify search results"""
        modified_results = results
        for plugin in self.plugins.values():
            modified_results = plugin.on_search(query, modified_results)
        return modified_results
```

## Improved Search Capabilities

### 1. Advanced Query Language

**Current Limitation**: Limited query syntax for complex searches.

**Recommendation**: Implement a more powerful query language:

```python
# mcp_code_indexer/query_parser.py
import re
from typing import Dict, Any, List, Optional, Tuple

class QueryParser:
    """Parser for advanced search queries"""
    
    def __init__(self):
        self.operators = {
            "AND": "&",
            "OR": "|",
            "NOT": "!",
        }
    
    def parse(self, query: str) -> Dict[str, Any]:
        """Parse a query string into structured components"""
        result = {
            "text": "",
            "filters": {},
            "sort": None,
            "limit": None,
        }
        
        # Extract filters (field:value)
        filter_pattern = r'(\w+):("[^"]+"|[^\s]+)'
        filters = re.findall(filter_pattern, query)
        for field, value in filters:
            # Remove quotes if present
            value = value.strip('"')
            result["filters"][field] = value
            # Remove the filter from the query
            query = re.sub(f"{field}:{value}", "", query).strip()
        
        # Extract sort directive (sort:field)
        sort_match = re.search(r'sort:(\w+)', query)
        if sort_match:
            result["sort"] = sort_match.group(1)
            query = re.sub(r'sort:\w+', "", query).strip()
        
        # Extract limit directive (limit:N)
        limit_match = re.search(r'limit:(\d+)', query)
        if limit_match:
            result["limit"] = int(limit_match.group(1))
            query = re.sub(r'limit:\d+', "", query).strip()
        
        # The remaining text is the search query
        result["text"] = query
        
        return result

# Usage in SearchEngine
def search(self, query: str, project_ids: Optional[List[str]] = None, 
           filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Enhanced search with query parsing"""
    
    # Parse the query
    parser = QueryParser()
    parsed_query = parser.parse(query)
    
    # Merge parsed filters with explicit filters
    if filters is None:
        filters = {}
    filters.update(parsed_query["filters"])
    
    # Use parsed limit if provided
    if parsed_query["limit"] is not None:
        limit = parsed_query["limit"]
    
    # Use the parsed text as the actual query
    query_text = parsed_query["text"]
    
    # Continue with existing search logic...
    # ...
```

### 2. Semantic Code Search Enhancements

**Current Limitation**: Basic semantic search without context awareness.

**Recommendation**: Enhance semantic search with context-aware embeddings:

```python
# Enhanced embedding generation in indexer.py
def _process_file(self, file_path: str) -> List[CodeChunk]:
    """Process a file with enhanced context awareness"""
    # ... existing code ...
    
    # Get code structure
    from .code_analyzer import CodeAnalyzer
    analyzer = CodeAnalyzer()
    structure = analyzer.get_code_structure(content, language)
    
    # Create context-aware chunks
    chunks = []
    
    # Process functions with their context
    for func in structure["functions"]:
        # Extract function content
        start_line = func["start_line"]
        end_line = func["end_line"]
        func_content = '\n'.join(content.split('\n')[start_line:end_line+1])
        
        # Get imports that might be relevant to this function
        imports = self._find_relevant_imports(structure["imports"], func_content)
        
        # Add imports as context
        context = '\n'.join(imports) + '\n\n' + func_content
        
        # Create chunk with enhanced metadata
        chunks.append(CodeChunk(
            content=context,  # Context-enhanced content
            file_path=file_path,
            start_line=start_line + 1,
            end_line=end_line + 1,
            language=language,
            type="function",
            metadata={
                "function_name": func["name"],
                "imports": imports,
                "dependencies": self._find_dependencies(func_content, structure)
            }
        ))
    
    # Similar processing for classes...
    
    return chunks

def _find_relevant_imports(self, all_imports: List[str], code_content: str) -> List[str]:
    """Find imports that are relevant to the given code content"""
    relevant_imports = []
    
    for imp in all_imports:
        # Extract the module/symbol being imported
        import_match = re.search(r'import\s+(\w+)', imp)
        from_match = re.search(r'from\s+[\w.]+\s+import\s+([\w,\s]+)', imp)
        
        if import_match:
            module = import_match.group(1)
            if module in code_content:
                relevant_imports.append(imp)
        elif from_match:
            symbols = from_match.group(1).split(',')
            for symbol in symbols:
                symbol = symbol.strip()
                if symbol in code_content:
                    relevant_imports.append(imp)
                    break
    
    return relevant_imports
```

### 3. Multi-Modal Search

**Current Limitation**: Text-only search without considering code structure.

**Recommendation**: Implement multi-modal search combining text and structure:

```python
# search_engine.py
def multi_modal_search(self, query: str, project_ids: Optional[List[str]] = None,
                      filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Multi-modal search combining semantic and structural search
    
    Args:
        query: Search query
        project_ids: Project IDs to search
        filters: Additional filters
        limit: Result limit
        
    Returns:
        Combined search results
    """
    # 1. Perform semantic search
    semantic_results = self.search(query, project_ids, filters, limit=limit*2)
    
    # 2. Extract code structure from query
    from .code_analyzer import CodeAnalyzer
    analyzer = CodeAnalyzer()
    
    # Create a minimal code snippet from the query to analyze structure
    query_lang = filters.get("language", "python")  # Default to Python
    query_code = f"def example():\n    {query}\n"
    
    # Analyze the query structure
    query_structure = analyzer.analyze_code(query_code, query_lang)
    
    # 3. Score results based on structural similarity
    scored_results = []
    for result in semantic_results:
        # Get the code content
        content = result.get("content", "")
        language = result.get("language", query_lang)
        
        # Analyze the result structure
        result_structure = analyzer.analyze_code(content, language)
        
        # Calculate structural similarity score
        structure_score = self._calculate_structure_similarity(
            query_structure, result_structure
        )
        
        # Combine semantic and structural scores
        combined_score = 0.7 * result.get("similarity", 0) + 0.3 * structure_score
        
        # Add to scored results
        result_copy = result.copy()
        result_copy["similarity"] = combined_score
        result_copy["structure_score"] = structure_score
        scored_results.append(result_copy)
    
    # Sort by combined score
    scored_results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
    
    return scored_results[:limit]

def _calculate_structure_similarity(self, query_structure: Dict[str, Any], 
                                   result_structure: Dict[str, Any]) -> float:
    """Calculate structural similarity between query and result"""
    # Compare function calls
    query_deps = set(query_structure.get("dependencies", []))
    result_deps = set(result_structure.get("dependencies", []))
    
    if not query_deps:
        return 0.5  # Neutral score if no dependencies in query
    
    # Calculate Jaccard similarity
    intersection = len(query_deps.intersection(result_deps))
    union = len(query_deps.union(result_deps))
    
    if union == 0:
        return 0.5
    
    return intersection / union
```

### 4. Code Graph-Based Search

**Current Limitation**: No graph-based search capabilities.

**Recommendation**: Implement a code graph database for relationship-based searches:

```python
# mcp_code_indexer/graph_search.py
from typing import List, Dict, Any, Optional
import networkx as nx

class CodeGraphSearch:
    """Graph-based code search"""
    
    def __init__(self, config):
        self.config = config
        self.graph = nx.DiGraph()
    
    def build_graph(self, project_id: str, code_analyzer) -> None:
        """Build a code graph from analyzed code"""
        # Get all indexed files
        indexed_files = self._get_indexed_files(project_id)
        
        for file_path in indexed_files:
            # Analyze file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get language from file extension
            ext = os.path.splitext(file_path)[1].lower()
            language = self._get_language_from_extension(ext)
            
            # Analyze code structure
            structure = code_analyzer.get_code_structure(content, language)
            
            # Add file node
            file_node_id = f"file:{file_path}"
            self.graph.add_node(file_node_id, type="file", path=file_path)
            
            # Process functions
            for func in structure["functions"]:
                func_node_id = f"func:{file_path}:{func['name']}"
                self.graph.add_node(
                    func_node_id, 
                    type="function",
                    name=func["name"],
                    start_line=func["start_line"],
                    end_line=func["end_line"]
                )
                
                # Connect function to file
                self.graph.add_edge(func_node_id, file_node_id, type="defined_in")
                
                # Process function dependencies
                for dep in self._extract_dependencies(func):
                    dep_node_id = f"symbol:{dep}"
                    self.graph.add_node(dep_node_id, type="symbol", name=dep)
                    self.graph.add_edge(func_node_id, dep_node_id, type="uses")
            
            # Process classes similarly...
    
    def search(self, query: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Search the code graph"""
        # Parse query to extract target and relationship
        parts = query.split()
        if len(parts) < 3:
            return []
        
        source_type = parts[0]  # e.g., "function", "class"
        relation = parts[1]     # e.g., "uses", "calls", "imports"
        target = ' '.join(parts[2:])  # e.g., "parse_query"
        
        # Find matching nodes
        results = []
        
        if source_type == "function":
            # Find functions that use the target
            for node, data in self.graph.nodes(data=True):
                if data.get("type") == "function":
                    # Check if this function uses the target
                    neighbors = list(self.graph.neighbors(node))
                    for neighbor in neighbors:
                        neighbor_data = self.graph.nodes[neighbor]
                        if (neighbor_data.get("type") == "symbol" and 
                            neighbor_data.get("name") == target and
                            self.graph.edges[node, neighbor].get("type") == relation):
                            
                            # Found a match
                            function_data = data.copy()
                            file_node = next((n for n in self.graph.neighbors(node) 
                                             if self.graph.nodes[n].get("type") == "file"), None)
                            
                            if file_node:
                                function_data["file_path"] = self.graph.nodes[file_node].get("path")
                            
                            results.append(function_data)
        
        return results
```

### 5. Natural Language Code Search

**Current Limitation**: Limited natural language understanding.

**Recommendation**: Enhance the natural language search with better query understanding:

```python
# Enhanced natural language search in search_engine.py
def natural_language_search(self, query: str, project_ids: Optional[List[str]] = None,
                          filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> Dict[str, Any]:
    """
    Enhanced natural language code search
    
    Args:
        query: Natural language query
        project_ids: Project IDs to search
        filters: Additional filters
        limit: Result limit
        
    Returns:
        Search results with LLM-generated answer
    """
    try:
        # 1. Analyze the query intent
        query_intent = self._analyze_query_intent(query)
        
        # 2. Transform the query based on intent
        transformed_query = self._transform_query(query, query_intent)
        
        # 3. Get search results using the transformed query
        results = self.search(transformed_query, project_ids, filters, limit=limit)
        
        if not results:
            return {
                "answer": f"No code found matching '{query}'.",
                "context_files": [],
                "search_query": query,
                "transformed_query": transformed_query
            }
        
        # 4. Prepare context for LLM
        context_text = ""
        context_files = []
        
        for i, result in enumerate(results, 1):
            file_path = result.get('file_path', 'unknown')
            language = result.get('language', 'text')
            content = result.get('content', '')
            start_line = result.get('start_line', 1)
            end_line = result.get('end_line', 1)
            
            # Add to context
            context_text += f"\n[{i}] File: {file_path} (lines {start_line}-{end_line}):\n"
            context_text += f"```{language}\n{content}\n```\n"
            
            # Save context file
            context_files.append({
                "file_path": file_path,
                "content": content,
                "language": language,
                "start_line": start_line,
                "end_line": end_line,
                "similarity": result.get('similarity', 0.0)
            })
        
        # 5. Generate answer using LLM
        prompt_template = """
        You are a code assistant helping a developer understand code.
        
        User query: {query}
        
        Based on the following code snippets, provide a clear and concise answer:
        
        {context}
        
        Focus on explaining how the code works and how it relates to the user's query.
        If the code doesn't fully answer the query, acknowledge that and explain what's missing.
        Reference specific code snippets by their number (e.g., [1], [2]) in your explanation.
        """
        
        prompt = prompt_template.format(
            query=query,
            context=context_text
        )
        
        # Call LLM
        answer = self._call_llm(prompt)
        
        return {
            "answer": answer,
            "context_files": context_files,
            "search_query": query,
            "transformed_query": transformed_query,
            "query_intent": query_intent
        }
        
    except Exception as e:
        logger.error(f"Natural language search failed: {str(e)}")
        return {
            "answer": f"Search error: {str(e)}",
            "context_files": [],
            "search_query": query
        }

def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
    """Analyze the intent of a natural language query"""
    # Intent categories
    intents = {
        "function_search": ["how to", "function for", "implement", "code that"],
        "definition_search": ["what is", "define", "meaning of", "definition of"],
        "example_search": ["example of", "sample code", "usage of", "how to use"],
        "error_search": ["error", "exception", "bug", "fix", "issue", "problem"],
        "concept_search": ["concept", "pattern", "architecture", "design"]
    }
    
    # Determine primary intent
    query_lower = query.lower()
    primary_intent = "general"
    max_matches = 0
    
    for intent, patterns in intents.items():
        matches = sum(1 for pattern in patterns if pattern in query_lower)
        if matches > max_matches:
            max_matches = matches
            primary_intent = intent
    
    # Extract key entities
    entities = {}
    
    # Look for code elements
    code_patterns = {
        "function": [r'function\s+(\w+)', r'method\s+(\w+)', r'(\w+)\s+function', r'(\w+)\s+method'],
        "class": [r'class\s+(\w+)', r'(\w+)\s+class'],
        "variable": [r'variable\s+(\w+)', r'(\w+)\s+variable'],
        "file": [r'file\s+(\w+\.\w+)', r'(\w+\.\w+)\s+file'],
        "language": [r'in\s+(python|javascript|java|c\+\+|typescript|php|ruby|go)']
    }
    
    for entity_type, patterns in code_patterns.items():
        for pattern in patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                entities[entity_type] = matches[0]
                break
    
    return {
        "primary_intent": primary_intent,
        "entities": entities
    }

def _transform_query(self, query: str, intent: Dict[str, Any]) -> str:
    """Transform a natural language query based on intent analysis"""
    primary_intent = intent["primary_intent"]
    entities = intent["entities"]
    
    # Base transformed query is the original
    transformed = query
    
    # Add intent-specific terms
    if primary_intent == "function_search":
        if "function" in entities:
            transformed = f"function {entities['function']} {query}"
        else:
            transformed = f"function {query}"
    
    elif primary_intent == "definition_search":
        if "class" in entities:
            transformed = f"class {entities['class']} definition {query}"
        elif "function" in entities:
            transformed = f"function {entities['function']} definition {query}"
    
    elif primary_intent == "example_search":
        transformed = f"example {query}"
    
    elif primary_intent == "error_search":
        transformed = f"error {query}"
    
    # Add language filter if specified
    if "language" in entities:
        transformed = f"{transformed} language:{entities['language']}"
    
    return transformed
```

## Implementation Roadmap

1. **Phase 1: Core Improvements**
   - Implement REST API layer
   - Enhance query language
   - Improve semantic search with context awareness

2. **Phase 2: Advanced Features**
   - Add multi-modal search
   - Implement code graph database
   - Enhance natural language search

3. **Phase 3: Integration Options**
   - Develop LSP integration
   - Create CI/CD integrations
   - Implement plugin system
   - Add WebSocket support

## Conclusion

By implementing these improvements to integration options and search capabilities, the mcp-index project will become more versatile, powerful, and user-friendly. The enhanced integration options will allow the system to be used in a wider variety of contexts, while the improved search capabilities will provide more accurate and relevant results to users.