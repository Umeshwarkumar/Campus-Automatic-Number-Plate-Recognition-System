import os
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")

COOLDOWN_SECONDS = 20

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def parse_iso_datetime(dt_str):
    if dt_str.endswith("Z"):
        dt_str = dt_str.replace("Z", "+00:00")
    return datetime.fromisoformat(dt_str)

def find_latest_camera_event(plate_number):
    if not supabase: return None
    plate = plate_number.strip().upper()
    response = (
        supabase.table("camera_events")
        .select("*")
        .eq("plate_number", plate)
        .order("detected_at", desc=True)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None

def is_in_cooldown(plate_number, cooldown_seconds=COOLDOWN_SECONDS):
    latest_event = find_latest_camera_event(plate_number)
    if not latest_event:
        return False, None

    latest_time = parse_iso_datetime(latest_event["detected_at"])
    now_time = datetime.now(timezone.utc)
    diff_seconds = (now_time - latest_time).total_seconds()

    if diff_seconds < cooldown_seconds:
        return True, latest_event

    return False, latest_event

def find_vehicle_by_plate(plate_number):
    if not supabase: return None
    plate = plate_number.strip().upper()
    response = (
        supabase.table("vehicles")
        .select("*")
        .eq("plate_number", plate)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None

def log_camera_event(
    plate_number,
    confidence=None,
    event_type="unknown",
    camera_name=None,
    image_url=None,
    created_by=None
):
    if not supabase: return None
    payload = {
        "plate_number": plate_number.strip().upper(),
        "confidence": confidence,
        "event_type": event_type,
        "camera_name": camera_name,
        "image_url": image_url,
        "detected_at": utc_now(),
        "created_by": created_by
    }

    response = (
        supabase.table("camera_events")
        .insert(payload)
        .select("*")
        .execute()
    )
    return response.data[0] if response.data else None

def find_open_gate_session(plate_number):
    if not supabase: return None
    plate = plate_number.strip().upper()
    response = (
        supabase.table("gate_sessions")
        .select("*")
        .eq("plate_number", plate)
        .eq("status", "inside")
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None

def create_gate_entry_session(plate_number, vehicle_id=None, entry_event_id=None):
    if not supabase: return None
    payload = {
        "vehicle_id": vehicle_id,
        "plate_number": plate_number.strip().upper(),
        "entry_event_id": entry_event_id,
        "entry_time": utc_now(),
        "status": "inside"
    }

    response = (
        supabase.table("gate_sessions")
        .insert(payload)
        .select("*")
        .execute()
    )
    return response.data[0] if response.data else None

def close_gate_session(session_id, exit_event_id=None):
    if not supabase: return None
    payload = {
        "exit_event_id": exit_event_id,
        "exit_time": utc_now(),
        "status": "exited"
    }

    response = (
        supabase.table("gate_sessions")
        .update(payload)
        .eq("id", session_id)
        .select("*")
        .execute()
    )
    return response.data[0] if response.data else None

def process_plate_event(
    plate_number,
    confidence=None,
    camera_name=None,
    image_url=None,
    created_by=None,
    cooldown_seconds=COOLDOWN_SECONDS
):
    if not supabase:
        return {"action": "error", "message": "Supabase not configured"}

    plate = plate_number.strip().upper()

    cooldown_hit, latest_event = is_in_cooldown(plate, cooldown_seconds)
    if cooldown_hit:
        return {
            "action": "cooldown_skipped",
            "vehicle_found": find_vehicle_by_plate(plate) is not None,
            "latest_event": latest_event,
            "message": f"Duplicate scan ignored within {cooldown_seconds} seconds"
        }

    vehicle = find_vehicle_by_plate(plate)
    open_session = find_open_gate_session(plate)

    event_type = "entry" if open_session is None else "exit"

    camera_event = log_camera_event(
        plate_number=plate,
        confidence=confidence,
        event_type=event_type,
        camera_name=camera_name,
        image_url=image_url,
        created_by=created_by
    )

    if open_session is None:
        session = create_gate_entry_session(
            plate_number=plate,
            vehicle_id=vehicle["id"] if vehicle else None,
            entry_event_id=camera_event["id"] if camera_event else None
        )
        return {
            "action": "entry_created",
            "vehicle_found": vehicle is not None,
            "vehicle": vehicle,
            "camera_event": camera_event,
            "gate_session": session
        }
    else:
        session = close_gate_session(
            session_id=open_session["id"],
            exit_event_id=camera_event["id"] if camera_event else None
        )
        return {
            "action": "exit_closed",
            "vehicle_found": vehicle is not None,
            "vehicle": vehicle,
            "camera_event": camera_event,
            "gate_session": session
        }

def run_query(intent: str) -> dict:
    """
    Executes specific allowed queries based on recognized intent mapping to new schema.
    """
    if not supabase:
        return {"error": "Supabase not configured."}
    
    try:
        if intent == "COUNT_TODAY":
            # Using current UTC day broadly
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            res = supabase.table("gate_sessions").select("*", count="exact").gte("entry_time", today).execute()
            return {"count": getattr(res, 'count', len(res.data) if res.data else 0)}
        elif intent == "COUNT_INSIDE":
            res = supabase.table("gate_sessions").select("*, vehicles(*)").eq("status", "inside").execute()
            return {"records": res.data}
        elif intent == "RECENT_IN":
            res = supabase.table("camera_events").select("*").eq("event_type", "entry").order("detected_at", desc=True).limit(5).execute()
            return {"records": res.data}
        elif intent == "RECENT_OUT":
            res = supabase.table("camera_events").select("*").eq("event_type", "exit").order("detected_at", desc=True).limit(5).execute()
            return {"records": res.data}
        else:
            return {"error": "Unknown intent"}
    except Exception as e:
        return {"error": str(e)}

def get_recent_events_from_db(limit=10) -> list:
    if not supabase:
        return []
    try:
        response = (
            supabase.table("camera_events")
            .select("*")
            .order("detected_at", desc=True)
            .limit(limit)
            .execute()
        )
        events = []
        for row in response.data:
            plate = row["plate_number"]
            vehicle = find_vehicle_by_plate(plate)
            v_name = vehicle["owner_name"] if vehicle else "Guest"
            direction = "IN" if row["event_type"] == "entry" else "OUT"
            
            events.append({
                "timestamp": row["detected_at"],
                "plate_number": plate,
                "confidence": row["confidence"],
                "direction": direction,
                "vehicle_name": v_name,
                "local_image_path": row["image_url"]
            })
        return events
    except Exception as e:
        print(f"Error fetching recent events from DB: {e}")
        return []
