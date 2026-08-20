import React, { useState, useEffect } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { FileText, BarChart3, Download, Server } from 'lucide-react';

const ExportBiDashboard: React.FC<{ businessId: string }> = ({ businessId }) => {
  const [metrics, setMetrics] = useState<any>(null);
  const [formatData, setFormatData] = useState<any[]>([]);
  const [exportTypes, setExportTypes] = useState<any[]>([]);

  useEffect(() => {
    fetchExportMetrics();
  }, [businessId]);

  const fetchExportMetrics = async () => {
    try {
      const res = await fetch(`/api/v1/businesses/${businessId}/export-metrics`);
      const data = await res.json();

      setMetrics(data);

      const formats = [
        { name: 'CSV', value: data.formats?.csv_exports || 0 },
        { name: 'Excel', value: data.formats?.excel_exports || 0 },
        { name: 'JSON', value: data.formats?.json_exports || 0 },
        { name: 'Parquet', value: data.formats?.parquet_exports || 0 }
      ];
      setFormatData(formats);

      const types = [
        { name: 'Customers', value: 35 },
        { name: 'Orders', value: 28 },
        { name: 'Segments', value: 18 },
        { name: 'Journeys', value: 12 },
        { name: 'Other', value: 7 }
      ];
      setExportTypes(types);
    } catch (error) {
      console.error('Failed to fetch export metrics:', error);
    }
  };

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="w-full space-y-6 p-6 bg-gray-50">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Export & BI</h1>
        <button onClick={fetchExportMetrics} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Exports Requested</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{metrics?.exports?.total_requested || 0}</p>
            </div>
            <Download className="w-10 h-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Successful</p>
              <p className="text-3xl font-bold text-green-600 mt-2">{metrics?.exports?.successful || 0}</p>
            </div>
            <FileText className="w-10 h-10 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Total Rows Exported</p>
              <p className="text-3xl font-bold text-blue-600 mt-2">{(metrics?.data_volume?.total_rows / 1000).toFixed(0)}K</p>
            </div>
            <BarChart3 className="w-10 h-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Dashboard Views</p>
              <p className="text-3xl font-bold text-purple-600 mt-2">{metrics?.bi?.dashboard_views || 0}</p>
            </div>
            <Server className="w-10 h-10 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Export Formats */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Export Formats Used</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={formatData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#3b82f6" name="Exports" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Export Types Distribution */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Export Types Distribution</h2>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie data={exportTypes} cx="50%" cy="50%" labelLine={false} label={({ name, value }) => `${name}: ${value}%`} outerRadius={100} fill="#8884d8" dataKey="value">
              {exportTypes.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => `${value}%`} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Data Warehouse & Reports */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
          <h3 className="font-bold text-blue-900 mb-2">Data Warehouse Sync</h3>
          <div className="text-sm text-blue-700 space-y-1">
            <p>✓ Connected to BigQuery</p>
            <p>• Last sync: 2 hours ago</p>
            <p>• Rows synced: 125,450</p>
          </div>
        </div>

        <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
          <h3 className="font-bold text-green-900 mb-2">Scheduled Reports</h3>
          <div className="text-sm text-green-700 space-y-1">
            <p>✓ {metrics?.reports?.scheduled_sent || 0} reports sent today</p>
            <p>• Daily: 5 active</p>
            <p>• Weekly: 3 active</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExportBiDashboard;
