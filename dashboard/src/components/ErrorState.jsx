import React from 'react';
import { AlertCircle } from 'lucide-react';

export default function ErrorState({ error, retry }) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[400px] p-6 bg-red-50 rounded-xl border border-red-100">
      <AlertCircle className="text-red-500 mb-4" size={48} />
      <h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading Data</h3>
      <p className="text-red-600 text-center max-w-md mb-6">{error?.message || 'An unexpected error occurred.'}</p>
      {retry && (
        <button 
          onClick={retry}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
