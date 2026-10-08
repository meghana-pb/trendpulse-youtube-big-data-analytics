import React, { useEffect, useState } from 'react';
import { Card, Title, Text, Badge } from '@tremor/react';
import { Zap, AlertTriangle } from 'lucide-react';
import { getBreakoutVideos } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';

export default function BreakoutVideos() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getBreakoutVideos()
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorState error={error} retry={() => window.location.reload()} />;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Breakout Anomalies</h1>
        <p className="text-slate-500 mt-1">Videos exhibiting statistically significant anomalous behavior.</p>
      </div>

      {data.length === 0 ? (
        <Card className="bg-white ring-1 ring-slate-200 py-12 flex flex-col items-center justify-center">
          <Zap size={48} className="text-slate-300 mb-4" />
          <Title className="text-slate-500 text-xl font-medium">No Breakout Videos Detected</Title>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {data.map((video) => (
            <Card key={video.video_id} className="bg-white ring-1 ring-slate-200 hover:shadow-lg transition-all border-t-4 border-t-yellow-400">
              <div className="flex justify-between items-start mb-4">
                <Badge size="lg" color="yellow" icon={AlertTriangle}>
                  Anomaly Score: {video.anomaly_score.toFixed(1)}
                </Badge>
                <Badge color="slate">{video.category_name || 'Unknown'}</Badge>
              </div>
              
              <h3 className="font-bold text-lg text-slate-900 mb-4 line-clamp-2" title={video.title}>
                {video.title}
              </h3>
              
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                  <Text className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Views</Text>
                  <p className="font-bold text-slate-800 text-lg">{(video.views || 0).toLocaleString()}</p>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                  <Text className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Trending</Text>
                  <p className="font-bold text-slate-800 text-lg">{video.trending_duration_days} Days</p>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 col-span-2 flex items-center justify-between">
                  <Text className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Engagement Rate</Text>
                  <p className="font-bold text-blue-600 text-lg">{((video.engagement_rate || 0) * 100).toFixed(2)}%</p>
                </div>
              </div>
              
              <div>
                <Text className="text-sm font-semibold text-slate-700 mb-2">Detection Reasons:</Text>
                <div className="flex flex-wrap gap-2">
                  {video.anomaly_reasons?.map((reason, idx) => (
                    <span key={idx} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-700 border border-red-100">
                      {reason}
                    </span>
                  ))}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
