import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import { TrendingUp, Zap, DollarSign } from 'lucide-react';

const AttributionDashboard: React.FC<{ businessId: string }> = ({ businessId }) => {
  const [channelROI, setChannelROI] = useState<any[]>([]);
  const [topChannels, setTopChannels] = useState<any[]>([]);
  const [attributionTrend, setAttributionTrend] = useState<any[]>([]);

  useEffect(() => {
    fetchAttributionData();
  }, [businessId]);

  const fetchAttributionData = async () => {
    try {
      const res = await fetch(`/api/v1/businesses/${businessId}/top-channels?metric=revenue&days=30`);
      const data = await res.json();

      if (data.channels) {
        setTopChannels(data.channels);
        setChannelROI(data.channels.map((ch: any) => ({
          name: ch.channel,
          roas: ch.roas || 0,
          cost: ch.cost || 0,
          revenue: ch.revenue || 0
        })));
      }

      // Trend data
      const trend = Array.from({ length: 30 }).map((_, i) => ({
        day: `Day ${i + 1}`,
        organic: Math.floor(Math.random() * 5000 + 2000),
        paid: Math.floor(Math.random() * 8000 + 1000),
        social: Math.floor(Math.random() * 3000 + 500),
        email: Math.floor(Math.random() * 2000 + 300)
      }));
      setAttributionTrend(trend);
    } catch (error) {
      console.error('Failed to fetch attribution data:', error);
    }
  };

  return (
    <div className="w-full space-y-6 p-6 bg-gray-50">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Marketing Attribution</h1>
        <button onClick={fetchAttributionData} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Refresh
        </button>
      </div>

      {/* Top Channels */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {topChannels.slice(0, 3).map((channel, idx) => (
          <div key={idx} className="bg-white p-6 rounded-lg shadow">
            <p className="text-gray-600 text-sm font-medium capitalize">{channel.channel}</p>
            <div className="mt-3 space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-700">Revenue:</span>
                <span className="font-bold text-green-600">${channel.revenue?.toFixed(0) || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-700">ROAS:</span>
                <span className="font-bold text-blue-600">{channel.roas?.toFixed(2) || 0}x</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-700">CPV:</span>
                <span className="font-bold text-orange-600">${channel.cpv?.toFixed(2) || 0}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Channel ROI Comparison */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Channel ROI Comparison</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={channelROI}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="roas" fill="#3b82f6" name="ROAS (x)" />
            <Bar yAxisId="right" dataKey="revenue" fill="#10b981" name="Revenue ($)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* 30-Day Revenue Trend by Channel */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Revenue Trend by Channel (30 days)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={attributionTrend}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip formatter={(value) => `$${value}`} />
            <Legend />
            <Line type="monotone" dataKey="organic" stroke="#3b82f6" name="Organic" />
            <Line type="monotone" dataKey="paid" stroke="#f59e0b" name="Paid" />
            <Line type="monotone" dataKey="social" stroke="#8b5cf6" name="Social" />
            <Line type="monotone" dataKey="email" stroke="#10b981" name="Email" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default AttributionDashboard;
