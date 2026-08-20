import React, { useState, useEffect } from 'react';
import { Mail, MessageCircle, Phone, Calendar, ShoppingCart, TrendingUp, TicketIcon, Star, Search, Filter } from 'lucide-react';

const CustomerTimeline: React.FC<{ customerId: string; businessId: string }> = ({ customerId, businessId }) => {
  const [events, setEvents] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [filters, setFilters] = useState({
    eventTypes: [] as string[],
    channels: [] as string[],
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchTimeline();
    fetchSummary();
  }, [customerId, businessId, filters]);

  const fetchTimeline = async () => {
    try {
      const params = new URLSearchParams({
        business_id: businessId,
      });
      if (filters.eventTypes.length > 0) {
        params.append('event_types', filters.eventTypes.join(','));
      }
      if (filters.channels.length > 0) {
        params.append('channels', filters.channels.join(','));
      }

      const res = await fetch(
        `/api/v1/customers/${customerId}/timeline?${params.toString()}`
      );
      const data = await res.json();
      setEvents(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch timeline:', error);
    }
  };

  const fetchSummary = async () => {
    try {
      const res = await fetch(
        `/api/v1/customers/${customerId}/timeline/summary?business_id=${businessId}`
      );
      const data = await res.json();
      setSummary(data);
    } catch (error) {
      console.error('Failed to fetch summary:', error);
    }
  };

  const getEventIcon = (eventType: string) => {
    if (eventType.includes('email')) return <Mail className="w-5 h-5 text-blue-600" />;
    if (eventType.includes('sms') || eventType.includes('whatsapp')) return <MessageCircle className="w-5 h-5 text-green-600" />;
    if (eventType.includes('call')) return <Phone className="w-5 h-5 text-purple-600" />;
    if (eventType.includes('meeting')) return <Calendar className="w-5 h-5 text-orange-600" />;
    if (eventType.includes('order')) return <ShoppingCart className="w-5 h-5 text-cyan-600" />;
    if (eventType.includes('deal')) return <TrendingUp className="w-5 h-5 text-green-700" />;
    if (eventType.includes('support')) return <TicketIcon className="w-5 h-5 text-red-600" />;
    return <Mail className="w-5 h-5 text-gray-600" />;
  };

  const getOutcomeColor = (outcome: string) => {
    switch (outcome) {
      case 'success':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'no_show':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const markAsImportant = async (eventId: string, isImportant: boolean) => {
    try {
      await fetch(
        `/api/v1/events/${eventId}/important?is_important=${!isImportant}`,
        { method: 'POST' }
      );
      fetchTimeline();
    } catch (error) {
      console.error('Failed to mark event:', error);
    }
  };

  const toggleFilter = (type: 'eventTypes' | 'channels', value: string) => {
    setFilters((prev) => ({
      ...prev,
      [type]: prev[type].includes(value)
        ? prev[type].filter((v) => v !== value)
        : [...prev[type], value],
    }));
  };

  const eventTypeOptions = [
    'email_sent', 'email_opened', 'email_clicked',
    'sms_sent', 'whatsapp_sent',
    'call_incoming', 'call_outgoing',
    'meeting_scheduled', 'meeting_completed',
    'order_created', 'order_paid',
    'deal_created', 'deal_won',
  ];

  const channelOptions = ['email', 'sms', 'whatsapp', 'call', 'meeting', 'order', 'deal', 'support'];

  return (
    <div className="w-full space-y-6 p-6 bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Timeline del Cliente</h1>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Filter className="w-4 h-4" />
          Filtros
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Buscar en timeline..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-7 gap-3">
          <div className="bg-white p-3 rounded-lg shadow text-center">
            <p className="text-gray-600 text-xs font-medium">Total</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{summary.total_events}</p>
          </div>
          <div className="bg-white p-3 rounded-lg shadow text-center">
            <p className="text-gray-600 text-xs font-medium">Email</p>
            <p className="text-xl font-bold text-blue-600 mt-1">{summary.email_count}</p>
          </div>
          <div className="bg-white p-3 rounded-lg shadow text-center">
            <p className="text-gray-600 text-xs font-medium">SMS</p>
            <p className="text-xl font-bold text-green-600 mt-1">{summary.sms_count}</p>
          </div>
          <div className="bg-white p-3 rounded-lg shadow text-center">
            <p className="text-gray-600 text-xs font-medium">Llamadas</p>
            <p className="text-xl font-bold text-purple-600 mt-1">{summary.call_count}</p>
          </div>
          <div className="bg-white p-3 rounded-lg shadow text-center">
            <p className="text-gray-600 text-xs font-medium">Reuniones</p>
            <p className="text-xl font-bold text-orange-600 mt-1">{summary.meeting_count}</p>
          </div>
          <div className="bg-white p-3 rounded-lg shadow text-center">
            <p className="text-gray-600 text-xs font-medium">Órdenes</p>
            <p className="text-xl font-bold text-cyan-600 mt-1">{summary.order_count}</p>
          </div>
          <div className="bg-white p-3 rounded-lg shadow text-center">
            <p className="text-gray-600 text-xs font-medium">Engagement</p>
            <p className="text-xl font-bold text-pink-600 mt-1">{summary.avg_engagement_score}</p>
          </div>
        </div>
      )}

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <h3 className="font-semibold text-gray-900 mb-4">Filtros</h3>

          <div className="space-y-4">
            <div>
              <p className="text-sm font-semibold text-gray-700 mb-2">Tipos de evento</p>
              <div className="flex flex-wrap gap-2">
                {eventTypeOptions.map((type) => (
                  <button
                    key={type}
                    onClick={() => toggleFilter('eventTypes', type)}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition ${
                      filters.eventTypes.includes(type)
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {type.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="text-sm font-semibold text-gray-700 mb-2">Canales</p>
              <div className="flex flex-wrap gap-2">
                {channelOptions.map((channel) => (
                  <button
                    key={channel}
                    onClick={() => toggleFilter('channels', channel)}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition ${
                      filters.channels.includes(channel)
                        ? 'bg-green-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {channel}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Timeline */}
      <div className="space-y-4">
        {events.length === 0 ? (
          <div className="bg-white p-12 rounded-lg shadow text-center">
            <p className="text-gray-500">Sin eventos en la timeline</p>
          </div>
        ) : (
          events.map((event, index) => (
            <div
              key={event.event_id}
              className="bg-white p-4 rounded-lg shadow border-l-4 border-blue-600 hover:shadow-lg transition relative"
            >
              <div className="flex gap-4">
                {/* Icon */}
                <div className="flex-shrink-0 mt-1">{getEventIcon(event.event_type)}</div>

                {/* Content */}
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">{event.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                    </div>
                    <button
                      onClick={() => markAsImportant(event.event_id, event.is_important)}
                      className="p-1 hover:bg-gray-100 rounded"
                    >
                      <Star
                        className={`w-5 h-5 ${
                          event.is_important ? 'fill-yellow-400 text-yellow-400' : 'text-gray-400'
                        }`}
                      />
                    </button>
                  </div>

                  {/* Metadata */}
                  <div className="flex items-center gap-2 mt-3 flex-wrap">
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                      {event.event_type}
                    </span>
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                      {event.channel}
                    </span>
                    <span
                      className={`text-xs px-2 py-1 rounded font-semibold ${getOutcomeColor(
                        event.outcome
                      )}`}
                    >
                      {event.outcome}
                    </span>
                    {event.revenue_impact && (
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                        {event.revenue_impact === 'positive' ? '+' : ''} ${event.estimated_value || 0}
                      </span>
                    )}
                    <span className="text-xs text-gray-500 ml-auto">
                      {new Date(event.timestamp).toLocaleString('es-AR')}
                    </span>
                  </div>

                  {/* Engagement Score */}
                  {event.engagement_score > 0 && (
                    <div className="mt-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-600">Engagement:</span>
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${event.engagement_score}%` }}
                          ></div>
                        </div>
                        <span className="text-xs font-semibold text-gray-700">{event.engagement_score}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default CustomerTimeline;
