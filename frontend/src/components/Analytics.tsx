import React, { useState } from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const Analytics: React.FC = () => {
  const [period, setPeriod] = useState('30days');

  const performanceData = [
    { day: 'Mon', deals: 12, calls: 24, emails: 45 },
    { day: 'Tue', deals: 15, calls: 28, emails: 52 },
    { day: 'Wed', deals: 18, calls: 32, emails: 48 },
    { day: 'Thu', deals: 14, calls: 26, emails: 58 },
    { day: 'Fri', deals: 22, calls: 35, emails: 62 },
    { day: 'Sat', deals: 8, calls: 12, emails: 25 },
    { day: 'Sun', deals: 5, calls: 8, emails: 15 },
  ];

  const conversionData = [
    { stage: 'Prospect', value: 1000 },
    { stage: 'Qualified', value: 650 },
    { stage: 'Proposal', value: 380 },
    { stage: 'Negotiation', value: 120 },
    { stage: 'Won', value: 98 },
  ];

  const channelData = [
    { name: 'Email', value: 35, color: '#3b82f6' },
    { name: 'LinkedIn', value: 25, color: '#0a66c2' },
    { name: 'Phone', value: 20, color: '#10b981' },
    { name: 'SMS', value: 15, color: '#f59e0b' },
    { name: 'Direct', value: 5, color: '#8b5cf6' },
  ];

  const repData = [
    { name: 'Alice Johnson', quota: 500000, actual: 560000, deals: 45 },
    { name: 'Bob Smith', quota: 500000, actual: 480000, deals: 42 },
    { name: 'Charlie Davis', quota: 500000, actual: 520000, deals: 48 },
    { name: 'Diana Wilson', quota: 500000, actual: 450000, deals: 38 },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Analytics & Insights</h1>
            <p className="text-slate-400">Performance metrics and team analytics</p>
          </div>
          <div className="flex gap-2">
            {['7days', '30days', '90days', 'ytd'].map(p => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-4 py-2 rounded font-semibold transition ${
                  period === p
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {p === '7days' ? 'Last 7 Days' : p === '30days' ? 'Last 30 Days' : p === '90days' ? 'Last 90 Days' : 'YTD'}
              </button>
            ))}
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
          {[
            { label: 'Total Revenue', value: '$2.8M', icon: '💰', trend: '+15%' },
            { label: 'Won Deals', value: '98', icon: '🎉', trend: '+23%' },
            { label: 'Conversion Rate', value: '9.8%', icon: '📈', trend: '+2.1%' },
            { label: 'Avg Deal Size', value: '$45K', icon: '💼', trend: '+8%' },
            { label: 'Sales Cycle', value: '35 days', icon: '⏱️', trend: '-5 days' },
          ].map((metric, idx) => (
            <div key={idx} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="flex justify-between items-start mb-2">
                <span className="text-2xl">{metric.icon}</span>
                <p className="text-green-400 text-sm font-semibold">{metric.trend}</p>
              </div>
              <p className="text-slate-400 text-sm mb-1">{metric.label}</p>
              <p className="text-2xl font-bold text-white">{metric.value}</p>
            </div>
          ))}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Activity Performance */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-white mb-4">Weekly Activity</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="day" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }} />
                <Legend />
                <Line type="monotone" dataKey="deals" stroke="#3b82f6" strokeWidth={2} name="Deals" />
                <Line type="monotone" dataKey="calls" stroke="#10b981" strokeWidth={2} name="Calls" />
                <Line type="monotone" dataKey="emails" stroke="#f59e0b" strokeWidth={2} name="Emails" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Channel Distribution */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-white mb-4">Success by Channel</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={channelData} cx="50%" cy="50%" labelLine={false} label={({ name, value }) => `${name} (${value}%)`} outerRadius={100} fill="#8884d8" dataKey="value">
                  {channelData.map((item, index) => (
                    <Cell key={`cell-${index}`} fill={item.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Conversion Funnel */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-white mb-4">Conversion Funnel</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={conversionData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#9ca3af" />
                <YAxis dataKey="stage" type="category" stroke="#9ca3af" width={100} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }} />
                <Bar dataKey="value" fill="#3b82f6" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Team Leaderboard */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-white mb-4">Sales Team Leaderboard</h2>
            <div className="space-y-3">
              {repData.map((rep, idx) => (
                <div key={idx} className="bg-slate-700 p-4 rounded-lg">
                  <div className="flex justify-between items-start mb-2">
                    <p className="text-white font-semibold">{idx + 1}. {rep.name}</p>
                    <p className="text-green-400 font-bold">{Math.round((rep.actual / rep.quota) * 100)}%</p>
                  </div>
                  <div className="w-full bg-slate-600 rounded-full h-2 mb-2">
                    <div className="bg-green-500 h-2 rounded-full" style={{ width: `${Math.min((rep.actual / rep.quota) * 100, 100)}%` }}></div>
                  </div>
                  <div className="flex justify-between text-slate-400 text-sm">
                    <span>${(rep.actual / 1000).toFixed(0)}K / ${(rep.quota / 1000).toFixed(0)}K</span>
                    <span>{rep.deals} deals</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* AI Insights */}
        <div className="bg-gradient-to-r from-blue-900 to-purple-900 rounded-lg p-8 border border-blue-700">
          <h2 className="text-2xl font-bold text-white mb-4">🤖 AI-Powered Insights</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-800 bg-opacity-50 p-4 rounded-lg">
              <p className="text-slate-300 text-sm"><strong>📊 Revenue Trend:</strong> On track to exceed Q4 target by 12%. Email channel showing 34% YoY growth.</p>
            </div>
            <div className="bg-slate-800 bg-opacity-50 p-4 rounded-lg">
              <p className="text-slate-300 text-sm"><strong>⚠️ Attention Needed:</strong> Bob Smith 4% below quota. Recommend peer coaching with top performer Alice.</p>
            </div>
            <div className="bg-slate-800 bg-opacity-50 p-4 rounded-lg">
              <p className="text-slate-300 text-sm"><strong>🚀 Opportunity:</strong> LinkedIn channel has 2.1x better conversion rate than SMS. Reallocate budget by 15%.</p>
            </div>
            <div className="bg-slate-800 bg-opacity-50 p-4 rounded-lg">
              <p className="text-slate-300 text-sm"><strong>✨ Best Practice:</strong> Deals with proposal sent within 24 hours close 28% faster. Train team on urgency.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
