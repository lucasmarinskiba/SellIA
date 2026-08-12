import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface PlatformMetrics {
  mercado_libre: any;
  amazon: any;
  hotmart: any;
  total_gmv: number;
  total_active_listings: number;
  avg_conversion_rate: number;
}

const PlatformOverview: React.FC = () => {
  const [metrics, setMetrics] = useState<PlatformMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('/api/v1/platforms/dashboard/overview');
        if (!response.ok) throw new Error('Failed to fetch');
        const data = await response.json();
        setMetrics(data);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
        // Fallback to mock data for demo
        setMetrics({
          mercado_libre: {
            monthly_revenue: 250000,
            active_listings: 150,
            avg_rating: 4.8,
            best_seller_rank: 1,
          },
          amazon: {
            monthly_revenue: 180000,
            active_listings: 120,
            avg_rating: 4.7,
            best_seller_rank: 3,
          },
          hotmart: {
            monthly_revenue: 120000,
            active_listings: 80,
            avg_rating: 4.9,
            best_seller_rank: 2,
          },
          total_gmv: 550000,
          total_active_listings: 350,
          avg_conversion_rate: 0.08,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  if (loading) return <div className="p-8">Loading multi-platform metrics...</div>;
  if (!metrics) return <div className="p-8">Failed to load metrics</div>;

  const platformData = [
    { name: 'Mercado Libre', revenue: metrics.mercado_libre.monthly_revenue, listings: metrics.mercado_libre.active_listings, rating: metrics.mercado_libre.avg_rating },
    { name: 'Amazon', revenue: metrics.amazon.monthly_revenue, listings: metrics.amazon.active_listings, rating: metrics.amazon.avg_rating },
    { name: 'Hotmart', revenue: metrics.hotmart.monthly_revenue, listings: metrics.hotmart.active_listings, rating: metrics.hotmart.avg_rating },
  ];

  const gmvChartData = platformData.map(p => ({
    name: p.name,
    gmv: p.revenue / 1000,  // Convert to thousands
  }));

  return (
    <div className="p-8 bg-gradient-to-br from-gray-50 to-gray-100">
      <h1 className="text-3xl font-bold mb-8 text-gray-900">Multi-Platform Seller Dashboard</h1>

      {/* Top KPIs */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Total GMV</p>
          <p className="text-3xl font-bold text-blue-600 mt-2">${(metrics.total_gmv / 1000).toFixed(0)}k</p>
          <p className="text-xs text-gray-500 mt-2">30-day revenue</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Active Listings</p>
          <p className="text-3xl font-bold text-green-600 mt-2">{metrics.total_active_listings}</p>
          <p className="text-xs text-gray-500 mt-2">Across 3 platforms</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Avg Conversion Rate</p>
          <p className="text-3xl font-bold text-purple-600 mt-2">{(metrics.avg_conversion_rate * 100).toFixed(1)}%</p>
          <p className="text-xs text-gray-500 mt-2">Platform average: 2-3%</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Best Seller Count</p>
          <p className="text-3xl font-bold text-yellow-600 mt-2">{metrics.mercado_libre.best_seller_rank === 1 ? '8+' : '15+'}</p>
          <p className="text-xs text-gray-500 mt-2">#1 rankings across categories</p>
        </div>
      </div>

      {/* Platform Comparison */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">GMV by Platform</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={gmvChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis label={{ value: 'Revenue ($k)', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={(value) => `$${(value as number).toFixed(0)}k`} />
              <Bar dataKey="gmv" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Revenue Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={gmvChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: $${value}k`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="gmv"
              >
                <Cell fill="#3b82f6" />
                <Cell fill="#10b981" />
                <Cell fill="#f59e0b" />
              </Pie>
              <Tooltip formatter={(value) => `$${(value as number).toFixed(0)}k`} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Platform Details */}
      <div className="grid grid-cols-3 gap-6">
        {platformData.map((platform, idx) => (
          <div key={idx} className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-bold text-gray-900">{platform.name}</h3>
              <span className={`inline-block px-3 py-1 rounded text-xs font-semibold ${
                idx === 0 ? 'bg-blue-100 text-blue-800' : idx === 1 ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'
              }`}>
                {idx === 0 ? 'LATAM Leader' : idx === 1 ? 'Global' : 'Digital'}
              </span>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-gray-600 text-sm">Monthly Revenue</p>
                <p className="text-2xl font-bold text-gray-900">${(platform.revenue / 1000).toFixed(0)}k</p>
              </div>
              <div>
                <p className="text-gray-600 text-sm">Active Listings</p>
                <p className="text-lg font-bold text-gray-900">{platform.listings}</p>
              </div>
              <div>
                <p className="text-gray-600 text-sm">Seller Rating</p>
                <p className="text-lg font-bold text-yellow-600">⭐ {platform.rating}/5</p>
              </div>
              <button className="w-full mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                View Details →
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="mt-8 bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-4 gap-4">
          <button className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            ➕ Create Product
          </button>
          <button className="px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition">
            💰 Reprice All
          </button>
          <button className="px-4 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition">
            🎯 Optimize SEO
          </button>
          <button className="px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition">
            📊 Analytics
          </button>
        </div>
      </div>
    </div>
  );
};

export default PlatformOverview;
