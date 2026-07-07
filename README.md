# Campus ANPR System

## Overview

The Campus ANPR (Automatic Number Plate Recognition) System is a professional, AI-powered license plate detection and vehicle operations management platform. The system is designed for real-time license plate detection, vehicle identification, entry/exit logging, database querying, and dashboard operations. 

The application is composed of a FastAPI backend and a React dashboard frontend. The backend integrates with Supabase for data persistence and row-level security, utilizing an AI-based detection engine to verify license plates. An interactive AI data assistant allows administrators and operators to run natural language queries on vehicle activity.

### Optimization and Hardware Independence

The system has been optimized to run efficiently on CPU-only systems and does not require a dedicated GPU. While GPU acceleration can improve inference speed, the application performs well on modern CPUs. This design choice simplifies deployment on standard desktop and laptop hardware without necessitating specialized high-end graphics processing units.

---

## Features

- **Automatic Number Plate Recognition**: Real-time license plate detection and OCR-based recognition using deep learning models.
- **Entry and Exit Tracking**: Automatically determines vehicle status (entry/exit) based on gate sessions.
- **Vehicle Database Management**: Standard database structure to manage registered vehicles, owner details (students, staff, visitors), and active statuses.
- **Event History**: Log-based view tracking every detected plate, confidence level, camera location, and timestamp.
- **Operations Dashboard**: Real-time React dashboard displaying live video feeds, recent entry/exit events, system terminal logs, and the assistant.
- **SSE Real-Time Broadcasting**: Server-Sent Events (SSE) bridge backend events and logs directly to the frontend for zero-latency updates.
- **Interactive Data Assistant**: Bypasses complex database lookups by handling natural language commands for daily activity counts and current gate occupancies.
- **Camera Flexibility**: Supports both standard Webcams and network-based IP Cameras via RTSP stream decoding.
- **Configurable Detection Parameters**: Fine-tune accuracy thresholds, trigger streaks, and cooldown periods directly in the engine configuration.
- **CPU-Friendly Inference**: Optimized models built on ONNX Runtime for deployment on standard computer processors.
- **Role-Based Policies**: Supabase backend protected with Row Level Security (RLS) policies for administrators, operators, and viewers.

---

## Project Structure

The project repository is structured into the following key components:

