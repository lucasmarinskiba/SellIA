import React, { useState, useEffect } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import { Users, AlertTriangle, TrendingDown } from 'lucide-react';

const SegmentationDashboard: React.FC<{ businessId: string }> = ({ businessId }) => {
  const [summary, setSummary] = useState<any>(null);
  const [rfmData, setRfmData] = useState<any[]>([]);
  const [churnRiskData, setChurnRiskData] = useState<any[]>([]);

  useEffect(() => {
    fetchSegmentationData();
  }, [businessId]);

  const fetchSegmentationData = async () => {
    try {
      const res = await fetch(`/api/v1/businesses/${businessId}/segmentation-summary`);
      const data = await res.json();

      setSummary(data);

      const rfm = [
        { name: 'Champions', value: data.rfm_distribution?.champions || 0, fill: '#10b981' },
        { name: 'Loyal', value: data.rfm_distribution?.loyal_customers || 0, fill: '#3b82f6' },
        { name: 'At Risk', value: data.rfm_distribution?.at_risk || 0, fill: '#ef4444' },
        { name: 'Need Activation', value: data.rfm_distribution?.need_activation || 0, fill: '#f59e0b' }
      ];
      setRfmData(rfm);

      const churn = [
        { name: 'Low Risk', value: data.churn_distribution?.low || 0 },
        { name: 'Medium Risk', value: data.churn_distribution?.medium || 0 },
        { name: 'High Risk', value: data.churn_distribution?.high || 0 },
        { name: 'Critical Risk', value: data.churn_distribution?.critical || 0 }
      ];
      setChurnRiskData(churn);
    } catch (error) {
      console.error('Failed to fetch segmentation data:', error);
    }
  };

  return (
    <div className="w-full space-y-6 p-6 bg-gray-50">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Customer Segmentation</h1>
        <button onClick={fetchSegmentationData} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Total Customers</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{summary?.total_customers || 0}</p>
            </div>
            <Users className="w-10 h-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Avg CLV</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">${summary?.avg_clv?.toFixed(0) || 0}</p>
            </div>
            <TrendingDown className="w-10 h-10 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Avg Engagement</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{summary?.avg_engagement?.toFixed(1) || 0}/10</p>
            </div>
            <AlertTriangle className="w-10 h-10 text-orange-500" />
          </div>
        </div>
      </div>

      {/* RFM Distribution */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">RFM Segmentation</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={rfmData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#3b82f6" name="Customers" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Churn Risk Distribution */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Churn Risk Distribution</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={churnRiskData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#ef4444" name="Customers" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* At-Risk Customers Alert */}
      <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
        <div className="flex items-start">
          <AlertTriangle className="w-6 h-6 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <h3 className="font-bold text-red-900">At-Risk Alert</h3>
            <p className="text-red-700 text-sm mt-1">
              {summary?.churn_distribution?.high + summary?.churn_distribution?.critical || 0} customers have high churn risk. Consider re-engagement campaigns.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SegmentationDashboard;
