import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ message = 'Loading data...' }) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-slate-500">
      <Loader2 className="animate-spin mb-4" size={40} />
      <p className="font-medium animate-pulse">{message}</p>
    </div>
  );
}
