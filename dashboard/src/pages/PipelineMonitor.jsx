import React, { useEffect, useState } from 'react';
import { Card, Title, Text, Grid, Col, Tracker, Flex } from '@tremor/react';
import { Database, Server, Cpu, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { getPipelineStatus, getDataQuality } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';

export default function PipelineMonitor() {
  const [status, setStatus] = useState(null);
  const [quality, setQuality] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = () => {
    setLoading(true);
    Promise.all([getPipelineStatus(), getDataQuality()])
      .then(([statusRes, qualityRes]) => {
        setStatus(statusRes);
        setQuality(qualityRes);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Auto-refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading && !status) return <LoadingSpinner />;
  if (error) return <ErrorState error={error} retry={fetchData} />;

  const getStatusColor = (s) => {
    if (s === 'ONLINE') return 'text-emerald-500 bg-emerald-50 border-emerald-200';
    if (s === 'WARNING') return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    if (s === 'ERROR') return 'text-red-500 bg-red-50 border-red-200';
    return 'text-blue-500 bg-blue-50 border-blue-200';
  };

  const getStatusIcon = (s) => {
    if (s === 'ONLINE') return <CheckCircle size={20} />;
    if (s === 'WARNING') return <AlertCircle size={20} />;
    if (s === 'ERROR') return <XCircle size={20} />;
    return <Cpu size={20} className="animate-pulse" />;
  };

  // Mock tracker data for demo purposes since we don't have historical uptime
  const trackerData = Array.from({ length: 24 }).map((_, i) => {
    if (i === 14) return { color: "yellow", tooltip: "Warning: High latency" };
    if (i === 20) return { color: "emerald", tooltip: "Operational" }; // Current
    return { color: "emerald", tooltip: "Operational" };
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Pipeline Monitor</h1>
          <p className="text-slate-500 mt-1">System health, data ingestion metrics, and quality checks.</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </span>
          Live Monitoring Active
        </div>
      </div>

      <Grid numItems={1} numItemsLg={2} className="gap-6">
        <Col>
          <Card className="h-full bg-white ring-1 ring-slate-200">
            <Title className="flex items-center gap-2 mb-6"><Server size={20}/> Infrastructure Status</Title>
            <div className="space-y-4">
              {status?.services?.map((svc, idx) => (
                <div key={idx} className="flex items-center justify-between p-4 rounded-xl border border-slate-100 bg-slate-50">
                  <div>
                    <h4 className="font-semibold text-slate-800">{svc.name}</h4>
                    <p className="text-xs text-slate-500 mt-1">{svc.details}</p>
                  </div>
                  <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm font-bold ${getStatusColor(svc.status)}`}>
                    {getStatusIcon(svc.status)}
                    {svc.status}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-8 pt-6 border-t border-slate-100">
              <Flex className="mb-2">
                <Text className="font-semibold text-slate-700">System Uptime (Last 24h)</Text>
                <Text>99.9%</Text>
              </Flex>
              <Tracker data={trackerData} className="mt-2" />
            </div>
          </Card>
        </Col>

        <Col>
          <Card className="h-full bg-white ring-1 ring-slate-200">
            <Title className="flex items-center gap-2 mb-6"><Database size={20}/> Pipeline Throughput</Title>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                <Text className="text-sm font-semibold text-slate-500">Kafka Produced</Text>
                <p className="text-2xl font-bold text-slate-900 mt-1">{(status?.kafka_messages_produced || 0).toLocaleString()}</p>
              </div>
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                <Text className="text-sm font-semibold text-slate-500">Kafka Consumed</Text>
                <p className="text-2xl font-bold text-slate-900 mt-1">{(status?.kafka_messages_consumed || 0).toLocaleString()}</p>
              </div>
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                <Text className="text-sm font-semibold text-slate-500">HDFS Records</Text>
                <p className="text-2xl font-bold text-blue-600 mt-1">{(status?.hdfs_records_written || 0).toLocaleString()}</p>
              </div>
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                <Text className="text-sm font-semibold text-slate-500">Analytics DB</Text>
                <p className="text-2xl font-bold text-emerald-600 mt-1">{(status?.analytics_records || 0).toLocaleString()}</p>
              </div>
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 col-span-2 flex items-center justify-between">
                <Text className="text-sm font-semibold text-slate-500">MapReduce Jobs Completed</Text>
                <p className="text-2xl font-bold text-purple-600">{status?.mapreduce_jobs_run || 0}</p>
              </div>
            </div>
            <div className="mt-6">
               <Text className="text-xs text-slate-400">Last pipeline run: {status?.last_run ? new Date(status.last_run).toLocaleString() : 'N/A'}</Text>
            </div>
          </Card>
        </Col>
      </Grid>

      <Card className="bg-white ring-1 ring-slate-200 mt-6">
        <div className="flex items-center justify-between mb-6">
          <Title>Data Quality Assessment</Title>
          <div className={`px-4 py-1.5 rounded-full font-bold text-white ${
            quality?.quality_score >= 95 ? 'bg-emerald-500' :
            quality?.quality_score >= 80 ? 'bg-yellow-500' : 'bg-red-500'
          }`}>
            Score: {quality?.quality_score || 0}%
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="py-3 px-4 text-sm font-semibold text-slate-600">Check Name</th>
                <th className="py-3 px-4 text-sm font-semibold text-slate-600">Passed</th>
                <th className="py-3 px-4 text-sm font-semibold text-slate-600">Failed</th>
                <th className="py-3 px-4 text-sm font-semibold text-slate-600">Pass Rate</th>
                <th className="py-3 px-4 text-sm font-semibold text-slate-600">Status</th>
              </tr>
            </thead>
            <tbody>
              {quality?.checks?.map((check, idx) => (
                <tr key={idx} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                  <td className="py-3 px-4 font-medium text-slate-800">{check.check}</td>
                  <td className="py-3 px-4 text-emerald-600">{check.passed.toLocaleString()}</td>
                  <td className="py-3 px-4 text-red-600">{check.failed.toLocaleString()}</td>
                  <td className="py-3 px-4 font-semibold text-slate-700">{check.pass_rate.toFixed(1)}%</td>
                  <td className="py-3 px-4">
                    {check.pass_rate >= 95 ? (
                      <span className="text-xs font-bold bg-emerald-100 text-emerald-700 px-2 py-1 rounded">PASS</span>
                    ) : check.pass_rate >= 80 ? (
                      <span className="text-xs font-bold bg-yellow-100 text-yellow-700 px-2 py-1 rounded">WARN</span>
                    ) : (
                      <span className="text-xs font-bold bg-red-100 text-red-700 px-2 py-1 rounded">FAIL</span>
                    )}
                  </td>
                </tr>
              ))}
              {(!quality?.checks || quality.checks.length === 0) && (
                <tr>
                  <td colSpan="5" className="py-8 text-center text-slate-500 font-medium">
                    No data quality metrics available. Run the pipeline to generate reports.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
