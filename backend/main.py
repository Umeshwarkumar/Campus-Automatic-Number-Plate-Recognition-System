import asyncio
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import json

from backend.anpr_engine import anpr_engine
from backend.state import log_queues, event_queues, recent_events
from backend.llm_agent import classify_intent, generate_reply
from backend.supabase_client import run_query

app = FastAPI(title="ANPR Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Pre-populate recent events list from Supabase
    from backend.supabase_client import get_recent_events_from_db
    db_events = get_recent_events_from_db(10)
    recent_events.clear()
    for event in db_events:
        recent_events.append(event)
    anpr_engine.start()

@app.on_event("shutdown")
async def shutdown_event():
    anpr_engine.stop()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/video-feed")
async def video_feed():
    def frame_generator():
        while True:
            frame = anpr_engine.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                asyncio.run(asyncio.sleep(0.05))

    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/logs/stream")
async def logs_stream(request: Request):
    queue = asyncio.Queue()
    log_queues.append(queue)
    
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await queue.get()
                yield {"data": json.dumps(data)}
        finally:
            log_queues.remove(queue)
            
    return EventSourceResponse(event_generator())

@app.get("/events/stream")
async def events_stream(request: Request):
    queue = asyncio.Queue()
    event_queues.append(queue)
    
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await queue.get()
                yield {"data": json.dumps(data)}
        finally:
            event_queues.remove(queue)
            
    return EventSourceResponse(event_generator())

@app.get("/events/recent")
def get_recent_events():
    from backend.supabase_client import get_recent_events_from_db
    db_events = get_recent_events_from_db(10)
    recent_events.clear()
    for event in db_events:
        recent_events.append(event)
    return {"events": recent_events}

class QueryRequest(BaseModel):
    message: str

@app.post("/query")
def handle_query(request: QueryRequest):
    intent = classify_intent(request.message)
    if intent == "UNKNOWN":
        return {"intent": intent, "reply": "I couldn't understand that. Try asking about recent vehicles or today's count."}
    
    data = run_query(intent)
    reply = generate_reply(intent, data)
    
    return {
        "intent": intent,
        "data": data,
        "reply": reply
    }
