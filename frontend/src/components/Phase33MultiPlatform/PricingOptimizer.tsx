import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

interface Product {
  id: string;
  sku: string;
  title: string;
  current_price: number;
  recommended_price: number;
  strategy: string;
  inventory: number;
  competitor_price: number;
  margin_impact: number;
}

const PricingOptimizer: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([
    {
      id: 'prod-1',
      sku: 'SKU-001',
      title: 'Premium Headphones',
      current_price: 99.99,
      recommended_price: 89.99,
      strategy: 'undercut_competitor',
      inventory: 150,
      competitor_price: 94.99,
      margin_impact: -8.5,
    },
    {
      id: 'prod-2',
      sku: 'SKU-002',
      title: 'Wireless Charger',
      current_price: 49.99,
      recommended_price: 69.99,
      strategy: 'scarcity_premium',
      inventory: 12,
      competitor_price: 59.99,
      margin_impact: +28.5,
    },
    {
      id: 'prod-3',
      sku: 'SKU-003',
      title: 'USB Cable',
      current_price: 12.99,
      recommended_price: 12.99,
      strategy: 'maintain_margin',
      inventory: 500,
      competitor_price: 13.99,
      margin_impact: 0,
    },
  ]);

  const priceHistoryData = [
    { date: 'Day 1', ml: 99.99, amazon: 104.99, hotmart: 79.99 },
    { date: 'Day 5', ml: 94.99, amazon: 99.99, hotmart: 79.99 },
    { date: 'Day 10', ml: 89.99, amazon: 94.99, hotmart: 69.99 },
    { date: 'Day 15', ml: 89.99, amazon: 94.99, hotmart: 69.99 },
  ];

  const getStrategyBadge = (strategy: string) => {
    const badges: Record<string, { bg: string; text: string; label: string }> = {
      undercut_competitor: { bg: 'bg-red-100', text: 'text-red-800', label: '📉 Undercut' },
      scarcity_premium: { bg: 'bg-green-100', text: 'text-green-800', label: '🔥 Premium' },
      maintain_margin: { bg: 'bg-blue-100', text: 'text-blue-800', label: '💰 Margin' },
      seasonal_surge: { bg: 'bg-orange-100', text: 'text-orange-800', label: '🎉 Seasonal' },
    };
    const badge = badges[strategy] || badges.maintain_margin;
    return { ...badge };
  };

  return (
    <div className="p-8 bg-gradient-to-br from-gray-50 to-gray-100">
      <h1 className="text-3xl font-bold mb-8 text-gray-900">Dynamic Pricing Optimizer</h1>

      {/* Price History Chart */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Price History (Top Product)</h2>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={priceHistoryData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis label={{ value: 'Price ($)', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(value) => `$${(value as number).toFixed(2)}`} />
            <Legend />
            <Line type="monotone" dataKey="ml" stroke="#3b82f6" name="Mercado Libre" />
            <Line type="monotone" dataKey="amazon" stroke="#10b981" name="Amazon" />
            <Line type="monotone" dataKey="hotmart" stroke="#f59e0b" name="Hotmart" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Repricing Status */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-900">Repricing Status</h2>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            🚀 Reprice All Now
          </button>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded">
            <p className="text-gray-600 text-sm">Last Repricing</p>
            <p className="text-lg font-bold text-gray-900">2 hours ago</p>
          </div>
          <div className="bg-green-50 p-4 rounded">
            <p className="text-gray-600 text-sm">Prices Increased</p>
            <p className="text-lg font-bold text-green-600">45 products</p>
          </div>
          <div className="bg-orange-50 p-4 rounded">
            <p className="text-gray-600 text-sm">Prices Decreased</p>
            <p className="text-lg font-bold text-orange-600">60 products</p>
          </div>
        </div>

        <div className="bg-yellow-50 p-4 border border-yellow-200 rounded">
          <p className="text-sm text-yellow-800">
            ⚡ <strong>Revenue Impact:</strong> +8.5% estimated MRR from dynamic pricing optimization
          </p>
        </div>
      </div>

      {/* Product Pricing Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left py-3 px-4 text-gray-700 font-semibold">Product</th>
              <th className="text-center py-3 px-4 text-gray-700 font-semibold">Current Price</th>
              <th className="text-center py-3 px-4 text-gray-700 font-semibold">Recommended</th>
              <th className="text-center py-3 px-4 text-gray-700 font-semibold">Change</th>
              <th className="text-center py-3 px-4 text-gray-700 font-semibold">Strategy</th>
              <th className="text-center py-3 px-4 text-gray-700 font-semibold">Margin Impact</th>
              <th className="text-center py-3 px-4 text-gray-700 font-semibold">Action</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product, idx) => {
              const priceDiff = product.recommended_price - product.current_price;
              const priceDiffPct = ((priceDiff / product.current_price) * 100).toFixed(1);
              const badge = getStrategyBadge(product.strategy);

              return (
                <tr key={idx} className="border-b hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <p className="font-semibold text-gray-900">{product.title}</p>
                    <p className="text-sm text-gray-500">{product.sku}</p>
                  </td>
                  <td className="text-center py-3 px-4">
                    <p className="font-semibold text-gray-900">${product.current_price.toFixed(2)}</p>
                  </td>
                  <td className="text-center py-3 px-4">
                    <p className="font-bold text-blue-600">${product.recommended_price.toFixed(2)}</p>
                  </td>
                  <td className="text-center py-3 px-4">
                    <span className={`inline-block px-3 py-1 rounded text-sm font-semibold ${
                      priceDiff > 0 ? 'bg-green-100 text-green-800' : priceDiff < 0 ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {priceDiff > 0 ? '+' : ''}{priceDiffPct}%
                    </span>
                  </td>
                  <td className="text-center py-3 px-4">
                    <span className={`inline-block px-3 py-1 rounded text-sm font-semibold ${badge.bg} ${badge.text}`}>
                      {badge.label}
                    </span>
                  </td>
                  <td className="text-center py-3 px-4">
                    <span className={`inline-block px-3 py-1 rounded text-sm font-semibold ${
                      product.margin_impact > 0 ? 'bg-green-100 text-green-800' : product.margin_impact < 0 ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {product.margin_impact > 0 ? '+' : ''}{product.margin_impact}%
                    </span>
                  </td>
                  <td className="text-center py-3 px-4">
                    <button className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition">
                      Apply
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Competitor Analysis */}
      <div className="mt-8 bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Competitor Price Intelligence</h2>
        <p className="text-gray-600 mb-4">Last scan: 15 minutes ago • Tracking 150+ competitors across 3 platforms</p>
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded">
            <p className="text-gray-600 text-sm">Mercado Libre</p>
            <p className="text-2xl font-bold text-blue-600">47 tracked</p>
            <p className="text-xs text-gray-500">Avg competitor: $94.99</p>
          </div>
          <div className="bg-green-50 p-4 rounded">
            <p className="text-gray-600 text-sm">Amazon</p>
            <p className="text-2xl font-bold text-green-600">38 tracked</p>
            <p className="text-xs text-gray-500">Avg competitor: $99.99</p>
          </div>
          <div className="bg-orange-50 p-4 rounded">
            <p className="text-gray-600 text-sm">Hotmart</p>
            <p className="text-2xl font-bold text-orange-600">25 tracked</p>
            <p className="text-xs text-gray-500">Avg competitor: $79.99</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PricingOptimizer;
