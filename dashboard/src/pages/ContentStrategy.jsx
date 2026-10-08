import React, { useEffect, useState } from 'react';
import { Card, Title, Text, Grid, Col, BarChart, LineChart } from '@tremor/react';
import { getUploadTimes, getTitleAnalysis } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';

export default function ContentStrategy() {
  const [uploadTimes, setUploadTimes] = useState([]);
  const [titleData, setTitleData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([getUploadTimes(), getTitleAnalysis()])
      .then(([uploadRes, titleRes]) => {
        setUploadTimes(uploadRes);
        setTitleData(titleRes);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorState error={error} retry={() => window.location.reload()} />;

  const hourFormatter = (number) => `${number}:00`;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Content Strategy Insights</h1>
        <p className="text-slate-500 mt-1">Actionable insights on upload timing and metadata optimization.</p>
      </div>

      <Grid numItems={1} numItemsLg={2} className="gap-6">
        <Col>
          <Card className="h-full bg-white ring-1 ring-slate-200">
            <Title>Optimal Upload Timing (UTC)</Title>
            <Text className="mb-4">Average trending duration by publish hour</Text>
            <LineChart
              className="mt-6 h-72"
              data={uploadTimes}
              index="publish_hour"
              categories={["avg_trending_duration"]}
              colors={["emerald"]}
              valueFormatter={(val) => val.toFixed(1) + " days"}
              yAxisWidth={48}
            />
          </Card>
        </Col>
        
        <Col>
          <Card className="h-full bg-white ring-1 ring-slate-200">
            <Title>Upload Volume Heatmap</Title>
            <Text className="mb-4">When are most trending videos published?</Text>
            <BarChart
              className="mt-6 h-72"
              data={uploadTimes}
              index="publish_hour"
              categories={["total_videos"]}
              colors={["sky"]}
              valueFormatter={(val) => val.toLocaleString()}
              yAxisWidth={60}
            />
          </Card>
        </Col>
      </Grid>

      <Card className="bg-white ring-1 ring-slate-200 mt-6">
        <Title>Title Length Optimization</Title>
        <Text className="mb-6">Relationship between title character count and trending performance</Text>
        <BarChart
          className="h-80"
          data={titleData}
          index="bucket"
          categories={["avg_trending_duration"]}
          colors={["fuchsia"]}
          valueFormatter={(val) => val.toFixed(2) + " days"}
          yAxisWidth={48}
        />
      </Card>
    </div>
  );
}
