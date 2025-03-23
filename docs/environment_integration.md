# Environment Integration Recommendations

This document outlines recommendations for integrating the `environment` folder components with the rest of the codebase and improving component interconnectivity.

## Current Architecture

The current architecture consists of:

1. **Core Indexing System**:
   - `indexer.py`: Main code indexing system using ChromaDB for vector storage
   - `search_engine.py`: Search functionality on top of the indexed code
   - `code_analyzer.py`, `code_compressor.py`, `code_optimizer.py`: Code processing components

2. **Environment Components** (currently not integrated):
   - `environment/environment.py`: Message-passing environment for agents
   - `environment/graph_database/`: Neo4j graph database implementation

3. **Server and Client**:
   - `server/mcp_server.py`: MCP protocol server exposing indexing and search functionality
   - `client/`: CLI and plugin implementations for interacting with the server

## Integration Recommendations

### 1. Integrate GraphDatabaseHandler with CodeIndexer

The `GraphDatabaseHandler` in `environment/graph_database/graph_database.py` provides a Neo4j-based graph database that can complement the vector-based search in `indexer.py`. This would enable both semantic search (vectors) and structural search (graph).

#### Implementation Steps:

1. **Add Graph Database Support to CodeIndexer**:

```python
# In indexer.py

from .environment.graph_database.graph_database import GraphDatabaseHandler

class CodeIndexer:
    def __init__(self, config: Config):
        # Existing initialization code...
        
        # Initialize graph database if enabled
        self.use_graph_db = config.get("indexer.use_graph_db", False)
        if self.use_graph_db:
            self.graph_db = GraphDatabaseHandler(
                uri=config.get("graph_db.uri", "bolt://localhost:7687"),
                user=config.get("graph_db.user", "neo4j"),
                password=config.get("graph_db.password", "password"),
                database_name=config.get("graph_db.database", "neo4j"),
                task_id=config.get("graph_db.task_id", "mcp_indexer"),
                use_lock=config.get("graph_db.use_lock", True)
            )
```

2. **Extend _process_file Method to Add Code to Graph Database**:

```python
# In indexer.py, extend _process_file method

def _process_file(self, file_path: str) -> List[CodeChunk]:
    # Existing code processing...
    
    # Add to graph database if enabled
    if self.use_graph_db and chunks:
        try:
            # Extract file information
            file_node = self.graph_db.add_node(
                label="File",
                full_name=file_path,
                parms={
                    "language": language,
                    "file_path": file_path,
                    "line_count": len(content.splitlines())
                }
            )
            
            # Add each code chunk to graph
            for chunk in chunks:
                chunk_node = self.graph_db.add_node(
                    label=chunk.type.capitalize(),
                    full_name=f"{file_path}:{chunk.start_line}-{chunk.end_line}",
                    parms={
                        "content": chunk.content,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "language": chunk.language
                    }
                )
                
                # Connect chunk to file
                self.graph_db.add_edge(
                    start_name=file_path,
                    relationship_type="CONTAINS",
                    end_name=f"{file_path}:{chunk.start_line}-{chunk.end_line}"
                )
                
                # TODO: Add more relationships based on code analysis
                # e.g., function calls, imports, etc.
        except Exception as e:
            logger.error(f"Error adding to graph database: {str(e)}")
    
    return chunks
```

3. **Add Graph-Based Search Methods to SearchEngine**:

```python
# In search_engine.py

def graph_search(self, query: str, project_ids: Optional[List[str]] = None, 
                limit: int = 10) -> List[Dict[str, Any]]:
    """
    Execute a graph-based search using Cypher query
    
    Args:
        query: Cypher query string
        project_ids: Project IDs to search in
        limit: Maximum number of results
        
    Returns:
        List of search results
    """
    if not self.indexer.use_graph_db:
        return []
    
    try:
        # Execute Cypher query
        cypher_query = f"""
        MATCH (n)
        WHERE n.content CONTAINS $query
        RETURN n
        LIMIT $limit
        """
        
        results = self.indexer.graph_db.execute_query(
            cypher_query, 
            query=query,
            limit=limit
        )
        
        # Format results
        formatted_results = []
        for record in results:
            node = record["n"]
            formatted_results.append({
                "file_path": node.get("file_path", ""),
                "content": node.get("content", ""),
                "start_line": node.get("start_line", 0),
                "end_line": node.get("end_line", 0),
                "language": node.get("language", ""),
                "type": node.get("type", "code")
            })
        
        return formatted_results
    except Exception as e:
        logger.error(f"Graph search failed: {str(e)}")
        return []
```

### 2. Integrate Environment Class with Server

The `Environment` class in `environment/environment.py` provides a message-passing system that can be used to implement a multi-agent architecture for code analysis. This can be integrated with the server to enable more complex code analysis workflows.

#### Implementation Steps:

1. **Create an Agent Manager Class**:

