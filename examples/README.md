# MCP-Index Examples

This directory contains example scripts demonstrating how to use the MCP-Index code context retrieval system.

## RelevantCodeContextRetriever Example

The `relevant_context_example.py` script demonstrates how to use the integrated `RelevantCodeContextRetriever` to get relevant code context based on a query and current position.

### Usage

```bash
python relevant_context_example.py <project_path> [query]
```

- `project_path`: Path to the project to index and search
- `query`: (Optional) Search query, defaults to "search functionality"

### Example Output

```
Indexing project: /path/to/project
Indexing status: indexing, progress: 0.10
Indexing status: indexing, progress: 0.30
Indexing status: indexing, progress: 0.50
Indexing status: indexing, progress: 0.70
Indexing status: indexing, progress: 0.90
Indexing completed: 1.00

Searching for: search functionality
Current context: /path/to/examples/relevant_context_example.py:50

Results:
{
  "query": "search functionality",
  "current_context": {
    "file": "/path/to/examples/relevant_context_example.py",
    "line": 50
  },
  "results": [
    {
      "content": "def search(self, query: str, project_ids: Optional[List[str]] = None, \n              filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:\n    \"\"\"\n    Search code (direct access to search engine)\n    \n    Args:\n        query: Search query\n        project_ids: Project IDs\n        filters: Filters\n        limit: Result limit\n        \n    Returns:\n        Search results\n    \"\"\"\n    return self.search_engine.search(query, project_ids, filters, limit)",
      "file_path": "/path/to/project/mcp_code_indexer/relevant_context_retriever.py",
      "start_line": 375,
      "end_line": 389,
      "language": "python",
      "type": "function",
      "similarity": 0.8765,
      "context_relevance": 0.3456,
      "enhanced_context": {
        "content": "def search(self, query: str, project_ids: Optional[List[str]] = None, \n              filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:\n    \"\"\"\n    Search code (direct access to search engine)\n    \n    Args:\n        query: Search query\n        project_ids: Project IDs\n        filters: Filters\n        limit: Result limit\n        \n    Returns:\n        Search results\n    \"\"\"\n    return self.search_engine.search(query, project_ids, filters, limit)",
        "type": "function",
        "name": "search",
        "dependencies": [
          "self.search_engine.search"
        ]
      }
    },
    // More results...
  ],
  "agent_insights": {
    "code_analysis": "Code analysis for /path/to/examples/relevant_context_example.py:\n- Functions: 2\n- Classes: 0\n- Imports: 4\n\nFunctions:\n- main (lines 16-108)\n- print_progress (lines 110-112)",
    "quality_analysis": "Code quality analysis for /path/to/examples/relevant_context_example.py:\n\n## Complexity\n- Cyclomatic complexity: 3\n- Cognitive complexity: 2\n- Function count: 2\n\n## Style\n- Line length: Good\n- Documentation: Good\n- Naming: Good"
  }
}

Top Result:
File: /path/to/project/mcp_code_indexer/relevant_context_retriever.py
Lines: 375-389
Similarity: 0.8765

Enhanced Context (function):
Name: search
Dependencies: ['self.search_engine.search']

Content:
```
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
```
```

## Requirements

- Python 3.7+
- Sentence Transformers
- ChromaDB
- Tree-sitter

## Installation

Make sure you have installed the required dependencies:

```bash
pip install sentence-transformers chromadb tree-sitter
```