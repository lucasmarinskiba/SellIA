import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface KPI {
  label: string;
  value: number | string;
  trend?: number;
  icon: string;
}

const Dashboard: React.FC = () => {
  const [kpis, setKpis] = useState<KPI[]>([
    { label: 'Total Revenue', value: '$450,000', trend: 12, icon: '💰' },
    { label: 'Active Deals', value: '89', trend: 8, icon: '🤝' },
    { label: 'Conversion Rate', value: '18%', trend: 3, icon: '📈' },
    { label: 'Avg Deal Size', value: '$45,000', trend: -2, icon: '💼' },
  ]);

  const [pipelineData] = useState([
    { stage: 'Prospect', value: 45 },
    { stage: 'Qualified', value: 38 },
    { stage: 'Proposal', value: 23 },
    { stage: 'Negotiation', value: 12 },
    { stage: 'Won', value: 98 },
  ]);

  const [forecastData] = useState([
    { month: 'Jan', forecast: 350000, actual: 380000 },
    { month: 'Feb', forecast: 380000, actual: 420000 },
    { month: 'Mar', forecast: 410000, actual: 450000 },
    { month: 'Apr', forecast: 440000, actual: 480000 },
  ]);

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Sales Dashboard</h1>
          <p className="text-slate-400">Real-time performance overview</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {kpis.map((kpi, idx) => (
            <div key={idx} className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-blue-500 transition">
              <div className="flex justify-between items-start mb-4">
                <span className="text-3xl">{kpi.icon}</span>
                {kpi.trend && (
                  <span className={`text-sm font-semibold ${kpi.trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {kpi.trend > 0 ? '+' : ''}{kpi.trend}%
                  </span>
                )}
              </div>
              <p className="text-slate-400 text-sm mb-2">{kpi.label}</p>
              <p className="text-2xl font-bold text-white">{kpi.value}</p>
            </div>
          ))}
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Pipeline Distribution */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-white mb-4">Pipeline by Stage</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={pipelineData} cx="50%" cy="50%" labelLine={false} label={({ name, value }) => `${name} (${value})`} outerRadius={100} fill="#8884d8" dataKey="value">
                  {pipelineData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Revenue Forecast */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-white mb-4">Revenue Forecast vs Actual</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={forecastData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="month" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }} />
                <Legend />
                <Line type="monotone" dataKey="forecast" stroke="#10b981" strokeWidth={2} name="Forecast" />
                <Line type="monotone" dataKey="actual" stroke="#3b82f6" strokeWidth={2} name="Actual" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Deal Distribution */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 lg:col-span-2">
            <h2 className="text-xl font-bold text-white mb-4">Deal Distribution by Value</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={pipelineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="stage" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }} />
                <Bar dataKey="value" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 mt-8">
          <h2 className="text-xl font-bold text-white mb-4">Recent Activity</h2>
          <div className="space-y-4">
            {[
              { action: 'Deal Won', customer: 'Acme Corp', amount: '$125,000', time: '2 hours ago', icon: '🎉' },
              { action: 'Proposal Sent', customer: 'TechStart Inc', amount: '$85,000', time: '4 hours ago', icon: '📨' },
              { action: 'Call Scheduled', customer: 'Global Ltd', amount: '$45,000', time: '6 hours ago', icon: '📞' },
              { action: 'Lead Qualified', customer: 'Innovation Co', amount: '$120,000', time: '1 day ago', icon: '✅' },
            ].map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-4 bg-slate-700 rounded border border-slate-600">
                <div className="flex items-center gap-4">
                  <span className="text-2xl">{item.icon}</span>
                  <div>
                    <p className="text-white font-semibold">{item.action}</p>
                    <p className="text-slate-400 text-sm">{item.customer}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-white font-semibold">{item.amount}</p>
                  <p className="text-slate-400 text-sm">{item.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
