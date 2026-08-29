import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AlertCircle, Bell, TrendingUp, CheckCircle } from 'lucide-react';

const AlertsDashboard: React.FC<{ businessId: string }> = ({ businessId }) => {
  const [metrics, setMetrics] = useState<any>(null);
  const [alertRules, setAlertRules] = useState<any[]>([]);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [createMode, setCreateMode] = useState(false);
  const [newRule, setNewRule] = useState({
    name: '',
    alert_type: 'deal_closing',
    priority: 'medium',
    channels: ['in_app', 'email']
  });

  useEffect(() => {
    fetchMetrics();
    fetchAlertRules();
  }, [businessId]);

  const fetchMetrics = async () => {
    try {
      const res = await fetch(`/api/v1/businesses/${businessId}/notifications/metrics`);
      const data = await res.json();
      setMetrics(data);

      // Generate trend data
      const trend = Array.from({ length: 30 }).map((_, i) => ({
        day: `Day ${i + 1}`,
        triggered: Math.floor(Math.random() * 50 + 10),
        delivered: Math.floor(Math.random() * 45 + 5),
      }));
      setTrendData(trend);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    }
  };

  const fetchAlertRules = async () => {
    try {
      const res = await fetch(`/api/v1/businesses/${businessId}/alerts/rules`);
      const data = await res.json();
      setAlertRules(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch alert rules:', error);
    }
  };

  const createAlertRule = async () => {
    try {
      await fetch(`/api/v1/businesses/${businessId}/alerts/rules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newRule)
      });
      setCreateMode(false);
      setNewRule({
        name: '',
        alert_type: 'deal_closing',
        priority: 'medium',
        channels: ['in_app', 'email']
      });
      fetchAlertRules();
    } catch (error) {
      console.error('Failed to create alert rule:', error);
    }
  };

  return (
    <div className="w-full space-y-6 p-6 bg-gray-50">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Alertas y Notificaciones</h1>
        <button
          onClick={() => setCreateMode(!createMode)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + Nueva regla de alerta
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Notificaciones totales</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{metrics?.total_notifications || 0}</p>
            </div>
            <Bell className="w-10 h-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Entregadas</p>
              <p className="text-3xl font-bold text-green-600 mt-2">{metrics?.successful || 0}</p>
            </div>
            <CheckCircle className="w-10 h-10 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Fallidas</p>
              <p className="text-3xl font-bold text-red-600 mt-2">{metrics?.failed || 0}</p>
            </div>
            <AlertCircle className="w-10 h-10 text-red-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Tasa de lectura</p>
              <p className="text-3xl font-bold text-purple-600 mt-2">{metrics?.read_rate_pct || 0}%</p>
            </div>
            <TrendingUp className="w-10 h-10 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Alert Trend */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Tendencia de alertas (30 días)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="triggered" stroke="#3b82f6" name="Disparadas" />
            <Line type="monotone" dataKey="delivered" stroke="#10b981" name="Entregadas" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Create New Rule */}
      {createMode && (
        <div className="bg-white p-6 rounded-lg shadow border border-blue-200">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Nueva regla de alerta</h3>
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Nombre de la regla"
              value={newRule.name}
              onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />

            <select
              value={newRule.alert_type}
              onChange={(e) => setNewRule({ ...newRule, alert_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="deal_closing">Deal cerrando</option>
              <option value="churn_risk">Riesgo de churn</option>
              <option value="low_inventory">Inventario bajo</option>
              <option value="revenue_milestone">Hito de ingresos</option>
              <option value="failed_transaction">Transacción fallida</option>
              <option value="fraud_alert">Alerta de fraude</option>
            </select>

            <select
              value={newRule.priority}
              onChange={(e) => setNewRule({ ...newRule, priority: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="low">Baja</option>
              <option value="medium">Media</option>
              <option value="high">Alta</option>
              <option value="critical">Crítica</option>
            </select>

            <div className="flex gap-2">
              <button
                onClick={createAlertRule}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Crear regla
              </button>
              <button
                onClick={() => setCreateMode(false)}
                className="flex-1 px-4 py-2 bg-gray-300 text-gray-900 rounded-lg hover:bg-gray-400"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Alert Rules List */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Reglas de alerta activas</h2>
        <div className="space-y-3">
          {alertRules.length === 0 ? (
            <p className="text-gray-500 py-8 text-center">Sin reglas de alerta configuradas</p>
          ) : (
            alertRules.map((rule) => (
              <div
                key={rule.rule_id}
                className="p-4 border border-gray-200 rounded-lg hover:border-gray-400 transition"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{rule.name}</h3>
                    <p className="text-sm text-gray-600 mt-1">{rule.alert_type}</p>
                    <div className="flex items-center gap-2 mt-2">
                      {rule.channels.map((channel: any) => (
                        <span
                          key={channel}
                          className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded"
                        >
                          {channel}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="text-right">
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                        rule.priority === 'critical'
                          ? 'bg-red-100 text-red-800'
                          : rule.priority === 'high'
                          ? 'bg-orange-100 text-orange-800'
                          : rule.priority === 'medium'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {rule.priority}
                    </span>
                    {rule.enabled && (
                      <p className="text-xs text-green-600 mt-2">Activa</p>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Channels Breakdown */}
      {metrics?.channels && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Distribución por canal</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={Object.entries(metrics.channels).map(([channel, count]) => ({
                channel: channel.toUpperCase(),
                count
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="channel" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default AlertsDashboard;
