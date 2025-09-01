"""
WebSocket manager for real-time collaboration
"""

import json
import asyncio
from typing import Dict, List, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.project import Project


class ConnectionManager:
    """Manages WebSocket connections for real-time collaboration"""
    
    def __init__(self):
        # Store active connections by project_id
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Store user info for each connection
        self.connection_users: Dict[WebSocket, dict] = {}
        # Store cursor positions for each user
        self.user_cursors: Dict[int, Dict[int, dict]] = {}  # project_id -> user_id -> cursor_data
    
    async def connect(self, websocket: WebSocket, project_id: int, user: dict):
        """Connect a user to a project room"""
        await websocket.accept()
        
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
            self.user_cursors[project_id] = {}
        
        self.active_connections[project_id].append(websocket)
        self.connection_users[websocket] = {
            "user_id": user["id"],
            "username": user["username"],
            "project_id": project_id
        }
        
        # Initialize user cursor
        self.user_cursors[project_id][user["id"]] = {
            "x": 0,
            "y": 0,
            "username": user["username"],
            "color": self._generate_user_color(user["id"])
        }
        
        # Notify others that user joined
        await self.broadcast_to_project(
            project_id,
            {
                "type": "user_joined",
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "cursor": self.user_cursors[project_id][user["id"]]
                }
            },
            exclude_websocket=websocket
        )
        
        # Send current project state to new user
        await self.send_personal_message(
            websocket,
            {
                "type": "project_state",
                "active_users": [
                    {
                        "id": uid,
                        "username": cursor_data["username"],
                        "cursor": cursor_data
                    }
                    for uid, cursor_data in self.user_cursors[project_id].items()
                ]
            }
        )
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a user from a project room"""
        if websocket in self.connection_users:
            user_info = self.connection_users[websocket]
            project_id = user_info["project_id"]
            user_id = user_info["user_id"]
            
            # Remove from active connections
            if project_id in self.active_connections:
                self.active_connections[project_id].remove(websocket)
                if not self.active_connections[project_id]:
                    del self.active_connections[project_id]
                    del self.user_cursors[project_id]
            
            # Remove user cursor
            if project_id in self.user_cursors and user_id in self.user_cursors[project_id]:
                del self.user_cursors[project_id][user_id]
            
            # Remove from connection users
            del self.connection_users[websocket]
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send a message to a specific user"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Error sending personal message: {e}")
    
    async def broadcast_to_project(self, project_id: int, message: dict, exclude_websocket: WebSocket = None):
        """Broadcast a message to all users in a project"""
        if project_id not in self.active_connections:
            return
        
        disconnected_websockets = []
        
        for websocket in self.active_connections[project_id]:
            if websocket == exclude_websocket:
                continue
            
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error broadcasting message: {e}")
                disconnected_websockets.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            self.disconnect(websocket)
    
    async def handle_cursor_update(self, websocket: WebSocket, data: dict):
        """Handle cursor position updates from users"""
        if websocket not in self.connection_users:
            return
        
        user_info = self.connection_users[websocket]
        project_id = user_info["project_id"]
        user_id = user_info["user_id"]
        
        # Update cursor position
        if project_id in self.user_cursors and user_id in self.user_cursors[project_id]:
            self.user_cursors[project_id][user_id].update({
                "x": data.get("x", 0),
                "y": data.get("y", 0),
                "timestamp": data.get("timestamp")
            })
            
            # Broadcast cursor update to other users
            await self.broadcast_to_project(
                project_id,
                {
                    "type": "cursor_update",
                    "user_id": user_id,
                    "cursor": self.user_cursors[project_id][user_id]
                },
                exclude_websocket=websocket
            )
    
    async def handle_timeline_update(self, websocket: WebSocket, data: dict):
        """Handle timeline updates from users"""
        if websocket not in self.connection_users:
            return
        
        user_info = self.connection_users[websocket]
        project_id = user_info["project_id"]
        
        # Broadcast timeline update to other users
        await self.broadcast_to_project(
            project_id,
            {
                "type": "timeline_update",
                "user_id": user_info["user_id"],
                "data": data
            },
            exclude_websocket=websocket
        )
    
    async def handle_chat_message(self, websocket: WebSocket, data: dict):
        """Handle chat messages from users"""
        if websocket not in self.connection_users:
            return
        
        user_info = self.connection_users[websocket]
        project_id = user_info["project_id"]
        
        # Broadcast chat message to all users in project
        await self.broadcast_to_project(
            project_id,
            {
                "type": "chat_message",
                "user_id": user_info["user_id"],
                "username": user_info["username"],
                "message": data.get("message", ""),
                "timestamp": data.get("timestamp")
            }
        )
    
    def _generate_user_color(self, user_id: int) -> str:
        """Generate a consistent color for a user"""
        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
            "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"
        ]
        return colors[user_id % len(colors)]


# Global connection manager instance
manager = ConnectionManager()
