import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface KeywordMetric {
  keyword: string;
  search_volume: number;
  current_rank: number;
  competition: string;
  opportunity: number;
  conversion_rate: number;
}

const SEOOptimizer: React.FC = () => {
  const [selectedProduct] = useState('prod-1');
  const [keywords] = useState<KeywordMetric[]>([
    {
      keyword: 'best headphones',
      search_volume: 5000,
      current_rank: 3,
      competition: 'high',
      opportunity: 0.6,
      conversion_rate: 0.08,
    },
    {
      keyword: 'wireless headphones',
      search_volume: 3000,
      current_rank: 1,
      competition: 'medium',
      opportunity: 0.9,
      conversion_rate: 0.12,
    },
    {
      keyword: 'affordable headphones',
      search_volume: 2000,
      current_rank: 2,
      competition: 'low',
      opportunity: 0.95,
      conversion_rate: 0.15,
    },
    {
      keyword: 'professional headphones',
      search_volume: 1500,
      current_rank: 5,
      competition: 'high',
      opportunity: 0.4,
      conversion_rate: 0.20,
    },
  ]);

  const listingVersions = [
    {
      version: 1,
      title: 'Headphones | Premium Quality',
      impressions: 1200,
      conversions: 96,
      conversion_rate: 0.08,
      status: 'active',
    },
    {
      version: 2,
      title: 'Best Seller Headphones | Free Shipping | 4.9★',
      impressions: 1500,
      conversions: 180,
      conversion_rate: 0.12,
      status: 'active',
      winner: true,
    },
    {
      version: 3,
      title: 'Professional Wireless Headphones | Bestseller',
      impressions: 800,
      conversions: 120,
      conversion_rate: 0.15,
      status: 'testing',
    },
  ];

  const opportunityData = keywords.map(k => ({
    keyword: k.keyword.substring(0, 15),
    opportunity: k.opportunity * 100,
    conversion: k.conversion_rate * 100,
  }));

  return (
    <div className="p-8 bg-gradient-to-br from-gray-50 to-gray-100">
      <h1 className="text-3xl font-bold mb-8 text-gray-900">SEO & Listing Optimization</h1>

      {/* Quick Stats */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Keywords Tracked</p>
          <p className="text-3xl font-bold text-blue-600 mt-2">27</p>
          <p className="text-xs text-gray-500 mt-2">Across 3 platforms</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">#1 Rankings</p>
          <p className="text-3xl font-bold text-green-600 mt-2">8</p>
          <p className="text-xs text-gray-500 mt-2">Top position keywords</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Avg Position</p>
          <p className="text-3xl font-bold text-purple-600 mt-2">#4</p>
          <p className="text-xs text-gray-500 mt-2">↗️ Improving</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">A/B Test Winner</p>
          <p className="text-3xl font-bold text-yellow-600 mt-2">v2</p>
          <p className="text-xs text-gray-500 mt-2">+50% conversion lift</p>
        </div>
      </div>

      {/* Keyword Rankings */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Top Keywords & Rankings</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={opportunityData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="keyword" angle={-45} textAnchor="end" height={80} />
            <YAxis label={{ value: 'Score (%)', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="opportunity" fill="#3b82f6" name="Opportunity Score" />
            <Bar dataKey="conversion" fill="#10b981" name="Conversion %" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Keyword Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden mb-8">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left py-3 px-4 text-gray-700 font-semibold">Keyword</th>
              <th className="text-center py-3 px-4 text-gray-700 font-semibold">Search Vol</th>
              <th className="text-center py-3 px-4 text-gray-700 font-semibold">Current Rank</th>
              <th className="text-center py-3 px-4 text-gray-700 font-semibold">Competition</th>
              <th className="text-center py-3 px-4 text-gray-700 font-semibold">Opportunity</th>
              <th className="text-center py-3 px-4 text-gray-700 font-semibold">Conv. Rate</th>
              <th className="text-center py-3 px-4 text-gray-700 font-semibold">Trend</th>
            </tr>
          </thead>
          <tbody>
            {keywords.map((keyword, idx) => (
              <tr key={idx} className="border-b hover:bg-gray-50">
                <td className="py-3 px-4 font-semibold text-gray-900">{keyword.keyword}</td>
                <td className="text-center py-3 px-4 text-gray-700">{keyword.search_volume.toLocaleString()}</td>
                <td className="text-center py-3 px-4">
                  <span className={`inline-block px-3 py-1 rounded text-sm font-bold ${
                    keyword.current_rank <= 2 ? 'bg-green-100 text-green-800' : keyword.current_rank <= 5 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                  }`}>
                    #{keyword.current_rank}
                  </span>
                </td>
                <td className="text-center py-3 px-4">
                  <span className={`text-sm font-semibold ${
                    keyword.competition === 'low' ? 'text-green-600' : keyword.competition === 'medium' ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {keyword.competition}
                  </span>
                </td>
                <td className="text-center py-3 px-4">
                  <div className="w-16 bg-gray-200 rounded-full h-2 mx-auto">
                    <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${keyword.opportunity * 100}%` }}></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{(keyword.opportunity * 100).toFixed(0)}%</p>
                </td>
                <td className="text-center py-3 px-4 font-semibold text-gray-900">{(keyword.conversion_rate * 100).toFixed(1)}%</td>
                <td className="text-center py-3 px-4 text-sm">
                  {keyword.current_rank <= 2 ? '↗️ Up' : keyword.current_rank <= 5 ? '→ Stable' : '↘️ Down'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* A/B Test Listing Versions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Listing A/B Tests</h2>
        <div className="space-y-4">
          {listingVersions.map((version, idx) => (
            <div key={idx} className={`p-4 rounded-lg border-2 ${
              version.winner ? 'border-green-400 bg-green-50' : version.status === 'testing' ? 'border-blue-400 bg-blue-50' : 'border-gray-200 bg-gray-50'
            }`}>
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-bold text-gray-900">Version {version.version}</h3>
                  <p className="text-sm text-gray-600 mt-1">"{version.title}"</p>
                </div>
                <div className="text-right">
                  <span className={`inline-block px-3 py-1 rounded text-sm font-bold ${
                    version.winner ? 'bg-green-200 text-green-800' : version.status === 'active' ? 'bg-blue-200 text-blue-800' : 'bg-yellow-200 text-yellow-800'
                  }`}>
                    {version.winner ? '🏆 Winner' : version.status === 'active' ? '✓ Active' : '🧪 Testing'}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Impressions</p>
                  <p className="font-bold text-gray-900">{version.impressions.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-600">Conversions</p>
                  <p className="font-bold text-gray-900">{version.conversions}</p>
                </div>
                <div>
                  <p className="text-gray-600">Conv. Rate</p>
                  <p className={`font-bold ${version.conversion_rate > 0.12 ? 'text-green-600' : 'text-gray-900'}`}>
                    {(version.conversion_rate * 100).toFixed(2)}%
                  </p>
                </div>
                <div className="text-right">
                  {version.winner ? (
                    <button className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition">
                      Scale to 100%
                    </button>
                  ) : version.status === 'testing' ? (
                    <button className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition">
                      View Results
                    </button>
                  ) : (
                    <button className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 transition">
                      Archive
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      <div className="mt-8 grid grid-cols-2 gap-6">
        <div className="bg-green-50 rounded-lg shadow p-6 border-l-4 border-green-500">
          <h3 className="text-lg font-bold text-green-900 mb-3">✅ Quick Wins</h3>
          <ul className="space-y-2 text-green-800">
            <li>• Scale Version 2 (12% conv) to 100% → +$15k/month</li>
            <li>• Focus on "wireless headphones" (#1 rank)</li>
            <li>• Add "affordable" keyword to description</li>
          </ul>
        </div>

        <div className="bg-blue-50 rounded-lg shadow p-6 border-l-4 border-blue-500">
          <h3 className="text-lg font-bold text-blue-900 mb-3">📈 Optimization Path</h3>
          <ul className="space-y-2 text-blue-800">
            <li>• Test bullet point variations (5 A/B tests)</li>
            <li>• Improve "professional headphones" rank</li>
            <li>• Launch new backend keywords strategy</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default SEOOptimizer;
