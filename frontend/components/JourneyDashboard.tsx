import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, Users, ShoppingCart, Repeat2 } from 'lucide-react';

interface JourneyStageMetric {
  stage: string;
  count: number;
  conversionRate: number;
}

interface JourneyMetrics {
  awareness: number;
  consideration: number;
  intent: number;
  visit: number;
  purchase: number;
  retention: number;
  aov: number;
  avgLtv: number;
}

const JourneyDashboard: React.FC<{ businessId: string }> = ({ businessId }) => {
  const [metrics, setMetrics] = useState<JourneyMetrics | null>(null);
  const [stageData, setStageData] = useState<JourneyStageMetric[]>([]);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [channelBreakdown, setChannelBreakdown] = useState<any[]>([]);

  useEffect(() => {
    fetchJourneyMetrics();
  }, [businessId]);

  const fetchJourneyMetrics = async () => {
    try {
      const res = await fetch(`/api/v1/businesses/${businessId}/segmentation-summary`);
      const data = await res.json();

      setMetrics({
        awareness: data.funnel?.awareness || 0,
        consideration: data.funnel?.consideration || 0,
        intent: data.funnel?.intent || 0,
        visit: data.funnel?.visit || 0,
        purchase: data.funnel?.purchase || 0,
        retention: 0,
        aov: 0,
        avgLtv: data.avg_clv || 0
      });

      const stages = [
        { stage: 'Awareness', count: data.funnel?.awareness || 0, conversionRate: 100 },
        { stage: 'Consideration', count: data.funnel?.consideration || 0, conversionRate: (data.funnel?.consideration / data.funnel?.awareness * 100) || 0 },
        { stage: 'Intent', count: data.funnel?.intent || 0, conversionRate: (data.funnel?.intent / data.funnel?.awareness * 100) || 0 },
        { stage: 'Visit', count: data.funnel?.visit || 0, conversionRate: (data.funnel?.visit / data.funnel?.awareness * 100) || 0 },
        { stage: 'Purchase', count: data.funnel?.purchase || 0, conversionRate: data.conversion_rates?.awareness_to_visit_pct || 0 },
        { stage: 'Retention', count: 0, conversionRate: 0 }
      ];
      setStageData(stages);

      // Sample trend data
      const trend = Array.from({ length: 30 }).map((_, i) => ({
        day: `Day ${i + 1}`,
        awareness: Math.floor(Math.random() * 100 + 50),
        purchase: Math.floor(Math.random() * 20 + 10)
      }));
      setTrendData(trend);

      // Channel breakdown
      const channels = [
        { name: 'organic_search', value: 35 },
        { name: 'paid_search', value: 25 },
        { name: 'social_media', value: 20 },
        { name: 'email', value: 15 },
        { name: 'direct', value: 5 }
      ];
      setChannelBreakdown(channels);
    } catch (error) {
      console.error('Failed to fetch journey metrics:', error);
    }
  };

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  return (
    <div className="w-full space-y-6 p-6 bg-gray-50">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Customer Journey Mapping</h1>
        <button onClick={fetchJourneyMetrics} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Total Journeys</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{metrics?.awareness || 0}</p>
            </div>
            <Users className="w-10 h-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Converted</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{metrics?.purchase || 0}</p>
            </div>
            <ShoppingCart className="w-10 h-10 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Repeat Rate</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">42%</p>
            </div>
            <Repeat2 className="w-10 h-10 text-purple-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Avg LTV</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">${metrics?.avgLtv?.toFixed(0) || 0}</p>
            </div>
            <TrendingUp className="w-10 h-10 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Funnel Chart */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Conversion Funnel</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={stageData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="stage" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="count" fill="#3b82f6" name="Count" />
            <Bar yAxisId="right" dataKey="conversionRate" fill="#10b981" name="Conversion %" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Trend Chart */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">30-Day Trend</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="awareness" stroke="#3b82f6" name="Awareness" />
            <Line type="monotone" dataKey="purchase" stroke="#10b981" name="Purchase" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Channel Breakdown */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Discovery Channels</h2>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie data={channelBreakdown} cx="50%" cy="50%" labelLine={false} label={({ name, value }) => `${name}: ${value}%`} outerRadius={100} fill="#8884d8" dataKey="value">
              {channelBreakdown.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default JourneyDashboard;
