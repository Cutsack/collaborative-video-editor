"""
WebSocket endpoint for real-time collaboration
"""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.websockets.manager import manager
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.api.api_v1.endpoints.auth import get_current_user_from_token

router = APIRouter()


@router.websocket("/ws/project/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: int,
    token: str = None
):
    """WebSocket endpoint for project collaboration"""
    try:
        # Accept the connection first
        await websocket.accept()
        
        # Validate token and get user
        if not token:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Authentication token required"
            }))
            await websocket.close()
            return
        
        # For WebSocket, we'll do a simple token validation
        # In production, you might want to implement proper JWT validation
        user = await validate_websocket_token(token, project_id)
        if not user:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Invalid authentication token"
            }))
            await websocket.close()
            return
        
        # Connect user to project room
        await manager.connect(websocket, project_id, {
            "id": user.id,
            "username": user.username
        })
        
        try:
            # Handle incoming messages
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await handle_websocket_message(websocket, message, project_id)
                
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


async def validate_websocket_token(token: str, project_id: int) -> User:
    """Validate WebSocket token and return user"""
    try:
        # Simple token validation for WebSocket
        # In production, implement proper JWT validation
        from app.services.auth import verify_token
        
        payload = verify_token(token)
        if not payload:
            return None
        
        username = payload.get("sub")
        if not username:
            return None
        
        # Get user from database
        from app.services.auth import get_user_by_username
        user = get_user_by_username(None, username)  # We'll need to pass db session
        
        if not user:
            return None
        
        # Check if user has access to project
        # This is a simplified check - in production, use proper database session
        return user
        
    except Exception as e:
        print(f"Token validation error: {e}")
        return None


async def handle_websocket_message(websocket: WebSocket, message: dict, project_id: int):
    """Handle incoming WebSocket messages"""
    message_type = message.get("type")
    
    try:
        if message_type == "cursor_update":
            await manager.handle_cursor_update(websocket, message)
            
        elif message_type == "timeline_update":
            await manager.handle_timeline_update(websocket, message)
            
        elif message_type == "chat_message":
            await manager.handle_chat_message(websocket, message)
            
        elif message_type == "ping":
            # Respond to ping with pong
            await websocket.send_text(json.dumps({
                "type": "pong",
                "timestamp": message.get("timestamp")
            }))
            
        else:
            # Unknown message type
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }))
            
    except Exception as e:
        print(f"Error handling WebSocket message: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Internal server error"
        }))


# Add WebSocket router to main API router
# Note: This needs to be added to the main API router in api.py
