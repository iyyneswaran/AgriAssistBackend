from fastapi import WebSocket
from typing import Dict, Set
import asyncio


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Set[str]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, user_id: str, session_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active_connections[session_id] = websocket
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = set()
            self.user_sessions[user_id].add(session_id)

    async def disconnect(self, user_id: str, session_id: str):
        async with self.lock:
            if session_id in self.active_connections:
                del self.active_connections[session_id]

            if user_id in self.user_sessions:
                self.user_sessions[user_id].discard(session_id)
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]

    async def send_personal_message(self, session_id: str, message: dict):
        websocket = self.active_connections.get(session_id)
        if websocket:
            await websocket.send_json(message)

    async def broadcast_to_user(self, user_id: str, message: dict):
        sessions = self.user_sessions.get(user_id, set())
        for session_id in sessions:
            await self.send_personal_message(session_id, message)


manager = ConnectionManager()
