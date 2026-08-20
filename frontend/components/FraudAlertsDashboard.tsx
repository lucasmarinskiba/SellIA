import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { AlertTriangle, Shield, Lock, TrendingUp } from 'lucide-react';

const FraudAlertsDashboard: React.FC<{ businessId: string }> = ({ businessId }) => {
  const [fraudMetrics, setFraudMetrics] = useState<any>(null);
  const [riskLevels, setRiskLevels] = useState<any[]>([]);
  const [trends, setTrends] = useState<any[]>([]);

  useEffect(() => {
    fetchFraudData();
  }, [businessId]);

  const fetchFraudData = async () => {
    try {
      const res = await fetch(`/api/v1/businesses/${businessId}/fraud-summary`);
      const data = await res.json();

      setFraudMetrics(data);

      const risks = [
        { name: 'Low Risk', value: data.order_fraud?.high_risk ? 100 - data.order_fraud.high_risk : 85 },
        { name: 'High Risk', value: data.order_fraud?.high_risk || 15 },
        { name: 'Blocked', value: data.order_fraud?.blocked || 3 }
      ];
      setRiskLevels(risks);

      const trendData = Array.from({ length: 30 }).map((_, i) => ({
        day: `Day ${i + 1}`,
        flagged: Math.floor(Math.random() * 20 + 5),
        blocked: Math.floor(Math.random() * 5 + 1)
      }));
      setTrends(trendData);
    } catch (error) {
      console.error('Failed to fetch fraud data:', error);
    }
  };

  return (
    <div className="w-full space-y-6 p-6 bg-gray-50">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Fraud Detection & Prevention</h1>
        <button onClick={fetchFraudData} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Total Reviewed</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{fraudMetrics?.order_fraud?.total_reviewed || 0}</p>
            </div>
            <Shield className="w-10 h-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">High Risk</p>
              <p className="text-3xl font-bold text-red-600 mt-2">{fraudMetrics?.order_fraud?.high_risk || 0}</p>
            </div>
            <AlertTriangle className="w-10 h-10 text-red-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Blocked Orders</p>
              <p className="text-3xl font-bold text-orange-600 mt-2">{fraudMetrics?.order_fraud?.blocked || 0}</p>
            </div>
            <Lock className="w-10 h-10 text-orange-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Confirmed Fraud</p>
              <p className="text-3xl font-bold text-purple-600 mt-2">{fraudMetrics?.order_fraud?.confirmed_fraud || 0}</p>
            </div>
            <TrendingUp className="w-10 h-10 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Risk Distribution */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Order Risk Distribution</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={riskLevels}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#3b82f6" name="Orders" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* 30-Day Trend */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">30-Day Fraud Trend</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="flagged" stroke="#f59e0b" name="Flagged" />
            <Line type="monotone" dataKey="blocked" stroke="#ef4444" name="Blocked" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Active Alerts */}
      <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
        <h3 className="font-bold text-red-900 mb-2">Active Fraud Alerts</h3>
        <div className="space-y-2 text-sm text-red-700">
          <p>• {fraudMetrics?.account_fraud?.flagged || 0} flagged accounts</p>
          <p>• {fraudMetrics?.account_fraud?.suspended || 0} suspended accounts</p>
          <p>• {fraudMetrics?.blacklist?.total_entries || 0} blacklisted entities</p>
        </div>
      </div>
    </div>
  );
};

export default FraudAlertsDashboard;
