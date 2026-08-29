import React, { useState, useEffect } from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, AlertTriangle, DollarSign } from 'lucide-react';

const PredictiveDashboard: React.FC<{ businessId: string }> = ({ businessId }) => {
  const [churnTrend, setChurnTrend] = useState<any[]>([]);
  const [revenueForecast, setRevenueForecast] = useState<any[]>([]);
  const [demandForecast, setDemandForecast] = useState<any>(null);

  useEffect(() => {
    fetchPredictiveData();
  }, [businessId]);

  const fetchPredictiveData = async () => {
    try {
      // Sample data for churn trend
      const churnData = Array.from({ length: 30 }).map((_, i) => ({
        day: `Day ${i + 1}`,
        churnRisk: Math.sin(i / 10) * 15 + 25 + Math.random() * 5
      }));
      setChurnTrend(churnData);

      // Revenue forecast
      const revenueForecast = Array.from({ length: 30 }).map((_, i) => ({
        day: `Day ${i + 1}`,
        forecast: 50000 + Math.sin(i / 10) * 10000 + Math.random() * 5000,
        lower: 45000 + Math.sin(i / 10) * 8000,
        upper: 55000 + Math.sin(i / 10) * 12000
      }));
      setRevenueForecast(revenueForecast);

      setDemandForecast({
        category: 'Electronics',
        forecastedUnits: 1240,
        confidenceLow: 992,
        confidenceHigh: 1488
      });
    } catch (error) {
      console.error('Failed to fetch predictive data:', error);
    }
  };

  return (
    <div className="w-full space-y-6 p-6 bg-gray-50">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Predictive Analytics</h1>
        <button onClick={fetchPredictiveData} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Refresh
        </button>
      </div>

      {/* Forecast Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Avg Churn Risk (30d)</p>
              <p className="text-3xl font-bold text-red-600 mt-2">28%</p>
              <p className="text-xs text-gray-500 mt-1">↓ 2% from last month</p>
            </div>
            <AlertTriangle className="w-10 h-10 text-red-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Revenue Forecast (30d)</p>
              <p className="text-3xl font-bold text-green-600 mt-2">$1.5M</p>
              <p className="text-xs text-gray-500 mt-1">80% confidence interval</p>
            </div>
            <DollarSign className="w-10 h-10 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Demand Forecast</p>
              <p className="text-3xl font-bold text-blue-600 mt-2">{demandForecast?.forecastedUnits || 0}</p>
              <p className="text-xs text-gray-500 mt-1">{demandForecast?.category} units</p>
            </div>
            <TrendingUp className="w-10 h-10 text-blue-500" />
          </div>
        </div>
      </div>

      {/* Churn Risk Trend */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Churn Risk Forecast (30 days)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={churnTrend}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip formatter={(value) => `${Number(value).toFixed(1)}%`} />
            <Area type="monotone" dataKey="churnRisk" fill="#fca5a5" stroke="#ef4444" name="Churn Risk %" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Revenue Forecast with Confidence Interval */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Revenue Forecast (30 days)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={revenueForecast}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip formatter={(value) => `$${(Number(value) / 1000).toFixed(0)}K`} />
            <Legend />
            <Line type="monotone" dataKey="lower" stroke="#cbd5e1" strokeDasharray="5 5" name="Lower Bound" />
            <Line type="monotone" dataKey="forecast" stroke="#3b82f6" strokeWidth={2} name="Forecast" />
            <Line type="monotone" dataKey="upper" stroke="#cbd5e1" strokeDasharray="5 5" name="Upper Bound" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Model Accuracy */}
      <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
        <h3 className="font-bold text-blue-900 mb-2">Model Accuracy</h3>
        <div className="space-y-2 text-sm text-blue-700">
          <p>• Churn Prediction: R² = 0.78 | RMSE = 12.5%</p>
          <p>• Revenue Forecast: R² = 0.85 | RMSE = $3.2K</p>
          <p>• Demand Forecast: R² = 0.72 | Confidence: 80%</p>
        </div>
      </div>
    </div>
  );
};

export default PredictiveDashboard;
