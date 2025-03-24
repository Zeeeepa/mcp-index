# MCP-Index Upgrade Plan

This document outlines a comprehensive plan for upgrading the mcp-index project to enhance efficiency, robustness, and integration while maintaining compatibility with existing implementations.

## 1. Current Architecture Analysis

The mcp-index project is a sophisticated code indexing and retrieval system with the following key components:

- **CodeIndexer**: Manages the indexing process using sentence transformers and ChromaDB
- **CodeAnalyzer**: Uses tree-sitter to parse and analyze code structure
- **SearchEngine**: Provides semantic code search capabilities
- **ContextManager**: Handles code context with caching and compression

Current dependencies include:
- sentence-transformers for embeddings
- chromadb for vector storage
- tree-sitter for code parsing
- flask for API
- langchain for LLM integration

## 2. Upgrade Goals

1. **Enhance Efficiency**: Improve performance and reduce resource usage
2. **Improve Robustness**: Add better error handling and fault tolerance
3. **Enhance Integration**: Provide more comprehensive API and integration options
4. **Maintain Compatibility**: Ensure seamless integration with existing implementations
5. **Reduce Code Complexity**: Leverage modern libraries to achieve more with less code

## 3. Library Enhancements

### 3.1 Vector Database Upgrade

**Current Implementation**: ChromaDB

**Proposed Enhancement**: Upgrade to LanceDB or Qdrant

**Rationale**:
- **LanceDB**: An open-source, high-performance, serverless vector database built on top of Lance data format. It's significantly faster than ChromaDB and has a simpler API.
  - Provides up to 10x faster vector search
  - Supports on-disk storage with minimal memory footprint
  - Native support for hybrid search (vector + metadata filtering)
  - Simple Python API that's compatible with existing code

- **Qdrant**: A vector database with extended filtering capabilities
  - Better performance for large-scale deployments
  - Advanced filtering capabilities
  - Supports payload-based pre-filtering

**Implementation Strategy**:
- Create an abstraction layer for vector database operations
- Implement adapters for both ChromaDB and the new database
- Allow configuration-based selection of the backend
- Provide migration utilities for existing indices

```python
# Example abstraction layer
class VectorStore:
    @classmethod
    def create(cls, config):
        backend = config.get("vector_store.backend", "chroma")
        if backend == "lancedb":
            return LanceDBStore(config)
        elif backend == "qdrant":
            return QdrantStore(config)
        else:
            return ChromaDBStore(config)  # Default
```

### 3.2 Embedding Model Enhancement

**Current Implementation**: sentence-transformers

**Proposed Enhancement**: Integrate with MTEB-optimized models and add support for E5, BGE, and GTE models

**Rationale**:
- MTEB (Massive Text Embedding Benchmark) optimized models provide better performance
- E5, BGE, and GTE models offer state-of-the-art performance for code embeddings
- Support for quantized models reduces memory usage and improves inference speed

**Implementation Strategy**:
- Create an embedding model registry with support for multiple model types
- Add support for model quantization (int8, int4) using optimum or bitsandbytes
- Implement model caching to avoid reloading models
- Add support for batched encoding with dynamic batch sizes

```python
# Example embedding model registry
class EmbeddingModelRegistry:
    @classmethod
    def get_model(cls, model_name, quantization=None):
        if model_name.startswith("intfloat/e5-"):
            return E5EmbeddingModel(model_name, quantization)
        elif model_name.startswith("BAAI/bge-"):
            return BGEEmbeddingModel(model_name, quantization)
        else:
            return SentenceTransformerModel(model_name, quantization)
```

### 3.3 Code Parsing Enhancement

**Current Implementation**: tree-sitter with custom parsing logic

**Proposed Enhancement**: Integrate with Semantic Code Libraries like Semgrep or Tree-sitter-graph

**Rationale**:
- Semgrep provides advanced code analysis capabilities with pattern matching
- Tree-sitter-graph adds graph-based code analysis on top of tree-sitter
- These libraries provide more sophisticated code understanding with less custom code

**Implementation Strategy**:
- Create a code analysis abstraction layer
- Implement adapters for tree-sitter, semgrep, and tree-sitter-graph
- Add support for more languages with minimal custom code
- Enhance code structure analysis with semantic understanding

```python
# Example code analysis abstraction
class CodeAnalyzer:
    @classmethod
    def create(cls, language, config):
        analyzer_type = config.get("analyzer.type", "tree-sitter")
        if analyzer_type == "semgrep":
            return SemgrepAnalyzer(language)
        elif analyzer_type == "tree-sitter-graph":
            return TreeSitterGraphAnalyzer(language)
        else:
            return TreeSitterAnalyzer(language)  # Default
```

### 3.4 API Framework Enhancement

**Current Implementation**: Flask

**Proposed Enhancement**: Migrate to FastAPI with async support

**Rationale**:
- FastAPI provides automatic OpenAPI documentation
- Type hints and validation with Pydantic models
- Async support for better performance
- Dependency injection for cleaner code

**Implementation Strategy**:
- Create a new API layer using FastAPI
- Define Pydantic models for request/response validation
- Implement async endpoints for better performance
- Maintain backward compatibility with existing API endpoints
- Add comprehensive API documentation

