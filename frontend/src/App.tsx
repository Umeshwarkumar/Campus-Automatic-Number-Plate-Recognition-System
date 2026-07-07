import { useEffect, useState } from 'react';
import { QuadrantLayout } from './components/QuadrantLayout';
import { VideoFeedPanel } from './components/VideoFeedPanel';
import { RecentActivityPanel } from './components/RecentActivityPanel';
import type { VehicleEvent } from './components/RecentActivityPanel';
import { LiveLogsPanel } from './components/LiveLogsPanel';
import type { LogEntry } from './components/LiveLogsPanel';
import { AssistantPanel } from './components/AssistantPanel';
import { ShieldCheck } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [events, setEvents] = useState<VehicleEvent[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isCameraMaximized, setIsCameraMaximized] = useState(false);

  // Fetch initial recent events
  useEffect(() => {
    fetch(`${API_BASE}/events/recent`)
      .then(res => res.json())
      .then(data => {
        if (data.events) {
          setEvents(data.events);
        }
      })
      .catch(err => console.error("Failed to fetch initial events", err));
  }, []);

  // Subscribe to SSE
  useEffect(() => {
    const eventsSource = new EventSource(`${API_BASE}/events/stream`);
    eventsSource.onmessage = (e) => {
      try {
        const newEvent = JSON.parse(e.data);
        setEvents(prev => {
          const updated = [newEvent, ...prev];
          return updated.slice(0, 10);
        });
      } catch (err) {
        console.error("Error parsing event", err);
      }
    };

    const logsSource = new EventSource(`${API_BASE}/logs/stream`);
    logsSource.onmessage = (e) => {
      try {
        const logData = JSON.parse(e.data);
        const newLog: LogEntry = {
          message: logData.message,
          level: logData.level || 'info',
          timestamp: new Date().toISOString()
        };
        setLogs(prev => [...prev.slice(-99), newLog]); // Keep max 100 logs
      } catch (err) {
        console.error("Error parsing log", err);
      }
    };

    return () => {
      eventsSource.close();
      logsSource.close();
    };
  }, []);

  const handleQuery = async (query: string) => {
    const res = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: query })
    });
    if (!res.ok) throw new Error("Query failed");
    return res.json();
  };

  return (
    <div className="min-h-screen bg-[#080b11] flex flex-col font-sans text-slate-100">
      <header className="h-16 bg-[#0f1420] border-b border-slate-800/80 px-6 flex items-center justify-between shrink-0 sticky top-0 z-10 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-600 p-2 rounded-lg">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-slate-100 text-lg leading-tight">Campus Operations Center</h1>
            <p className="text-xs text-indigo-400 font-semibold tracking-wide uppercase">Real-Time ANPR Dashboard</p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-sm font-medium">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-950/30 rounded-full border border-emerald-800/50">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-emerald-400 font-semibold">System Online</span>
          </div>
        </div>
      </header>
      
      <main className="flex-1 flex flex-col bg-[#080b11]">
        <QuadrantLayout
          topLeft={<VideoFeedPanel streamUrl={`${API_BASE}/video-feed`} isMaximized={isCameraMaximized} />}
          topRight={<RecentActivityPanel events={events} />}
          bottomLeft={<LiveLogsPanel logs={logs} onClear={() => setLogs([])} />}
          bottomRight={<AssistantPanel onQuery={handleQuery} />}
          isCameraMaximized={isCameraMaximized}
          onToggleMaximize={() => setIsCameraMaximized(!isCameraMaximized)}
        />
      </main>
    </div>
  );
}

export default App;
