import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Users, Gift, TrendingUp, Award } from 'lucide-react';

const LoyaltyDashboard: React.FC<{ businessId: string }> = ({ businessId }) => {
  const [metrics, setMetrics] = useState<any>(null);
  const [tierDistribution, setTierDistribution] = useState<any[]>([]);
  const [rewards, setRewards] = useState<any[]>([]);

  useEffect(() => {
    fetchLoyaltyMetrics();
  }, [businessId]);

  const fetchLoyaltyMetrics = async () => {
    try {
      const res = await fetch(`/api/v1/businesses/${businessId}/loyalty-metrics`);
      const data = await res.json();

      setMetrics(data);

      const tiers = [
        { name: 'Bronze', value: data.members?.bronze || 0 },
        { name: 'Silver', value: data.members?.silver || 0 },
        { name: 'Gold', value: data.members?.gold || 0 },
        { name: 'Platinum', value: data.members?.platinum || 0 }
      ];
      setTierDistribution(tiers);

      const rewardData = [
        { name: 'Redeemed', value: data.points?.redeemed || 0 },
        { name: 'Remaining', value: data.points?.issued - data.points?.redeemed || 0 }
      ];
      setRewards(rewardData);
    } catch (error) {
      console.error('Failed to fetch loyalty metrics:', error);
    }
  };

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

  return (
    <div className="w-full space-y-6 p-6 bg-gray-50">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Loyalty Program</h1>
        <button onClick={fetchLoyaltyMetrics} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Total Members</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{metrics?.members?.total || 0}</p>
            </div>
            <Users className="w-10 h-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Active Members</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{metrics?.members?.active || 0}</p>
            </div>
            <TrendingUp className="w-10 h-10 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Points Issued</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{(metrics?.points?.issued / 1000).toFixed(0)}K</p>
            </div>
            <Award className="w-10 h-10 text-orange-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Redemption Rate</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {metrics?.points?.issued > 0 ? ((metrics.points.redeemed / metrics.points.issued) * 100).toFixed(0) : 0}%
              </p>
            </div>
            <Gift className="w-10 h-10 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Tier Distribution */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Member Distribution by Tier</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={tierDistribution}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#3b82f6" name="Members" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Points Status */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Points Status</h2>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie data={rewards} cx="50%" cy="50%" labelLine={false} label={({ name, value }) => `${name}: ${value}`} outerRadius={100} fill="#8884d8" dataKey="value">
              {[COLORS[0], COLORS[1]].map((color, index) => (
                <Cell key={`cell-${index}`} fill={color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default LoyaltyDashboard;
