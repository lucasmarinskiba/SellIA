import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, Users, Zap } from 'lucide-react';

const EventStreamDashboard: React.FC<{ businessId: string }> = ({ businessId }) => {
  const [events, setEvents] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchEventStream();
    fetchMetrics();

    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchEventStream();
      }, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [businessId, autoRefresh]);

  const fetchEventStream = async () => {
    try {
      const res = await fetch(`/api/v1/businesses/${businessId}/timeline/stream?limit=100`);
      const data = await res.json();
      setEvents(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch event stream:', error);
    }
  };

  const fetchMetrics = async () => {
    try {
      const res = await fetch(`/api/v1/timeline/metrics?business_id=${businessId}&days=7`);
      const data = await res.json();
      setMetrics(data);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    }
  };

  const getEventColor = (eventType: string) => {
    if (eventType.includes('email')) return 'bg-blue-50 border-blue-200';
    if (eventType.includes('whatsapp') || eventType.includes('sms')) return 'bg-green-50 border-green-200';
    if (eventType.includes('call')) return 'bg-purple-50 border-purple-200';
    if (eventType.includes('meeting')) return 'bg-orange-50 border-orange-200';
    if (eventType.includes('order')) return 'bg-cyan-50 border-cyan-200';
    if (eventType.includes('deal')) return 'bg-emerald-50 border-emerald-200';
    return 'bg-gray-50 border-gray-200';
  };

  return (
    <div className="w-full space-y-6 p-6 bg-gray-50">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Flujo de Eventos en Vivo</h1>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-4 h-4 rounded"
            />
            <span className="text-sm text-gray-700">Actualización en vivo</span>
          </label>
          <button
            onClick={fetchEventStream}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Actualizar
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">Eventos totales (7d)</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{metrics.total_events || 0}</p>
              </div>
              <Activity className="w-10 h-10 text-blue-500" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">Clientes activos</p>
                <p className="text-3xl font-bold text-green-600 mt-2">{metrics.active_customers || 0}</p>
              </div>
              <Users className="w-10 h-10 text-green-500" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">Engagement promedio</p>
                <p className="text-3xl font-bold text-purple-600 mt-2">{metrics.avg_engagement_score || 0}</p>
              </div>
              <TrendingUp className="w-10 h-10 text-purple-500" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">Impacto de ingresos</p>
                <p className="text-3xl font-bold text-green-600 mt-2">
                  ${(metrics.total_revenue_impact / 100).toLocaleString()}
                </p>
              </div>
              <Zap className="w-10 h-10 text-yellow-500" />
            </div>
          </div>
        </div>
      )}

      {/* Event Type Distribution */}
      {metrics?.event_types && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Distribución de eventos</h2>
          <div className="flex flex-wrap gap-2">
            {Object.entries(metrics.event_types).map(([type, count]: [string, any]) => (
              <div
                key={type}
                className="px-3 py-2 bg-gray-100 rounded-full text-sm font-medium text-gray-700"
              >
                {type}: <span className="font-bold text-gray-900">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Live Event Stream */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Eventos en vivo</h2>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {events.length === 0 ? (
            <p className="text-gray-500 py-8 text-center">Sin eventos</p>
          ) : (
            events.map((event, index) => (
              <div
                key={event.event_id}
                className={`p-3 rounded-lg border-l-4 ${getEventColor(event.event_type)}`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900 text-sm">{event.title}</p>
                    <p className="text-xs text-gray-600 mt-1">
                      {event.event_type} · {event.channel} · {event.customer_id}
                    </p>
                  </div>
                  <div className="text-right">
                    <span
                      className={`inline-block text-xs font-semibold px-2 py-1 rounded ${
                        event.outcome === 'success'
                          ? 'bg-green-100 text-green-800'
                          : event.outcome === 'pending'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {event.outcome}
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(event.timestamp).toLocaleTimeString('es-AR')}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Channel Distribution */}
      {metrics?.channels && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Eventos por canal</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(metrics.channels).map(([channel, count]: [string, any]) => (
              <div key={channel} className="p-4 bg-gray-50 rounded-lg text-center">
                <p className="text-gray-600 text-sm font-medium capitalize">{channel}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{count}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default EventStreamDashboard;
