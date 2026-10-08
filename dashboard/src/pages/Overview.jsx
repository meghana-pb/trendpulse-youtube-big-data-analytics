import React, { useEffect, useState } from 'react';
import { Card, Title, Text, Grid, Col, DonutChart, Legend, BarChart, Flex } from '@tremor/react';
import { Activity, Clock, PlayCircle, Zap } from 'lucide-react';
import { getOverview, getCategories } from '../services/api';
import KPICard from '../components/KPICard';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';

export default function Overview() {
  const [data, setData] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([getOverview(), getCategories()])
      .then(([overviewData, catData]) => {
        setData(overviewData);
        setCategories(catData.slice(0, 7)); // Top 7 for charts
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorState error={error} retry={() => window.location.reload()} />;
  if (!data) return null;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Platform Overview</h1>
        <p className="text-slate-500 mt-1">High-level metrics across the entire YouTube trending dataset.</p>
      </div>

      <Grid numItems={1} numItemsSm={2} numItemsLg={4} className="gap-6">
        <KPICard title="Analyzed Videos" metric={data.total_videos.toLocaleString()} icon={PlayCircle} />
        <KPICard title="Avg Trending Duration" metric={data.avg_trending_duration.toFixed(1)} suffix=" days" icon={Clock} />
        <KPICard title="Avg Engagement Rate" metric={(data.avg_engagement_rate * 100).toFixed(2)} suffix="%" icon={Activity} />
        <KPICard title="Breakout Anomalies" metric={data.breakout_video_count} icon={Zap} />
      </Grid>

      <Grid numItems={1} numItemsLg={3} className="gap-6">
        <Col numColSpan={1} numColSpanLg={2}>
          <Card className="h-full bg-white ring-1 ring-slate-200">
            <Title>Top Categories by Avg Trending Duration (Days)</Title>
            <Text className="mb-4">Which content types stay trending the longest?</Text>
            <BarChart
              className="mt-4 h-72"
              data={categories}
              index="category_name"
              categories={["avg_trending_duration"]}
              colors={["blue"]}
              valueFormatter={(val) => val.toFixed(1) + " days"}
              yAxisWidth={48}
            />
          </Card>
        </Col>
        
        <Col numColSpan={1} numColSpanLg={1}>
          <Card className="h-full bg-white ring-1 ring-slate-200 flex flex-col">
            <Title>Video Distribution</Title>
            <Text className="mb-6">Breakdown by category volume</Text>
            <div className="flex-1 flex flex-col justify-center">
              <DonutChart
                className="h-48"
                data={categories}
                category="total_videos"
                index="category_name"
                valueFormatter={(val) => val.toLocaleString()}
                colors={["blue", "cyan", "indigo", "violet", "fuchsia", "sky", "emerald"]}
              />
              <Legend
                className="mt-6 flex-wrap justify-center"
                categories={categories.map(c => c.category_name)}
                colors={["blue", "cyan", "indigo", "violet", "fuchsia", "sky", "emerald"]}
              />
            </div>
          </Card>
        </Col>
      </Grid>

      {data.insights && data.insights.length > 0 && (
        <Card className="bg-gradient-to-br from-indigo-900 to-blue-900 text-white ring-0">
          <Title className="text-white flex items-center gap-2 mb-4">
            <Zap size={20} className="text-yellow-400" />
            Key Insights
          </Title>
          <ul className="space-y-4">
            {data.insights.map((insight, idx) => (
              <li key={idx} className="flex gap-4 p-4 rounded-lg bg-white/10 backdrop-blur-sm border border-white/10">
                <div className="shrink-0 w-8 h-8 rounded-full bg-blue-500/30 flex items-center justify-center font-bold text-blue-200">
                  {idx + 1}
                </div>
                <p className="text-blue-50 leading-relaxed font-medium">{insight}</p>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
