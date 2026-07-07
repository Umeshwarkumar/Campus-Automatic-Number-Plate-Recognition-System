import { ReactNode } from 'react';
import clsx from 'clsx';

interface QuadrantLayoutProps {
  topLeft: ReactNode;
  topRight: ReactNode;
  bottomLeft: ReactNode;
  bottomRight: ReactNode;
  isCameraMaximized: boolean;
  onToggleMaximize: () => void;
}

export function QuadrantLayout({ 
  topLeft, 
  topRight, 
  bottomLeft, 
  bottomRight,
  isCameraMaximized,
  onToggleMaximize
}: QuadrantLayoutProps) {
  return (
    <div className={clsx(
      "gap-4 h-[calc(100vh-4rem)] p-4 max-w-[1600px] mx-auto w-full",
      isCameraMaximized 
        ? "block" 
        : "grid grid-cols-1 lg:grid-cols-2 grid-rows-[minmax(0,1fr)_minmax(0,1fr)]"
    )}>
      <div 
        className="min-h-0 h-full cursor-pointer" 
        onClick={onToggleMaximize}
      >
        {topLeft}
      </div>
      <div className={clsx("min-h-0 h-full", isCameraMaximized && "hidden")}>
        {topRight}
      </div>
      <div className={clsx("min-h-0 h-full", isCameraMaximized && "hidden")}>
        {bottomLeft}
      </div>
      <div className={clsx("min-h-0 h-full", isCameraMaximized && "hidden")}>
        {bottomRight}
      </div>
    </div>
  );
}
