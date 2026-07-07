import { TerminalSquare, Trash2, Pause, Play } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import clsx from 'clsx';

export interface LogEntry {
  message: string;
  level: 'info' | 'warning' | 'error' | 'success';
  timestamp: string;
}

interface LiveLogsPanelProps {
  logs: LogEntry[];
  onClear: () => void;
}

export function LiveLogsPanel({ logs, onClear }: LiveLogsPanelProps) {
  const [autoScroll, setAutoScroll] = useState(true);
  const endOfLogsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && endOfLogsRef.current) {
      endOfLogsRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  return (
    <div className="flex flex-col h-full bg-[#0a0d16] rounded-xl shadow-lg border border-slate-800/80 overflow-hidden text-slate-300">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-[#101421]">
        <div className="flex items-center gap-2">
          <TerminalSquare className="w-5 h-5 text-slate-400" />
          <h2 className="font-semibold text-slate-200">Live Terminal</h2>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={() => setAutoScroll(!autoScroll)}
            className="p-1.5 rounded-md hover:bg-slate-800 text-slate-450 hover:text-slate-200 transition-colors"
            title={autoScroll ? "Pause scroll" : "Resume scroll"}
          >
            {autoScroll ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          <button 
            onClick={onClear}
            className="p-1.5 rounded-md hover:bg-slate-800 text-slate-450 hover:text-slate-200 transition-colors"
            title="Clear view"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      <div className="flex-1 overflow-auto p-4 font-mono text-xs leading-relaxed space-y-1.5">
        {logs.length === 0 ? (
          <div className="text-slate-500 italic">Waiting for backend logs...</div>
        ) : (
          logs.map((log, idx) => (
            <div key={idx} className="flex gap-3">
              <span className="text-slate-500 shrink-0 select-none">
                {new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 })}
              </span>
              <span className={clsx(
                "break-all",
                log.level === 'info' && "text-slate-300",
                log.level === 'warning' && "text-amber-300",
                log.level === 'error' && "text-red-400",
                log.level === 'success' && "text-emerald-400 font-semibold",
              )}>
                {log.message}
              </span>
            </div>
          ))
        )}
        <div ref={endOfLogsRef} />
      </div>
    </div>
  );
}