- **backend/**: FastAPI application containing all server-side logic and camera processing loops.
  - **main.py**: Initializes the FastAPI app, manages CORSMiddleware, registers startup/shutdown events, exposes the MJPEG video feed, and configures SSE streams and query endpoints.
  - **anpr_engine.py**: Coordinates the camera stream ingestion and the ALPR prediction pipeline, implementing accuracy validation, streak confirmation, and file caching.
  - **supabase_client.py**: Configures the Supabase client wrapper and executes database queries, gate-session business logic, and event retrievals.
  - **llm_agent.py**: Houses the intent classification and response generation code for the natural language data assistant.
  - **state.py**: Manages global variables, SSE broadcast queues, and memory buffers.
- **frontend/**: React development workspace utilizing TypeScript, Vite, and Tailwind CSS.
  - **src/App.tsx**: Renders the main interface, handles API integrations, opens SSE streams, and controls full-screen camera toggles.
  - **src/components/**: Dashboard panels for layout structure:
    - **QuadrantLayout.tsx**: Grid layout engine supporting single-quadrant maximization.
    - **VideoFeedPanel.tsx**: Renders the live MJPEG camera feed and active status indicators.
    - **RecentActivityPanel.tsx**: Renders a table of the latest vehicle crossings.
    - **LiveLogsPanel.tsx**: Displays terminal logs streamed from the backend engine.
    - **AssistantPanel.tsx**: Prompts the user for queries, displays conversation state, and provides query suggestions.
- **Output_images/**: Runtime folder created automatically by the backend to store unannotated JPEG images of detected license plates.
- **start.sh**: Shell script to launch the backend and frontend servers concurrently.
- **ready.py**: Standalone Python script to verify webcam connectivity and local OCR engine parameters.
- **records.txt**: A local file documenting license plate details as a local failover.
- **IP camera-> copy-paste content from this to backend>anpr_engine.txt**: Camera source template code for IP camera streaming.
- **webcam-> copy-paste content from this to backend>anpr_engine.txt**: Camera source template code for local webcam capture.

---

## Requirements

The application requires the following software versions:

- **Python**: Version 3.10 or higher (Tested on Python 3.13.9)
- **Node.js**: Version 18.0.0 or higher (Tested on Node.js 20.20.2)
- **npm**: Version 10.0.0 or higher (Tested on npm 11.16.0)

---

## Installation

### 1. Clone the Repository

Clone the repository to your local machine:

```bash
git clone https://github.com/Umeshwarkumar/Campus-Automatic-Number-Plate-Recognition-System.git
cd 
Campus-Automatic-Number-Plate-Recognition-System
```

### 2. Install Python Backend Dependencies

Navigate to the `backend` directory, create a virtual environment, activate it, and install the required Python packages:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
cd ..
```

### 3. Install Frontend Dependencies

Navigate to the `frontend` directory and install the Node packages:

```bash
cd frontend
npm install
cd ..
```

### 4. Configure Environment Variables

Copy the provided example environment file to the backend directory and configure your keys:

```bash
cp .env.example backend/.env
```

Open `backend/.env` in a text editor and provide the correct Supabase credentials and API keys.

---

## Environment Variables

The application depends on configuration values defined in the environment. A template is provided in the root folder as `.env.example`. This file should be copied to the `backend` folder as `.env` (i.e., `backend/.env`).

The following variables must be configured:

- `SUPABASE_URL`: The URL endpoint of your Supabase project (e.g., `https://your-project.supabase.co`).
- `SUPABASE_KEY`: The public API key (anonymous or service role key) of your Supabase database.
- `XAI_API_KEY`: API key for xAI (Grok) to power the LLM Data Assistant queries.
- `OPENAI_API_KEY`: Optional fallback OpenAI API key.

---

## Camera Configuration

The application supports two input camera models. Two source code configuration files are provided in the root directory:

1. **Webcam Configuration**: `webcam-> copy-paste content from this to backend>anpr_engine.txt`
2. **IP Camera Configuration**: `IP camera-> copy-paste content from this to backend>anpr_engine.txt`

### Switching Configuration Modes

To switch between camera configurations:

1. Open the template file corresponding to your desired mode.
2. Copy the entire contents of the template file.
3. Paste the contents directly into `backend/anpr_engine.py`, overwriting the existing content.

### Webcam Mode

The webcam engine uses OpenCV to interface directly with a locally connected camera device index (`cv2.VideoCapture(0)`).

- **Advantages**:
  - Extremely easy to test and debug.
  - No additional external hardware required.
  - Portable and self-contained on laptops.
  - Ideal for demonstrations and local verification.

### IP Camera Mode

The IP camera engine resolves the stream resolution using `ffprobe` and initializes a subprocess running `ffmpeg` to capture raw video frames over TCP. This avoids buffer latency issues standard in default RTSP handlers.

- **Advantages**:
  - Designed for production-level deployments.
  - Allows precise camera positioning at facility gates.
  - Integrates with existing IP security camera and CCTV systems.
  - Supports remote network monitoring.
  - Offers higher installation and mounting flexibility.

---

## Detection Engine Configuration

The ANPR engine in `backend/anpr_engine.py` provides runtime parameters to adjust the sensitivity and accuracy of the detection system:

- **ACCURACY_THRESHOLD**: The confidence rating required to recognize a license plate character structure (default `0.93`).
  - *Higher value*: Restricts detections to high-quality frames, increasing precision and minimizing OCR misread errors.
  - *Lower value*: Allows the engine to log more plates under poor lighting or bad angles, though it increases the rate of minor false positives.
- **STREAK_REQUIRED**: The number of consecutive frames in which a license plate must be detected above the threshold before triggering a database action (default `3`).
  - *Higher value*: Filters out momentary false detections or background noise.
  - *Lower value*: Decreases detection latency for fast-moving vehicles.
- **COOLDOWN_DURATION**: The period in seconds during which the engine blocks duplicate detections of the same vehicle (default `5.0`).
  - *Purpose*: Prevents a stationary vehicle at a gate from spawning multiple back-to-back database logs.

These parameters can be edited directly in the source file `backend/anpr_engine.py` to match the specific deployment environment.

---

## Performance

The system is optimized for real-time license plate detection and OCR text extraction. The underlying inference engine, powered by ONNX Runtime, operates with the following performance characteristics:

- **Efficient CPU Performance**: The models are optimized for inference on modern x86 and ARM processors, allowing the system to run on standard desktop computers, mini-PCs, or laptops.
- **GPU Optionality**: High frame-rate performance is achievable on standard CPUs. While GPU acceleration is supported via CUDA, it is not required for standard entry/exit gates.
- **Deployment Scenarios**: The platform is suited for gate operations, commercial campuses, parking structures, and educational institutions with moderate traffic volume.
- **Lightweight Architecture**: Decoupling frame retrieval via FFmpeg subprocesses from FastAPI request handlers ensures the API remains responsive during peak workloads.

---

## Supabase Database Setup

This application depends on a strict Supabase database schema. Changing the schema without updating the application may cause runtime issues. Execute the SQL exactly as provided below. DO NOT modify anything.

```sql
create extension if not exists "uuid-ossp" with schema extensions;

create table if not exists public.profiles (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid unique references auth.users(id) on delete cascade,
  full_name text not null,
  role text not null default 'operator' check (role in ('admin', 'operator', 'viewer')),
  phone text,
  created_at timestamptz not null default now()
);

create table if not exists public.vehicles (
  id uuid primary key default uuid_generate_v4(),
  plate_number text not null unique,
  owner_name text,
  owner_type text default 'student' check (owner_type in ('student', 'staff', 'visitor', 'other')),
  department text,
  contact_number text,
  vehicle_type text,
  color text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.camera_events (
  id uuid primary key default uuid_generate_v4(),
  plate_number text not null,
  confidence numeric(5,4),
  event_type text not null default 'unknown' check (event_type in ('entry', 'exit', 'unknown')),
  camera_name text,
  image_url text,
  detected_at timestamptz not null default now(),
  created_by uuid references auth.users(id) on delete set null
);

create table if not exists public.gate_sessions (
  id uuid primary key default uuid_generate_v4(),
  vehicle_id uuid references public.vehicles(id) on delete set null,
  plate_number text not null,
  entry_event_id uuid references public.camera_events(id) on delete set null,
  exit_event_id uuid references public.camera_events(id) on delete set null,
  entry_time timestamptz,
  exit_time timestamptz,
  status text not null default 'inside' check (status in ('inside', 'exited', 'flagged')),
  notes text,
  created_at timestamptz not null default now()
);

create index if not exists idx_vehicles_plate_number on public.vehicles(plate_number);
create index if not exists idx_camera_events_plate_number on public.camera_events(plate_number);
create index if not exists idx_camera_events_detected_at on public.camera_events(detected_at desc);
create index if not exists idx_gate_sessions_plate_number on public.gate_sessions(plate_number);
create index if not exists idx_gate_sessions_status on public.gate_sessions(status);

alter table public.profiles enable row level security;
alter table public.vehicles enable row level security;
alter table public.camera_events enable row level security;
alter table public.gate_sessions enable row level security;

create policy "profiles read for authenticated"
on public.profiles
for select
to authenticated
using (true);

create policy "profiles insert self"
on public.profiles
for insert
to authenticated
with check (auth.uid() = user_id);

create policy "profiles update self"
on public.profiles
for update
to authenticated
using (auth.uid() = user_id);

create policy "vehicles read for authenticated"
on public.vehicles
for select
to authenticated
using (true);

create policy "vehicles write for authenticated"
on public.vehicles
for all
to authenticated
using (true)
with check (true);

create policy "camera_events read for authenticated"
on public.camera_events
for select
to authenticated
using (true);

create policy "camera_events insert for authenticated"
on public.camera_events
for insert
to authenticated
with check (true);

create policy "gate_sessions read for authenticated"
on public.gate_sessions
for select
to authenticated
using (true);

create policy "gate_sessions write for authenticated"
on public.gate_sessions
for all
to authenticated
using (true)
with check (true);
```

## Database Trigger

Paste the trigger SQL exactly as provided.

```sql
create extension if not exists moddatetime schema extensions;

drop trigger if exists handle_updated_at_vehicles on public.vehicles;

create trigger handle_updated_at_vehicles
before update on public.vehicles
for each row
execute procedure moddatetime (updated_at);
```

---

## Running the Project

### Using the Automated Startup Script

The application provides a bash script `start.sh` in the root folder that will start both servers in parallel. Run the following command from the root directory:

```bash
chmod +x start.sh
./start.sh
```

To stop all servers simultaneously, send an interrupt signal via `Ctrl+C`.

### Starting Components Manually

If you prefer to start the backend and frontend separately, follow these steps:

#### Start the FastAPI Backend

1. Navigate to the backend directory.
2. Activate the python virtual environment.
3. Start the server using Uvicorn.

```bash
cd backend
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Start the React Frontend

1. Navigate to the frontend directory.
2. Start the Vite development server.

```bash
cd frontend
npm run dev
```

The system will then be accessible at:
- **Dashboard**: `http://localhost:5173`
- **FastAPI API**: `http://localhost:8000`

---

## Technologies Used

- **Python**: Core programming language for backend operations.
- **FastAPI**: Asynchronous web framework for high-performance API endpoints.
- **Uvicorn**: ASGI web server implementation.
- **OpenCV**: Computer vision library for image operations and camera frame ingestion.
- **Ultralytics YOLO**: Used by the detection pipeline for license plate localization.
- **EasyOCR / Fast ALPR**: Extraction engines to perform optical character recognition.
- **Supabase**: Backend database service, security policies, and schema structures.
- **React**: Component-based UI library.
- **TypeScript**: Typed dialect of JavaScript for frontend stability.
- **Vite**: Frontend build system and hot-reloading development server.
- **Tailwind CSS**: Utility-first CSS styling engine.
- **Server-Sent Events (SSE)**: Unidirectional real-time connection from backend to frontend dashboard.
- **xAI API / OpenAI API**: Underlying LLM models powering the natural language query assistant.

---

## Notes

- **Webcam Support**: Readily configurable for local hardware testing.
- **IP Camera Support**: Fully configured FFmpeg receiver prevents RTSP lag.
- **CPU Optimization**: Inference models run via ONNX CPU providers.
- **Optional GPU**: Can be enabled by configuring CUDA execution providers.
- **Database Schema**: Hard dependency on the provided schema tables, triggers, and types.
- **API Keys**: Requires valid Supabase URL/keys and LLM endpoints to run without failures.
- **Production-Ready**: Employs reconnection locks, resource termination, and connection pools.

---

## License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
