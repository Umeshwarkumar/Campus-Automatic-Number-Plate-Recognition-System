import asyncio
from typing import List, Dict, Any

# In-memory storage for the latest 10 events
MAX_EVENTS = 10
recent_events: List[Dict[str, Any]] = []

# Queues for SSE broadcasting
log_queues: List[asyncio.Queue] = []
event_queues: List[asyncio.Queue] = []

def add_recent_event(event: Dict[str, Any]):
    global recent_events
    recent_events.insert(0, event)
    if len(recent_events) > MAX_EVENTS:
        recent_events = recent_events[:MAX_EVENTS]
    
    # Broadcast to all connected event clients
    for q in event_queues:
        q.put_nowait(event)

def add_log(message: str, level: str = "info"):
    log_data = {"message": message, "level": level}
    # Broadcast to all connected log clients
    for q in log_queues:
        q.put_nowait(log_data)
