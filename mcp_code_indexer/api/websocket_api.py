"""
WebSocket API Module

Provides a WebSocket interface for real-time communication with the mcp-index codebase.
This module enables real-time updates and streaming responses for AI agents.
"""

import json
import logging
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from pydantic import BaseModel

from ..config import Config
from ..agent_interface import AgentInterface, AgentRequest, AgentResponse, ActionType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Code Indexer WebSocket API",
    description="WebSocket API for real-time interaction with the MCP Code Indexer",
    version="1.0.0"
)

# Initialize config and agent interface
config = Config()
agent_interface = AgentInterface(config)

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Subscription topics
subscriptions: Dict[str, Set[str]] = {
    "indexing_updates": set(),
    "search_updates": set(),
    "analysis_updates": set()
}

# Helper functions
async def notify_subscribers(topic: str, data: Any) -> None:
    """Notify all subscribers of a topic"""
    if topic not in subscriptions:
        return
    
    for connection_id in subscriptions[topic]:
        if connection_id in active_connections:
            try:
                await active_connections[connection_id].send_json({
                    "topic": topic,
                    "data": data
                })
            except Exception as e:
                logger.error(f"Error sending notification to {connection_id}: {str(e)}")

class ConnectionManager:
    """WebSocket connection manager"""
    
    async def connect(self, websocket: WebSocket) -> str:
        """Connect a WebSocket client"""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        active_connections[connection_id] = websocket
        return connection_id
    
    async def disconnect(self, connection_id: str) -> None:
        """Disconnect a WebSocket client"""
        if connection_id in active_connections:
            del active_connections[connection_id]
        
        # Remove from all subscriptions
        for topic in subscriptions:
            if connection_id in subscriptions[topic]:
                subscriptions[topic].remove(connection_id)
    
    async def subscribe(self, connection_id: str, topic: str) -> None:
        """Subscribe a client to a topic"""
        if topic not in subscriptions:
            subscriptions[topic] = set()
        
        subscriptions[topic].add(connection_id)
    
    async def unsubscribe(self, connection_id: str, topic: str) -> None:
        """Unsubscribe a client from a topic"""
        if topic in subscriptions and connection_id in subscriptions[topic]:
            subscriptions[topic].remove(connection_id)

# Initialize connection manager
connection_manager = ConnectionManager()

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    connection_id = await connection_manager.connect(websocket)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connection_established",
            "connection_id": connection_id
        })
        
        # Handle messages
        while True:
            # Receive message
            message = await websocket.receive_text()
            
            try:
                # Parse message
                data = json.loads(message)
                message_type = data.get("type")
                
                # Handle different message types
                if message_type == "subscribe":
                    # Subscribe to a topic
                    topic = data.get("topic")
                    if topic:
                        await connection_manager.subscribe(connection_id, topic)
                        await websocket.send_json({
                            "type": "subscription_confirmed",
                            "topic": topic
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Missing topic in subscribe message"
                        })
                
                elif message_type == "unsubscribe":
                    # Unsubscribe from a topic
                    topic = data.get("topic")
                    if topic:
                        await connection_manager.unsubscribe(connection_id, topic)
                        await websocket.send_json({
                            "type": "unsubscription_confirmed",
                            "topic": topic
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Missing topic in unsubscribe message"
                        })
                
                elif message_type == "request":
                    # Process a request
                    action_str = data.get("action")
                    parameters = data.get("parameters", {})
                    request_id = data.get("request_id", str(uuid.uuid4()))
                    
                    if not action_str:
                        await websocket.send_json({
                            "type": "error",
                            "request_id": request_id,
                            "message": "Missing action in request message"
                        })
                        continue
                    
                    try:
                        # Convert action string to enum
                        action = ActionType(action_str)
                        
                        # Create and process request
                        request = AgentRequest(
                            action=action,
                            parameters=parameters,
                            request_id=request_id
                        )
                        
                        # Process request in a separate task to avoid blocking
                        asyncio.create_task(
                            process_request_ws(request, websocket, connection_id)
                        )
                        
                    except ValueError:
                        await websocket.send_json({
                            "type": "error",
                            "request_id": request_id,
                            "message": f"Invalid action: {action_str}"
                        })
                
                else:
                    # Unknown message type
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
            
            except json.JSONDecodeError:
                # Invalid JSON
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON message"
                })
            
            except Exception as e:
                # Other errors
                logger.error(f"Error processing WebSocket message: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                })
    
    except WebSocketDisconnect:
        # Client disconnected
        await connection_manager.disconnect(connection_id)
    
    except Exception as e:
        # Other errors
        logger.error(f"WebSocket error: {str(e)}")
        await connection_manager.disconnect(connection_id)

async def process_request_ws(request: AgentRequest, websocket: WebSocket, connection_id: str) -> None:
    """Process a request from a WebSocket client"""
    try:
        # Send processing message
        await websocket.send_json({
            "type": "processing",
            "request_id": request.request_id
        })
        
        # Process request (run in a thread pool to avoid blocking)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: agent_interface.process_request(request)
        )
        
        # Send response
        await websocket.send_json({
            "type": "response",
            "request_id": request.request_id,
            "success": response.success,
            "data": response.data,
            "error": response.error
        })
        
        # Notify subscribers if applicable
        if response.success:
            if request.action == ActionType.INDEX_PROJECT:
                await notify_subscribers("indexing_updates", {
                    "project_id": response.data.get("project_id"),
                    "status": response.data.get("status"),
                    "progress": response.data.get("progress")
                })
            
            elif request.action == ActionType.SEARCH_CODE:
                await notify_subscribers("search_updates", {
                    "query": request.parameters.get("query"),
                    "result_count": len(response.data.get("results", []))
                })
            
            elif request.action == ActionType.ANALYZE_CODE:
                await notify_subscribers("analysis_updates", {
                    "file_path": request.parameters.get("file_path"),
                    "analysis_type": "code_analysis"
                })
    
    except Exception as e:
        logger.error(f"Error processing WebSocket request: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "request_id": request.request_id,
            "message": f"Error processing request: {str(e)}"
        })

# Run the WebSocket server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)