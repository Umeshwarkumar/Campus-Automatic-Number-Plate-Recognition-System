import { Activity, CarFront, LogIn, LogOut } from 'lucide-react';
import clsx from 'clsx';
import { useEffect, useState } from 'react';

export interface VehicleEvent {
  timestamp: string;
  plate_number: string;
  confidence: number;
  direction: 'IN' | 'OUT';
  vehicle_name: string;
}

interface RecentActivityPanelProps {
  events: VehicleEvent[];
}

export function RecentActivityPanel({ events }: RecentActivityPanelProps) {
  return (
    <div className="flex flex-col h-full bg-[#101624] rounded-xl shadow-lg border border-slate-800/80 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800/80 bg-[#161e31]">
        <Activity className="w-5 h-5 text-slate-400" />
        <h2 className="font-semibold text-slate-200">Recent Activity</h2>
      </div>
      
      <div className="flex-1 overflow-auto p-2">
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <CarFront className="w-10 h-10 mb-2 opacity-55" />
            <p className="text-sm">No recent activity</p>
          </div>
        ) : (
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-450 uppercase bg-[#161e31] sticky top-0">
              <tr>
                <th className="px-4 py-2.5 font-semibold rounded-tl-lg">Time</th>
                <th className="px-4 py-2.5 font-semibold">Plate</th>
                <th className="px-4 py-2.5 font-semibold">Name</th>
                <th className="px-4 py-2.5 font-semibold rounded-tr-lg">Dir</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event, idx) => (
                <tr 
                  key={`${event.timestamp}-${idx}`} 
                  className={clsx(
                    "border-b border-slate-800/60 last:border-0 hover:bg-slate-800/30 transition-colors",
                    idx === 0 && "bg-slate-800/40 animate-pulse" // Subtle highlight for newest
                  )}
                >
                  <td className="px-4 py-3 text-slate-400 font-mono text-xs whitespace-nowrap">
                    {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </td>
                  <td className="px-4 py-3 font-semibold text-slate-100 font-mono">
                    {event.plate_number}
                  </td>
                  <td className="px-4 py-3 text-slate-300 truncate max-w-[120px]">
                    {event.vehicle_name}
                  </td>
                  <td className="px-4 py-3">
                    <span className={clsx(
                      "inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold uppercase tracking-wider",
                      event.direction === 'IN' 
                        ? "bg-emerald-950/40 text-emerald-400 border border-emerald-800/40" 
                        : "bg-amber-950/40 text-amber-400 border border-amber-800/40"
                    )}>
                      {event.direction === 'IN' ? <LogIn className="w-3 h-3" /> : <LogOut className="w-3 h-3" />}
                      {event.direction}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
