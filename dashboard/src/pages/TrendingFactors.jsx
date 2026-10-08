import React, { useEffect, useState } from 'react';
import { Card, Title, Text, BarChart, Badge } from '@tremor/react';
import { getTrendingFactors } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';

export default function TrendingFactors() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getTrendingFactors()
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
  if (!data) return null;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Trending Factor Analysis</h1>
        <p className="text-slate-500 mt-1">Data-driven ranking of attributes most strongly associated with extended trending duration.</p>
      </div>

      <Card className="bg-white ring-1 ring-slate-200">
        <Title>Top Factors Influencing Trending Duration</Title>
        <Text className="mb-6">Composite score based on Correlation (Pearson/Spearman/ANOVA) and Mutual Information.</Text>
        
        <BarChart
          className="h-80 mt-4"
          data={data.factors}
          index="factor_label"
          categories={["score"]}
          colors={["indigo"]}
          valueFormatter={(val) => val.toFixed(4)}
          layout="horizontal"
          yAxisWidth={160}
        />
      </Card>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-slate-800">Detailed Interpretations</h3>
        {data.factors.map((factor, idx) => (
          <Card key={idx} className="bg-white ring-1 ring-slate-200 hover:shadow-md transition-shadow">
            <div className="flex flex-col md:flex-row md:items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-xl shrink-0 border border-indigo-100">
                #{factor.rank_position}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h4 className="font-bold text-slate-900 text-lg">{factor.factor_label}</h4>
                  <Badge color={factor.association_type === 'categorical' ? 'fuchsia' : 'blue'}>
                    {factor.association_type}
                  </Badge>
                  <Badge color="emerald">Score: {factor.score.toFixed(4)}</Badge>
                </div>
                <p className="text-slate-600 leading-relaxed bg-slate-50 p-4 rounded-lg border border-slate-100">
                  {factor.interpretation}
                </p>
                <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-500 font-medium">
                  {factor.pearson_r !== null && <span>Pearson r: {factor.pearson_r.toFixed(3)}</span>}
                  {factor.anova_f !== null && <span>ANOVA F: {factor.anova_f.toFixed(2)}</span>}
                  {factor.mutual_info !== null && <span>Mutual Info: {factor.mutual_info.toFixed(4)}</span>}
                  {factor.p_value !== null && <span>p-value: {factor.p_value < 0.001 ? '<0.001' : factor.p_value.toFixed(4)}</span>}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