```python
# Example FastAPI implementation
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

app = FastAPI(title="MCP Code Indexer API", version="0.2.0")

class SearchRequest(BaseModel):
    query: str
    project_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10

@app.post("/api/search", response_model=SearchResponse)
async def search_code(request: SearchRequest, search_engine = Depends(get_search_engine)):
    try:
        results = await search_engine.search_async(
            request.query, request.project_ids, request.filters, request.limit
        )
        return format_search_results(results, request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3.5 Context Management Enhancement

**Current Implementation**: Custom ContextManager with file-based caching

**Proposed Enhancement**: Integrate with LRU caching and Redis for distributed deployments

**Rationale**:
- LRU caching provides better memory management
- Redis enables distributed caching for multi-server deployments
- More efficient context retrieval and storage

**Implementation Strategy**:
- Implement a pluggable cache backend system
- Add support for in-memory LRU cache (using functools.lru_cache or cachetools)
- Add support for Redis as a distributed cache backend
- Maintain backward compatibility with existing file-based cache

```python
# Example context cache enhancement
from cachetools import LRUCache
import redis

class ContextCache:
    @classmethod
    def create(cls, config):
        cache_type = config.get("context_cache.type", "file")
        if cache_type == "memory":
            return MemoryContextCache(
                max_size=config.get("context_cache.max_size", 1000)
            )
        elif cache_type == "redis":
            return RedisContextCache(
                redis_url=config.get("context_cache.redis_url"),
                max_size=config.get("context_cache.max_size", 1000)
            )
        else:
            return FileContextCache(
                cache_dir=config.get("context_cache.dir"),
                max_size=config.get("context_cache.max_size", 1000)
            )
```

### 3.6 Search Capability Enhancement

**Current Implementation**: Basic vector search with filtering

**Proposed Enhancement**: Hybrid search combining vector search with BM25 or sparse vectors

**Rationale**:
- Hybrid search combines the strengths of semantic and keyword search
- BM25 provides excellent keyword matching capabilities
- Sparse vectors (like SPLADE) can enhance retrieval for specific terms
- Better handling of code-specific search patterns

**Implementation Strategy**:
- Implement BM25 indexing alongside vector indexing
- Add support for hybrid search combining both approaches
- Implement code-specific search features (function search, class search)
- Add support for regular expression search within semantic results

```python
# Example hybrid search implementation
class HybridSearchEngine:
    def __init__(self, vector_store, bm25_index):
        self.vector_store = vector_store
        self.bm25_index = bm25_index
        
    async def search(self, query, project_ids=None, filters=None, limit=10):
        # Get vector search results
        vector_results = await self.vector_store.search(query, project_ids, filters, limit*2)
        
        # Get BM25 results
        bm25_results = self.bm25_index.search(query, project_ids, filters, limit*2)
        
        # Combine results with reciprocal rank fusion
        combined_results = self._combine_results(vector_results, bm25_results, limit)
        
        return combined_results
```

## 4. Implementation Plan

### Phase 1: Core Infrastructure Upgrades

1. Create abstraction layers for key components:
   - Vector database
   - Embedding models
   - Code analyzers
   - Context caching

2. Implement the new backends while maintaining compatibility:
   - LanceDB/Qdrant adapter
   - Enhanced embedding model support
   - Improved code analysis with Semgrep/Tree-sitter-graph

3. Add comprehensive test coverage for the new components

### Phase 2: API and Integration Enhancements

1. Implement FastAPI-based API layer
2. Add async support for core operations
3. Create Pydantic models for request/response validation
4. Generate OpenAPI documentation
5. Implement WebSocket support for real-time updates

### Phase 3: Search and Performance Enhancements

1. Implement hybrid search capabilities
2. Add support for code-specific search features
3. Optimize performance for large codebases
4. Implement distributed deployment support
5. Add monitoring and telemetry

## 5. Compatibility Strategy

To ensure seamless integration with existing implementations:

1. Maintain backward compatibility for all public APIs
2. Provide configuration options to use either old or new implementations
3. Implement adapters for new components to work with existing code
4. Create migration utilities for existing data
5. Add comprehensive documentation for upgrading

## 6. Recommended Libraries

| Category | Current Library | Recommended Upgrade | Benefits |
|----------|----------------|---------------------|----------|
| Vector Database | ChromaDB | LanceDB or Qdrant | 5-10x faster search, better filtering, lower memory usage |
| Embeddings | sentence-transformers | E5, BGE, GTE models | Better code understanding, support for quantization |
| Code Analysis | tree-sitter | Semgrep or tree-sitter-graph | More sophisticated code understanding, pattern matching |
| API Framework | Flask | FastAPI | Automatic documentation, validation, async support |
| Caching | Custom file-based | LRU cache + Redis | Better performance, distributed support |
| Search | Vector search | Hybrid search (vector + BM25) | Better recall, code-specific features |

## 7. Conclusion

This upgrade plan provides a comprehensive roadmap for enhancing the mcp-index project while maintaining compatibility with existing implementations. By leveraging modern libraries and architectural patterns, we can significantly improve performance, robustness, and integration capabilities with less code.

The phased implementation approach ensures that we can deliver value incrementally while minimizing disruption to existing users. The abstraction layers and compatibility strategies will allow for a smooth transition to the new architecture.