import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface SegmentData {
  name: string;
  users: number;
  conversion_rate: number;
}

interface MetricsData {
  total_free_users: number;
  total_conversions: number;
  total_revenue: number;
  avg_conversion_rate: number;
  segments: SegmentData[];
}

const MonetizationOverview: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('/api/v1/monetization/revenue-forecast');
        const data = await response.json();

        setMetrics({
          total_free_users: data.free_users,
          total_conversions: Math.floor(data.monthly_conversions),
          total_revenue: data.monthly_revenue,
          avg_conversion_rate: data.avg_conversion_rate,
          segments: [
            { name: 'Freemium Active', users: 40000, conversion_rate: 0.35 },
            { name: 'Freemium Stale', users: 20000, conversion_rate: 0.15 },
            { name: 'Trial Ending', users: 15000, conversion_rate: 0.45 },
            { name: 'Power User', users: 20000, conversion_rate: 0.28 },
            { name: 'At-Risk Paid', users: 5000, conversion_rate: 0.40 },
          ],
        });
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  if (loading) return <div className="p-8">Loading metrics...</div>;
  if (!metrics) return <div className="p-8">Failed to load metrics</div>;

  const segmentChartData = metrics.segments.map(s => ({
    name: s.name,
    users: s.users / 1000,
    conversion: s.conversion_rate * 100,
  }));

  return (
    <div className="p-8 bg-gradient-to-br from-gray-50 to-gray-100">
      <h1 className="text-3xl font-bold mb-8 text-gray-900">Platform Monetization Dashboard</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Total Free Users</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{metrics.total_free_users.toLocaleString()}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Monthly Conversions</p>
          <p className="text-3xl font-bold text-green-600 mt-2">{metrics.total_conversions.toLocaleString()}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">MRR from Conversions</p>
          <p className="text-3xl font-bold text-blue-600 mt-2">${(metrics.total_revenue / 1000000).toFixed(2)}M</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Avg Conversion Rate</p>
          <p className="text-3xl font-bold text-purple-600 mt-2">{(metrics.avg_conversion_rate * 100).toFixed(1)}%</p>
        </div>
      </div>

      {/* Segment Distribution */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Users by Segment</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={segmentChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
              <YAxis label={{ value: 'Users (thousands)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Bar dataKey="users" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Conversion Rate by Segment</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={segmentChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
              <YAxis label={{ value: 'Conversion %', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Bar dataKey="conversion" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Segment Details Table */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Segment Breakdown</h2>
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2 px-4 text-gray-700 font-semibold">Segment</th>
              <th className="text-right py-2 px-4 text-gray-700 font-semibold">Users</th>
              <th className="text-right py-2 px-4 text-gray-700 font-semibold">Conversion Rate</th>
              <th className="text-right py-2 px-4 text-gray-700 font-semibold">Est. Conversions</th>
              <th className="text-right py-2 px-4 text-gray-700 font-semibold">Est. Revenue</th>
            </tr>
          </thead>
          <tbody>
            {metrics.segments.map((segment, idx) => (
              <tr key={idx} className="border-b hover:bg-gray-50">
                <td className="py-3 px-4 text-gray-900 font-medium">{segment.name}</td>
                <td className="text-right py-3 px-4 text-gray-700">{segment.users.toLocaleString()}</td>
                <td className="text-right py-3 px-4 text-green-600 font-semibold">{(segment.conversion_rate * 100).toFixed(1)}%</td>
                <td className="text-right py-3 px-4 text-gray-700">{Math.floor(segment.users * segment.conversion_rate).toLocaleString()}</td>
                <td className="text-right py-3 px-4 text-blue-600 font-semibold">${(segment.users * segment.conversion_rate * 5000).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default MonetizationOverview;

