"""
Real-Time Collaboration for DataLineagePy
Provides a simple WebSocket-based server and client for collaborative lineage editing and viewing.
"""
import asyncio
import json
import websockets
from typing import Dict, Any, Set


class CollaborationServer:
    """WebSocket server for real-time lineage collaboration."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.lineage_state: Dict[str, Any] = {}

    async def handler(self, websocket, path):
        self.clients.add(websocket)
        try:
            await websocket.send(json.dumps({"type": "init", "state": self.lineage_state}))
            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "update":
                    self.lineage_state = data["state"]
                    await self.broadcast(json.dumps({"type": "update", "state": self.lineage_state}))
        finally:
            self.clients.remove(websocket)

    async def broadcast(self, message: str):
        for client in self.clients:
            await client.send(message)

    def run(self):
        asyncio.get_event_loop().run_until_complete(
            websockets.serve(self.handler, self.host, self.port)
        )
        print(f"Collaboration server running at ws://{self.host}:{self.port}")
        asyncio.get_event_loop().run_forever()


class CollaborationClient:
    """WebSocket client for real-time lineage collaboration."""

    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.state: Dict[str, Any] = {}

    async def connect(self):
        async with websockets.connect(self.uri) as websocket:
            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "init":
                    self.state = data["state"]
                    print("Initial state received:", self.state)
                elif data.get("type") == "update":
                    self.state = data["state"]
                    print("State updated:", self.state)

    def run(self):
        asyncio.get_event_loop().run_until_complete(self.connect())
