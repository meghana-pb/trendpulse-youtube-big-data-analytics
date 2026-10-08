import React, { useEffect, useState } from 'react';
import { Card, Title, Text, Table, TableHead, TableRow, TableHeaderCell, TableBody, TableCell, Badge, TextInput } from '@tremor/react';
import { Search } from 'lucide-react';
import { getVideos } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';

export default function VideoExplorer() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const fetchData = (searchTerm = "", pageNum = 1) => {
    setLoading(true);
    getVideos({ search: searchTerm, page: pageNum, page_size: 15, sort_by: 'trendpulse_score', sort_dir: 'desc' })
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchData(search, page);
  }, [page]);

  const handleSearch = (e) => {
    if (e.key === 'Enter') {
      setPage(1);
      fetchData(search, 1);
    }
  };

  if (error) return <ErrorState error={error} retry={() => fetchData(search, page)} />;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Video Explorer</h1>
          <p className="text-slate-500 mt-1">Search and analyze individual video performance.</p>
        </div>
        <div className="w-full md:w-72 relative">
          <TextInput 
            icon={Search} 
            placeholder="Search by title..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={handleSearch}
          />
        </div>
      </div>

      <Card className="bg-white ring-1 ring-slate-200">
        {loading && !data ? (
          <div className="h-96 flex items-center justify-center"><LoadingSpinner message="Searching..." /></div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHead className="bg-slate-50">
                  <TableRow>
                    <TableHeaderCell>Title / Channel</TableHeaderCell>
                    <TableHeaderCell>Category</TableHeaderCell>
                    <TableHeaderCell>Views</TableHeaderCell>
                    <TableHeaderCell>Eng. Rate</TableHeaderCell>
                    <TableHeaderCell>Trending Days</TableHeaderCell>
                    <TableHeaderCell>TrendPulse Score</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data?.data?.map((video) => (
                    <TableRow key={video.video_id} className="hover:bg-slate-50 transition-colors cursor-pointer">
                      <TableCell className="max-w-xs">
                        <div className="truncate font-medium text-slate-900" title={video.title}>{video.title}</div>
                        <div className="text-xs text-slate-500 truncate mt-1">{video.channel_title}</div>
                      </TableCell>
                      <TableCell><Badge color="slate">{video.category_name || 'Unknown'}</Badge></TableCell>
                      <TableCell>{(video.views || 0).toLocaleString()}</TableCell>
                      <TableCell>{((video.engagement_rate || 0) * 100).toFixed(2)}%</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-700">{video.trending_duration_days}</span>
                          <span className="text-xs text-slate-400">({video.trending_duration_bucket})</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge size="lg" color={
                          video.trendpulse_label === 'Very High' ? 'emerald' :
                          video.trendpulse_label === 'High' ? 'blue' :
                          video.trendpulse_label === 'Moderate' ? 'yellow' : 'slate'
                        }>
                          {video.trendpulse_score?.toFixed(1) || '0.0'}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            
            <div className="flex items-center justify-between mt-6 px-4">
              <Text className="text-slate-500 font-medium">
                Showing page {data?.page} of {data?.total_pages} ({data?.total?.toLocaleString()} total)
              </Text>
              <div className="flex gap-2">
                <button 
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-50 font-medium transition-colors"
                >
                  Previous
                </button>
                <button 
                  onClick={() => setPage(p => Math.min(data?.total_pages || 1, p + 1))}
                  disabled={page >= (data?.total_pages || 1)}
                  className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 font-medium transition-colors shadow-sm"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
