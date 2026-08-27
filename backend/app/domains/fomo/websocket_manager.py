"""
WebSocket Manager: Real-time social proof + metrics broadcast
Connects landing visitors, dashboard users, admin panel
"""

import asyncio
import json
from typing import Dict, Set
from datetime import datetime, timezone
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.landing_connections: Set[WebSocket] = set()
        self.dashboard_connections: Dict[str, WebSocket] = {}
        self.metrics = {
            "total_visitors": 15340,
            "seats_taken": 47,
            "total_revenue": 2300000,
            "active_users": 280,
        }
        self.proof_events: list = []

    async def connect_landing(self, websocket: WebSocket):
        await websocket.accept()
        self.landing_connections.add(websocket)
        self.metrics["total_visitors"] += 1

    async def disconnect_landing(self, websocket: WebSocket):
        self.landing_connections.discard(websocket)

    async def connect_dashboard(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.dashboard_connections[user_id] = websocket

    async def disconnect_dashboard(self, user_id: str):
        self.dashboard_connections.pop(user_id, None)

    async def broadcast_landing(self, data: dict):
        dead = set()
        for conn in self.landing_connections:
            try:
                await conn.send_json(data)
            except:
                dead.add(conn)
        for c in dead:
            self.landing_connections.discard(c)

    async def broadcast_dashboard(self, data: dict, user_id: str = None):
        targets = {user_id: self.dashboard_connections[user_id]} if user_id else self.dashboard_connections
        dead = set()
        for uid, conn in targets.items():
            try:
                await conn.send_json(data)
            except:
                dead.add(uid)
        for uid in dead:
            self.dashboard_connections.pop(uid, None)

    async def broadcast_all(self, data: dict):
        await self.broadcast_landing(data)
        await self.broadcast_dashboard(data)


manager = ConnectionManager()


async def generate_proof_events():
    """Generate synthetic social proof every 3-7 seconds"""
    import random

    event_templates = [
        {"type": "signup", "metric": "se registró", "amount": 0},
        {"type": "purchase", "metric": "hizo una compra 🎉", "amount": 99},
        {"type": "milestone", "metric": "cerró su primera venta", "amount": 0},
        {"type": "purchase", "metric": "compró Plan Pro", "amount": 149},
    ]

    names = ["Juan", "María", "Carlos", "Ana", "Luis", "Sofia", "Roberto", "Paula"]
    cities = ["Buenos Aires", "Madrid", "México", "Bogotá", "Lima", "Santiago"]

    while True:
        try:
            await asyncio.sleep(random.randint(3, 7))

            event_template = random.choice(event_templates)
            name = random.choice(names)
            city = random.choice(cities)

            proof_event = {
                "id": str(UUID(int=random.getrandbits(128))),
                "type": event_template["type"],
                "user_name": f"{name} ({city})",
                "metric": event_template["metric"],
                "amount": event_template["amount"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "seats_taken": manager.metrics["seats_taken"],
                "total_revenue": manager.metrics["total_revenue"],
            }

            if event_template["amount"] > 0:
                manager.metrics["seats_taken"] += 1
                manager.metrics["total_revenue"] += event_template["amount"]

            await manager.broadcast_all(proof_event)

        except Exception as e:
            print(f"Error: {e}")


@router.websocket("/ws/landing-proof")
async def websocket_landing_proof(websocket: WebSocket):
    await manager.connect_landing(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect_landing(websocket)


@router.websocket("/ws/dashboard/{user_id}")
async def websocket_dashboard(websocket: WebSocket, user_id: str):
    await manager.connect_dashboard(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
    except WebSocketDisconnect:
        await manager.disconnect_dashboard(user_id)


@router.post("/proof-events/manual")
async def trigger_manual_proof_event(
    event_type: str,
    user_name: str,
    metric: str,
    amount: float = 0,
):
    proof_event = {
        "id": str(UUID(int=asyncio.get_event_loop().time() * 1000)),
        "type": event_type,
        "user_name": user_name,
        "metric": metric,
        "amount": amount,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seats_taken": manager.metrics["seats_taken"],
        "total_revenue": manager.metrics["total_revenue"],
    }

    await manager.broadcast_all(proof_event)
    return proof_event


async def start_proof_generation():
    asyncio.create_task(generate_proof_events())
