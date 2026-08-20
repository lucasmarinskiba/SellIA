import React, { useState } from 'react';

interface CustomerMetrics {
  rfmScore: number;
  clv: number;
  churnRisk: number;
  propensity: number;
  nps: number;
  engagement: number;
}

interface TimelineEvent {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  value?: number;
}

const Customer360: React.FC = () => {
  const [customer] = useState({
    id: '12345',
    name: 'John Smith',
    company: 'Acme Corporation',
    email: 'john.smith@acme.com',
    phone: '+1 (555) 123-4567',
    industry: 'Technology',
    employeeCount: 5000,
    annualRevenue: '$500M+',
    avatar: '👤',
  });

  const [metrics] = useState<CustomerMetrics>({
    rfmScore: 85,
    clv: 125000,
    churnRisk: 15,
    propensity: 78,
    nps: 72,
    engagement: 82,
  });

  const [timeline] = useState<TimelineEvent[]>([
    { id: '1', type: 'deal_won', description: 'Enterprise Package Deal Won', timestamp: '2 days ago', value: 50000 },
    { id: '2', type: 'call', description: 'Strategic Planning Call', timestamp: '5 days ago' },
    { id: '3', type: 'email', description: 'Quarterly Business Review Sent', timestamp: '1 week ago' },
    { id: '4', type: 'proposal', description: 'Expansion Proposal Sent', timestamp: '2 weeks ago', value: 85000 },
    { id: '5', type: 'training', description: 'Advanced Features Training', timestamp: '3 weeks ago' },
    { id: '6', type: 'contract', description: 'Annual Contract Signed', timestamp: '1 month ago', value: 180000 },
  ]);

  const [interactions] = useState([
    { type: 'Email Opens', count: 24, icon: '📧' },
    { type: 'Link Clicks', count: 47, icon: '🔗' },
    { type: 'Calls', count: 12, icon: '📞' },
    { type: 'Meetings', count: 8, icon: '🤝' },
  ]);

  const scoreColor = (score: number) => {
    if (score >= 75) return 'text-green-400';
    if (score >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header with Customer Info */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg p-8 mb-8 text-white">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-6">
              <div className="text-7xl">{customer.avatar}</div>
              <div>
                <h1 className="text-4xl font-bold mb-2">{customer.name}</h1>
                <p className="text-lg opacity-90">{customer.company}</p>
              </div>
            </div>
            <button className="px-6 py-2 bg-white text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition">
              Send Message
            </button>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div>
              <p className="text-sm opacity-80">Email</p>
              <p className="font-semibold">{customer.email}</p>
            </div>
            <div>
              <p className="text-sm opacity-80">Phone</p>
              <p className="font-semibold">{customer.phone}</p>
            </div>
            <div>
              <p className="text-sm opacity-80">Industry</p>
              <p className="font-semibold">{customer.industry}</p>
            </div>
            <div>
              <p className="text-sm opacity-80">Company Size</p>
              <p className="font-semibold">{customer.employeeCount} employees</p>
            </div>
          </div>
        </div>

        {/* AI Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Key Metrics */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h2 className="text-2xl font-bold text-white mb-6">AI-Powered Insights</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <p className="text-slate-400">RFM Score (Value)</p>
                  <p className={`font-bold text-lg ${scoreColor(metrics.rfmScore)}`}>{metrics.rfmScore}/100</p>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full" style={{ width: `${metrics.rfmScore}%` }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <p className="text-slate-400">Customer Lifetime Value</p>
                  <p className="text-green-400 font-bold text-lg">${(metrics.clv / 1000).toFixed(0)}K</p>
                </div>
                <p className="text-slate-500 text-sm">Expected total revenue over lifetime</p>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <p className="text-slate-400">Churn Risk</p>
                  <p className={`font-bold text-lg ${metrics.churnRisk > 50 ? 'text-red-400' : 'text-green-400'}`}>{metrics.churnRisk}%</p>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div className="bg-red-500 h-2 rounded-full" style={{ width: `${metrics.churnRisk}%` }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <p className="text-slate-400">Buy Propensity</p>
                  <p className={`font-bold text-lg ${scoreColor(metrics.propensity)}`}>{metrics.propensity}%</p>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${metrics.propensity}%` }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <p className="text-slate-400">NPS Score</p>
                  <p className={`font-bold text-lg ${scoreColor(metrics.nps)}`}>{metrics.nps}</p>
                </div>
                <p className="text-slate-500 text-sm">Promoter - Likely to recommend</p>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <p className="text-slate-400">Overall Engagement</p>
                  <p className={`font-bold text-lg ${scoreColor(metrics.engagement)}`}>{metrics.engagement}%</p>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div className="bg-yellow-500 h-2 rounded-full" style={{ width: `${metrics.engagement}%` }}></div>
                </div>
              </div>
            </div>
          </div>

          {/* Interaction Stats */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h2 className="text-2xl font-bold text-white mb-6">Interactions</h2>
            <div className="space-y-4">
              {interactions.map((interaction, idx) => (
                <div key={idx} className="flex items-center justify-between p-4 bg-slate-700 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{interaction.icon}</span>
                    <p className="text-white font-semibold">{interaction.type}</p>
                  </div>
                  <p className="text-2xl font-bold text-blue-400">{interaction.count}</p>
                </div>
              ))}
            </div>

            <div className="mt-6 p-4 bg-slate-700 rounded-lg border-l-4 border-blue-500">
              <p className="text-slate-400 text-sm mb-2">💡 AI Recommendation</p>
              <p className="text-white">Schedule a quarterly business review. Customer shows high engagement and buy propensity. Ideal time to discuss expansion.</p>
            </div>
          </div>
        </div>

        {/* Timeline */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h2 className="text-2xl font-bold text-white mb-6">Customer Journey</h2>
          <div className="space-y-4">
            {timeline.map((event, idx) => (
              <div key={event.id} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                    {idx + 1}
                  </div>
                  {idx < timeline.length - 1 && <div className="w-1 bg-slate-600 flex-grow my-2" style={{ height: '40px' }}></div>}
                </div>
                <div className="flex-grow pb-4">
                  <div className="bg-slate-700 p-4 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <p className="text-white font-semibold capitalize">{event.type.replace('_', ' ')}</p>
                      <p className="text-slate-400 text-sm">{event.timestamp}</p>
                    </div>
                    <p className="text-slate-300">{event.description}</p>
                    {event.value && <p className="text-green-400 font-bold mt-2">${(event.value / 1000).toFixed(0)}K</p>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
          <button className="p-4 bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg text-white hover:from-blue-700 hover:to-blue-800 transition font-semibold">
            🤖 Send AI-Generated Email
          </button>
          <button className="p-4 bg-gradient-to-r from-green-600 to-green-700 rounded-lg text-white hover:from-green-700 hover:to-green-800 transition font-semibold">
            📞 Schedule AI Call Coaching
          </button>
          <button className="p-4 bg-gradient-to-r from-purple-600 to-purple-700 rounded-lg text-white hover:from-purple-700 hover:to-purple-800 transition font-semibold">
            🎯 Generate Next Best Action
          </button>
        </div>
      </div>
    </div>
  );
};

export default Customer360;
