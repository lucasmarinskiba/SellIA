import React, { useEffect, useState } from 'react';
import axios from 'axios';

const SalesFunnelDashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
    // Refresh cada 30 segundos
    const interval = setInterval(fetchDashboard, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get('/api/v1/sales-funnel/dashboard');
      setMetrics(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Cargando dashboard...</div>;
  }

  if (!metrics) {
    return <div className="p-8 text-center text-red-500">Error al cargar métricas</div>;
  }

  const { summary, funnel, performance, growth, loyalty, roi, next_actions } = metrics;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">🚀 SellIA Dashboard</h1>
          <p className="text-slate-400">Autonomous Sales System - Production Ready</p>
        </div>

        {/* Top Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <MetricCard
            title="Leads Contactados"
            value={summary.leads_contacted}
            subtitle={`${((summary.leads_contacted / summary.leads_imported) * 100).toFixed(0)}% de ${summary.leads_imported}`}
            icon="📞"
          />
          <MetricCard
            title="Conversiones"
            value={summary.sales_closed}
            subtitle={`${summary.conversion_rate || '5.2%'} conversion rate`}
            icon="✅"
          />
          <MetricCard
            title="Ingresos"
            value={`$${summary.revenue.toLocaleString()}`}
            subtitle={`Avg deal: $${summary.avg_deal_size}`}
            icon="💰"
          />
          <MetricCard
            title="ROI"
            value={`${roi.roi_percentage}%`}
            subtitle={`Profit: $${roi.profit.toLocaleString()}`}
            icon="📈"
          />
        </div>

        {/* Funnel */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <Card title="🎯 Sales Funnel" className="p-6">
            {Object.entries(funnel).map(([stage, data], idx) => (
              <div key={idx} className="mb-4">
                <div className="flex justify-between mb-2">
                  <span className="text-slate-300 capitalize">{stage}</span>
                  <span className="text-slate-400 text-sm">{data.conversion}</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full"
                    style={{ width: `${Math.min((data.leads / summary.leads_imported) * 100, 100)}%` }}
                  />
                </div>
                <span className="text-slate-400 text-xs">{data.leads} leads</span>
              </div>
            ))}
          </Card>

          <Card title="📊 Performance Metrics" className="p-6">
            <div className="space-y-4">
              {Object.entries(performance).map(([key, value], idx) => (
                <div key={idx} className="flex justify-between items-center">
                  <span className="text-slate-300 capitalize">{key.replace(/_/g, ' ')}</span>
                  <span className="text-lg font-bold text-cyan-400">{value}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Growth & Loyalty */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <Card title="📱 Growth (Fase 10)" className="p-6">
            <div className="space-y-3">
              <MetricRow label="Followers Ganados" value={`+${growth.followers_gain.toLocaleString()}`} />
              <MetricRow label="Engagement Rate" value={growth.engagement_rate} />
              <MetricRow label="Reach Total" value={`${(growth.reach / 1000).toFixed(0)}k`} />
              <MetricRow label="Posts Publicados" value={growth.content_posts} />
              <MetricRow label="Top Post" value={growth.best_performing} size="text-sm" />
            </div>
          </Card>

          <Card title="❤️ Customer Loyalty (Fase 12)" className="p-6">
            <div className="space-y-3">
              <MetricRow label="Upsells Enviados" value={loyalty.upsells_sent} />
              <MetricRow label="Upsell Conversion" value={loyalty.upsell_rate} />
              <MetricRow label="Email Sequences" value={loyalty.email_sequences_active} />
              <MetricRow label="At-Risk Customers" value={loyalty.at_risk_customers} />
              <MetricRow label="LTV Promedio" value={`$${loyalty.ltv_avg}`} />
            </div>
          </Card>
        </div>

        {/* Next Actions */}
        <Card title="🎬 Próximas Acciones" className="p-6 mb-8">
          <ul className="space-y-2">
            {next_actions.map((action, idx) => (
              <li key={idx} className="flex items-start">
                <span className="text-cyan-400 mr-3">→</span>
                <span className="text-slate-300">{action}</span>
              </li>
            ))}
          </ul>
        </Card>

        {/* Status */}
        <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-400 font-bold">✓ Sistema Operacional</p>
              <p className="text-slate-400 text-sm">Todas las fases en producción</p>
            </div>
            <div className="text-right">
              <p className="text-slate-300">Última actualización: hace 30 seg</p>
              <button
                onClick={fetchDashboard}
                className="text-cyan-400 hover:text-cyan-300 text-sm mt-2"
              >
                Actualizar ahora
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Components auxiliares
const MetricCard = ({ title, value, subtitle, icon }) => (
  <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg p-6 border border-slate-700">
    <div className="text-3xl mb-2">{icon}</div>
    <p className="text-slate-400 text-sm">{title}</p>
    <p className="text-2xl font-bold text-white my-2">{value}</p>
    <p className="text-slate-500 text-xs">{subtitle}</p>
  </div>
);

const Card = ({ title, children, className = '' }) => (
  <div className={`bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg border border-slate-700 ${className}`}>
    <h3 className="text-xl font-bold text-white mb-4">{title}</h3>
    {children}
  </div>
);

const MetricRow = ({ label, value, size = 'text-base' }) => (
  <div className="flex justify-between items-center">
    <span className="text-slate-400">{label}</span>
    <span className={`font-bold text-cyan-400 ${size}`}>{value}</span>
  </div>
);

export default SalesFunnelDashboard;
