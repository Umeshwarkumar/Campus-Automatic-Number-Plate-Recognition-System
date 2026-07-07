import { Camera, AlertCircle, Maximize2, Minimize2 } from 'lucide-react';
import clsx from 'clsx';

interface VideoFeedPanelProps {
  streamUrl: string;
  isMaximized?: boolean;
}

export function VideoFeedPanel({ streamUrl, isMaximized = false }: VideoFeedPanelProps) {
  return (
    <div className="flex flex-col h-full bg-[#101624] rounded-xl shadow-lg border border-slate-800/80 overflow-hidden hover:border-slate-700/80 hover:shadow-xl transition-all duration-300">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800/80 bg-[#161e31]">
        <div className="flex items-center gap-2">
          <Camera className="w-5 h-5 text-slate-400" />
          <h2 className="font-semibold text-slate-200">Live Gate Feed</h2>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <span className="text-xs font-semibold text-emerald-400">Active</span>
          </div>
          <div className="text-slate-400 hover:text-slate-200 transition-colors pl-1">
            {isMaximized ? (
              <Minimize2 className="w-4 h-4" title="Minimize" />
            ) : (
              <Maximize2 className="w-4 h-4" title="Maximize" />
            )}
          </div>
        </div>
      </div>
      <div className="flex-1 bg-slate-900 relative min-h-0 flex items-center justify-center">
        <img
          src={streamUrl}
          alt="Live Stream"
          className="w-full h-full object-contain"
          onError={(e) => {
            e.currentTarget.style.display = 'none';
          }}
        />
        <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400 pointer-events-none -z-10">
          <AlertCircle className="w-12 h-12 mb-3 opacity-50" />
          <p className="text-sm font-medium">Camera Offline</p>
          <p className="text-xs opacity-75 mt-1">Waiting for feed...</p>
        </div>
      </div>
    </div>
  );
}
