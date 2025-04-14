"""
API Server Module

Provides a combined server for both REST API and WebSocket interfaces.
This module serves as the entry point for running the API server.
"""

import os
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .agent_api import app as api_app
from .websocket_api import app as ws_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create combined app
app = FastAPI(
    title="MCP Code Indexer Combined API",
    description="Combined API for interacting with the MCP Code Indexer",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the REST API
app.mount("/api", api_app)

# Mount the WebSocket API
app.mount("/ws-api", ws_app)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return RedirectResponse(url="/docs")

# Run the server
if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=port)