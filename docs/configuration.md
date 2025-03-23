# MCP-Index Configuration Guide

This document provides a comprehensive guide to configuring the MCP-Index system.

## Configuration File Format

MCP-Index uses a YAML-based configuration file format. The configuration file can be specified using the `--config` command-line argument when starting the server.

```bash
python -m server.app --config config.yaml
```

If no configuration file is specified, the system will look for a file named `config.yaml` in the current directory.

## Configuration Sections

The configuration file is organized into several sections, each controlling a different aspect of the system.

### General Configuration

```yaml
# General configuration
general:
  # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  log_level: INFO
  # Cache directory for storing temporary files
  cache_dir: ".cache"
  # Maximum number of concurrent tasks
  max_concurrent_tasks: 4
```

### Indexer Configuration

```yaml
# Indexer configuration
indexer:
  # Enable or disable the graph database integration
  use_graph_db: false
  # Maximum number of files to index per project
  max_files: 10000
  # File extensions to include in indexing
  include_extensions: [".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".go", ".rb", ".php", ".html", ".css", ".md"]
  # File patterns to exclude from indexing
  exclude_patterns: ["node_modules", "venv", ".git", "__pycache__", "*.min.js"]
  # Normalization level for code compression (NONE, MINIMAL, MODERATE, AGGRESSIVE)
  normalization_level: MODERATE
  # Maximum number of tokens per chunk
  max_tokens_per_chunk: 1024
  # Overlap between chunks (percentage)
  chunk_overlap: 0.1
```

### Search Engine Configuration

```yaml
# Search engine configuration
search_engine:
  # Default number of results to return
  default_limit: 10
  # Minimum similarity score for results (0.0 to 1.0)
  min_similarity: 0.7
  # Context window size (number of lines before and after the match)
  context_window: 5
  # Enable or disable semantic search
  use_semantic_search: true
  # Enable or disable keyword search
  use_keyword_search: true
  # Weight for semantic search results (0.0 to 1.0)
  semantic_weight: 0.7
  # Weight for keyword search results (0.0 to 1.0)
  keyword_weight: 0.3
```

### Embedding Configuration

```yaml
# Embedding configuration
embeddings:
  # Embedding model to use
  model: "all-MiniLM-L6-v2"
  # Device to use for embedding generation (cpu, cuda)
  device: "cpu"
  # Batch size for embedding generation
  batch_size: 32
  # Normalize embeddings
  normalize: true
  # Cache embeddings to disk
  cache_embeddings: true
```

### Vector Database Configuration

```yaml
# Vector database configuration
vector_db:
  # Vector database implementation (chroma, faiss)
  implementation: "chroma"
  # Vector database directory
  directory: ".vectordb"
  # Distance metric (cosine, l2, ip)
  distance_metric: "cosine"
```

### Graph Database Configuration

```yaml
# Graph database configuration (Neo4j)
graph_db:
  # Neo4j connection URI
  uri: "bolt://localhost:7687"
  # Neo4j username
  user: "neo4j"
  # Neo4j password
  password: "password"
  # Neo4j database name
  database_name: "neo4j"
  # Use file lock for concurrent access
  use_lock: true
  # Lock file path
  lockfile: "neo4j.lock"
```

### Agent Configuration

```yaml
# Agent configuration
agents:
  # Enable or disable the agent system
  enabled: false
  # Agent roles to enable
  roles: ["code_analyzer", "search_agent", "quality_analyzer", "dependency_analyzer"]
  # Agent message queue size
  queue_size: 100
  # Agent processing interval (seconds)
  processing_interval: 0.1
  # Agent timeout (seconds)
  timeout: 30
```

### Server Configuration

```yaml
# Server configuration
server:
  # Server host
  host: "127.0.0.1"
  # Server port
  port: 5000
  # Enable or disable debug mode
  debug: false
  # Enable or disable CORS
  cors_enabled: true
  # CORS allowed origins
  cors_origins: ["*"]
  # Maximum request size (bytes)
  max_request_size: 10485760  # 10MB
```

## Environment Variables

In addition to the configuration file, MCP-Index also supports configuration through environment variables. Environment variables take precedence over configuration file values.

Environment variables should be prefixed with `MCP_` and use underscores to separate words. For example, to set the log level, you would use the environment variable `MCP_GENERAL_LOG_LEVEL`.

Example:

```bash
export MCP_GENERAL_LOG_LEVEL=DEBUG
export MCP_INDEXER_USE_GRAPH_DB=true
export MCP_GRAPH_DB_URI=bolt://localhost:7687
```

## Configuration Validation

MCP-Index validates the configuration at startup and will log warnings for any invalid or missing configuration values. If critical configuration values are missing or invalid, the server will fail to start.

## Default Configuration

If a configuration file is not provided and no environment variables are set, MCP-Index will use default values for all configuration options. The default values are designed to work for most common use cases, but may not be optimal for all scenarios.

## Configuration Examples

### Minimal Configuration

```yaml
general:
  log_level: INFO

indexer:
  max_files: 5000
  include_extensions: [".py", ".js", ".ts"]

search_engine:
  default_limit: 5
  min_similarity: 0.6

embeddings:
  model: "all-MiniLM-L6-v2"
  device: "cpu"
```

### Production Configuration

```yaml
general:
  log_level: WARNING
  cache_dir: "/var/cache/mcp-index"
  max_concurrent_tasks: 8

indexer:
  use_graph_db: true
  max_files: 50000
  include_extensions: [".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".go", ".rb", ".php", ".html", ".css", ".md"]
  exclude_patterns: ["node_modules", "venv", ".git", "__pycache__", "*.min.js", "dist", "build"]
  normalization_level: MODERATE
  max_tokens_per_chunk: 1024
  chunk_overlap: 0.1

search_engine:
  default_limit: 10
  min_similarity: 0.7
  context_window: 5
  use_semantic_search: true
  use_keyword_search: true
  semantic_weight: 0.7
  keyword_weight: 0.3

embeddings:
  model: "all-MiniLM-L6-v2"
  device: "cuda"
  batch_size: 64
  normalize: true
  cache_embeddings: true

vector_db:
  implementation: "chroma"
  directory: "/var/lib/mcp-index/vectordb"
  distance_metric: "cosine"

graph_db:
  uri: "bolt://neo4j:7687"
  user: "neo4j"
  password: "secure-password"
  database_name: "mcp-index"
  use_lock: true
  lockfile: "/var/lock/mcp-index/neo4j.lock"

agents:
  enabled: true
  roles: ["code_analyzer", "search_agent", "quality_analyzer", "dependency_analyzer"]
  queue_size: 100
  processing_interval: 0.1
  timeout: 60

server:
  host: "0.0.0.0"
  port: 5000
  debug: false
  cors_enabled: true
  cors_origins: ["https://example.com"]
  max_request_size: 52428800  # 50MB
```

## Troubleshooting

If you encounter issues with your configuration, check the following:

1. Ensure your YAML syntax is correct
2. Verify that all required configuration values are provided
3. Check that file paths exist and are accessible
4. Ensure that database connections are correctly configured
5. Check the server logs for configuration-related errors

For more detailed information on specific configuration options, refer to the relevant sections of the documentation.