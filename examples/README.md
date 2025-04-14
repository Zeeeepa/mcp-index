# MCP Code Indexer Examples

This directory contains example scripts demonstrating how to use the MCP Code Indexer.

## Client Example

The `client_example.py` script demonstrates how to use the MCP Code Indexer client library to:

1. Index a project
2. Search for code
3. Get file overviews
4. Connect to the WebSocket API for real-time updates

### Running the Example

To run the client example:

```bash
# Make sure the API server is running
python -m mcp_code_indexer.cli.server_cli

# In another terminal, run the example
python examples/client_example.py
```

## API Server Example

The MCP Code Indexer API server can be started using the CLI:

```bash
# Start the API server
python -m mcp_code_indexer.cli.server_cli

# Access the API documentation at http://localhost:8000/docs
```

## WebSocket Example

The WebSocket API is included in the API server and can be accessed at `ws://localhost:8000/ws-api/ws`.

See the client example for how to connect to the WebSocket API.