```python
# Create a new file: mcp_code_indexer/agent_manager.py

from typing import Dict, List, Any, Optional
from .environment.environment import Environment
from .config import Config
from .indexer import CodeIndexer
from .search_engine import SearchEngine

class AgentManager:
    """
    Agent Manager class
    
    Manages a multi-agent system for code analysis using the Environment
    """
    
    def __init__(self, config: Config, indexer: CodeIndexer, search_engine: SearchEngine):
        """
        Initialize Agent Manager
        
        Args:
            config: Configuration object
            indexer: Code indexer
            search_engine: Search engine
            
        Returns:
            None
        """
        self.config = config
        self.indexer = indexer
        self.search_engine = search_engine
        
        # Initialize environment with roles
        self.roles = ["code_analyzer", "search_agent", "quality_analyzer", "dependency_analyzer"]
        self.environment = Environment(roles=self.roles)
        
        # Initialize agents
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all agents in the environment"""
        # Implementation of agent initialization
        pass
    
    def analyze_code(self, file_path: str) -> Dict[str, Any]:
        """
        Perform multi-agent code analysis
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Analysis results
        """
        # Implementation of multi-agent code analysis
        pass
    
    # Additional methods for agent coordination
```

2. **Integrate Agent Manager with Server**:

```python
# In server/mcp_server.py

from mcp_code_indexer.agent_manager import AgentManager

def setup_mcp_server(config, indexer, search_engine, formatter):
    # Existing server setup code...
    
    # Initialize agent manager
    agent_manager = AgentManager(config, indexer, search_engine)
    
    # Add new tool for multi-agent code analysis
    @server.list_tools()
    async def list_tools():
        tools = [
            # Existing tools...
            
            Tool(
                name="multi_agent_analyze",
                description="Perform multi-agent code analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to analyze"
                        }
                    },
                    "required": ["file_path"]
                }
            )
        ]
        return tools
    
    # Add handler for the new tool
    @server.call_tool()
    async def call_tool(name, args):
        # Existing tool handlers...
        
        elif name == "multi_agent_analyze":
            if "file_path" not in args:
                return [
                    TextContent(
                        type="text",
                        text="Error: Missing file path parameter"
                    )
                ]
            
            try:
                analysis_results = agent_manager.analyze_code(args["file_path"])
                
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(analysis_results, indent=2, ensure_ascii=False)
                    )
                ]
            except Exception as e:
                return [
                    TextContent(
                        type="text",
                        text=f"Multi-agent analysis failed: {str(e)}"
                    )
                ]
```

### 3. Improve Component Interconnectivity

#### Configuration Updates:

1. **Add Graph Database Configuration**:

```python
# In config.py, extend default configuration

DEFAULT_CONFIG = {
    # Existing configuration...
    
    "indexer": {
        # Existing indexer configuration...
        "use_graph_db": False
    },
    
    "graph_db": {
        "uri": "bolt://localhost:7687",
        "user": "neo4j",
        "password": "password",
        "database": "neo4j",
        "task_id": "mcp_indexer",
        "use_lock": True
    },
    
    "agents": {
        "enabled": False,
        "roles": ["code_analyzer", "search_agent", "quality_analyzer", "dependency_analyzer"]
    }
}
```

2. **Create Factory Methods for Component Creation**:

```python
# Create a new file: mcp_code_indexer/factory.py

from typing import Dict, Any, Optional
from .config import Config
from .indexer import CodeIndexer
from .search_engine import SearchEngine
from .agent_manager import AgentManager

def create_indexer(config: Config) -> CodeIndexer:
    """Create and initialize a CodeIndexer instance"""
    return CodeIndexer(config)

def create_search_engine(config: Config, indexer: CodeIndexer) -> SearchEngine:
    """Create and initialize a SearchEngine instance"""
    return SearchEngine(config, indexer)

def create_agent_manager(config: Config, indexer: CodeIndexer, search_engine: SearchEngine) -> Optional[AgentManager]:
    """Create and initialize an AgentManager instance if enabled"""
    if config.get("agents.enabled", False):
        return AgentManager(config, indexer, search_engine)
    return None

def create_all_components(config: Config) -> Dict[str, Any]:
    """Create all components and return them in a dictionary"""
    indexer = create_indexer(config)
    search_engine = create_search_engine(config, indexer)
    agent_manager = create_agent_manager(config, indexer, search_engine)
    
    return {
        "indexer": indexer,
        "search_engine": search_engine,
        "agent_manager": agent_manager
    }
```

3. **Use Factory in Server Initialization**:

```python
# In server/app.py

from mcp_code_indexer.factory import create_all_components

def create_app():
    # Load configuration
    config = Config()
    
    # Create components
    components = create_all_components(config)
    indexer = components["indexer"]
    search_engine = components["search_engine"]
    agent_manager = components["agent_manager"]
    
    # Create formatter
    formatter = MCPFormatter()
    
    # Setup server
    server = setup_mcp_server(config, indexer, search_engine, formatter, agent_manager)
    
    # Return server
    return server
```

## Unused Functions and Components

The following components appear to be unused and could be refactored or removed:

1. **AST Search Components**: The `environment/graph_database/ast_search/` directory contains AST management utilities that aren't currently used. These could be integrated with the code analyzer.

2. **Indexer Components**: The `environment/graph_database/indexer/` directory contains indexing utilities that overlap with the main indexer functionality. Consider merging or removing.

3. **Duplicate Code Analysis**: There's potential duplication between `code_analyzer.py` and `environment/graph_database/ast_search/ast_manage.py`. Consider consolidating these.

## Conclusion

By implementing these recommendations, the `environment` folder components will be properly integrated with the rest of the codebase, enabling:

1. **Dual-Search Capability**: Both vector-based semantic search and graph-based structural search
2. **Multi-Agent Architecture**: Complex code analysis workflows using the Environment message-passing system
3. **Improved Component Organization**: Better separation of concerns and reduced duplication

These changes will enhance the functionality of the MCP Code Indexer while maintaining its modular architecture.