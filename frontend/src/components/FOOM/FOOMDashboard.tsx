/**
 * FOOM Dashboard - Campaign Management & Analytics
 */

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { LineChart } from '@/components/ui/Charts';

interface Campaign {
  id: string;
  name: string;
  campaign_type: string;
  status: string;
  summary: {
    total_conversions: number;
    total_revenue: number;
    avg_conversion_rate: number;
    avg_aov: number;
  };
}

export const FOOMDashboard: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCampaign, setSelectedCampaign] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<any[]>([]);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/fomo/analytics', {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || localStorage.getItem('token')}` },
      });
      const data = await res.json();
      setCampaigns(data);
    } catch (err) {
      console.error('Error fetching campaigns:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchMetrics = async (campaignId: string) => {
    try {
      const res = await fetch(`/api/fomo/analytics/${campaignId}/metrics?days=30`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || localStorage.getItem('token')}` },
      });
      const data = await res.json();
      setMetrics(data);
    } catch (err) {
      console.error('Error fetching metrics:', err);
    }
  };

  const handleSelectCampaign = (id: string) => {
    setSelectedCampaign(id);
    fetchMetrics(id);
  };

  if (loading) {
    return <div className="p-8 text-center">Cargando...</div>;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-4xl font-bold mb-8">Dashboard FOOM 🚀</h1>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">Campañas activas</div>
          <div className="text-3xl font-bold">
            {campaigns.filter(c => c.status === 'active').length}
          </div>
        </Card>

        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">Conversiones totales</div>
          <div className="text-3xl font-bold">
            {campaigns.reduce((sum, c) => sum + (c.summary?.total_conversions || 0), 0)}
          </div>
        </Card>

        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">Ingresos totales</div>
          <div className="text-3xl font-bold">
            ${campaigns.reduce((sum, c) => sum + (c.summary?.total_revenue || 0), 0).toFixed(2)}
          </div>
        </Card>

        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">Conversion Rate promedio</div>
          <div className="text-3xl font-bold">
            {(
              campaigns.reduce((sum, c) => sum + (c.summary?.avg_conversion_rate || 0), 0) /
              Math.max(campaigns.length, 1)
            ).toFixed(2)}
            %
          </div>
        </Card>
      </div>

      {/* Campaigns Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {campaigns.map(campaign => (
          <Card
            key={campaign.id}
            className={`p-6 cursor-pointer transition ${
              selectedCampaign === campaign.id
                ? 'ring-2 ring-blue-500'
                : 'hover:shadow-lg'
            }`}
            onClick={() => handleSelectCampaign(campaign.id)}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">{campaign.name}</h3>
              <span className={`px-2 py-1 rounded text-xs font-semibold ${
                campaign.status === 'active'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {campaign.status.toUpperCase()}
              </span>
            </div>

            <div className="space-y-2 text-sm">
              <div>
                <span className="text-gray-600">Tipo:</span>
                <span className="ml-2 font-semibold">{campaign.campaign_type}</span>
              </div>
              <div>
                <span className="text-gray-600">Conversiones:</span>
                <span className="ml-2 font-semibold">{campaign.summary.total_conversions}</span>
              </div>
              <div>
                <span className="text-gray-600">Ingresos:</span>
                <span className="ml-2 font-semibold">
                  ${campaign.summary.total_revenue.toFixed(2)}
                </span>
              </div>
              <div>
                <span className="text-gray-600">CR:</span>
                <span className="ml-2 font-semibold">
                  {campaign.summary.avg_conversion_rate.toFixed(2)}%
                </span>
              </div>
              <div>
                <span className="text-gray-600">AOV:</span>
                <span className="ml-2 font-semibold">
                  ${campaign.summary.avg_aov.toFixed(2)}
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Metrics Chart */}
      {selectedCampaign && metrics.length > 0 && (
        <Card className="p-6">
          <h2 className="text-2xl font-bold mb-4">Métricas de los últimos 30 días</h2>
          <LineChart
            data={metrics}
            xKey="date"
            yKeys={['conversions', 'impressions']}
            title="Conversions vs Impressions"
          />
        </Card>
      )}

      {/* Empty state */}
      {campaigns.length === 0 && (
        <Card className="p-12 text-center">
          <p className="text-gray-600 mb-4">No hay campañas FOOM aún.</p>
          <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            Crear primera campaña
          </button>
        </Card>
      )}
    </div>
  );
};

export default FOOMDashboard;
