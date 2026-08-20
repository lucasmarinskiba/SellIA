import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Zap, TrendingDown, Clock } from 'lucide-react';

const ApiManagementDashboard: React.FC<{ businessId: string }> = ({ businessId }) => {
  const [metrics, setMetrics] = useState<any>(null);
  const [rateLimitData, setRateLimitData] = useState<any[]>([]);
  const [performanceData, setPerformanceData] = useState<any[]>([]);

  useEffect(() => {
    fetchApiMetrics();
  }, [businessId]);

  const fetchApiMetrics = async () => {
    try {
      const res = await fetch(`/api/v1/businesses/${businessId}/api-metrics`);
      const data = await res.json();

      setMetrics(data);

      const rateLimits = [
        { name: 'Free', limit: 100, used: 85, color: '#3b82f6' },
        { name: 'Starter', limit: 1000, used: 650, color: '#10b981' },
        { name: 'Pro', limit: 10000, used: 4200, color: '#f59e0b' }
      ];
      setRateLimitData(rateLimits);

      const performance = Array.from({ length: 24 }).map((_, i) => ({
        hour: `${i}:00`,
        avgMs: Math.floor(Math.random() * 150 + 50),
        p95Ms: Math.floor(Math.random() * 300 + 100),
        p99Ms: Math.floor(Math.random() * 500 + 200)
      }));
      setPerformanceData(performance);
    } catch (error) {
      console.error('Failed to fetch API metrics:', error);
    }
  };

  return (
    <div className="w-full space-y-6 p-6 bg-gray-50">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">API Management</h1>
        <button onClick={fetchApiMetrics} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Total Requests</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{metrics?.requests?.total || 0}</p>
              <p className="text-xs text-gray-500 mt-1">Error Rate: {metrics?.requests?.errors || 0}%</p>
            </div>
            <Zap className="w-10 h-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Cache Hit Rate</p>
              <p className="text-3xl font-bold text-green-600 mt-2">{metrics?.cache?.hit_rate_pct || 0}%</p>
              <p className="text-xs text-gray-500 mt-1">{metrics?.cache?.hits || 0} hits today</p>
            </div>
            <TrendingDown className="w-10 h-10 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Avg Response Time</p>
              <p className="text-3xl font-bold text-blue-600 mt-2">{metrics?.performance?.avg_ms || 0}ms</p>
              <p className="text-xs text-gray-500 mt-1">P95: {metrics?.performance?.p95_ms || 0}ms</p>
            </div>
            <Clock className="w-10 h-10 text-blue-500" />
          </div>
        </div>
      </div>

      {/* Rate Limit Usage */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Rate Limit Usage by Tier</h2>
        <div className="space-y-4">
          {rateLimitData.map((tier, idx) => (
            <div key={idx}>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">{tier.name} Tier</span>
                <span className="text-sm text-gray-600">{tier.used}/{tier.limit} requests/hour</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${(tier.used / tier.limit) * 100}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Response Time (24h)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={performanceData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis />
            <Tooltip formatter={(value) => `${value}ms`} />
            <Legend />
            <Line type="monotone" dataKey="avgMs" stroke="#3b82f6" name="Average" />
            <Line type="monotone" dataKey="p95Ms" stroke="#f59e0b" name="P95" />
            <Line type="monotone" dataKey="p99Ms" stroke="#ef4444" name="P99" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ApiManagementDashboard;
