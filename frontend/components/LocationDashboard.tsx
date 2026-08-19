/**
 * LocationDashboard — Real-time location activity monitor
 * WebSocket-powered live feed of visitors, staff, feedback, metrics
 */

import React, { useEffect, useState, useRef } from 'react';

interface DashboardMessage {
  type: string;
  timestamp: string;
  [key: string]: any;
}

interface LocationMetrics {
  active_visitors: number;
  staff_on_shift: number;
  total_visitors: number;
  avg_dwell_minutes: number;
  avg_nps_score: number;
  feedback_count: number;
}

interface VisitorEvent {
  type: 'checkin' | 'checkout' | 'feedback';
  visitor_name?: string;
  checkin_type?: string;
  dwell_minutes?: number;
  nps_score?: number;
  timestamp: string;
}

interface StaffEvent {
  type: 'action' | 'checkout';
  staff_name: string;
  action?: string;
  hours_worked?: number;
  visitors_engaged?: number;
  demos?: number;
  sales?: number;
  timestamp: string;
}

type Alert = {
  id: string;
  type: 'high_wait_time' | 'capacity_warning' | 'negative_feedback' | 'staff_shortage';
  severity: 'info' | 'warning' | 'critical';
  message: string;
  timestamp: string;
};

export const LocationDashboard: React.FC<{ locationId: string; token: string }> = ({
  locationId,
  token,
}) => {
  const [metrics, setMetrics] = useState<LocationMetrics | null>(null);
  const [visitorEvents, setVisitorEvents] = useState<VisitorEvent[]>([]);
  const [staffEvents, setStaffEvents] = useState<StaffEvent[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [locationId, token]);

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//api.sellia.app/api/v1/ws/locations/${locationId}`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnected(true);
      console.log('Dashboard connected');

      // Send authorization
      ws.send(JSON.stringify({
        type: 'authorize',
        token: token,
      }));
    };

    ws.onmessage = (event) => {
      try {
        const message: DashboardMessage = JSON.parse(event.data);
        handleDashboardMessage(message);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    ws.onclose = () => {
      setConnected(false);
      console.log('Dashboard disconnected');
      // Reconnect after 5s
      setTimeout(connectWebSocket, 5000);
    };

    wsRef.current = ws;
  };

  const handleDashboardMessage = (message: DashboardMessage) => {
    switch (message.type) {
      case 'connection_established':
        setConnected(true);
        break;

      case 'location_metrics':
        setMetrics({
          active_visitors: message.active_visitors,
          staff_on_shift: message.staff_on_shift,
          total_visitors: message.total_visitors,
          avg_dwell_minutes: message.avg_dwell_minutes,
          avg_nps_score: message.avg_nps_score,
          feedback_count: message.feedback_count,
        });
        break;

      case 'visitor_checkin':
        addVisitorEvent({
          type: 'checkin',
          visitor_name: message.visitor_name || 'Anonymous',
          checkin_type: message.checkin_type,
          timestamp: message.checkin_time,
        });
        break;

      case 'visitor_checkout':
        addVisitorEvent({
          type: 'checkout',
          visitor_name: 'Visitor',
          dwell_minutes: Math.round(message.dwell_seconds / 60),
          timestamp: message.checkout_time,
        });
        break;

      case 'visitor_feedback':
        addVisitorEvent({
          type: 'feedback',
          nps_score: message.nps_score,
          timestamp: message.created_at,
        });
        break;

      case 'staff_action':
        addStaffEvent({
          type: 'action',
          staff_name: message.staff_name,
          action: message.action,
          timestamp: message.timestamp,
        });
        break;

      case 'staff_checkout':
        addStaffEvent({
          type: 'checkout',
          staff_name: message.staff_name,
          hours_worked: message.hours_worked,
          visitors_engaged: message.summary.visitors_engaged,
          demos: message.summary.demos,
          sales: message.summary.sales,
          timestamp: new Date().toISOString(),
        });
        break;

      case 'alert':
        addAlert({
          id: `${Date.now()}`,
          type: message.alert_type,
          severity: message.severity,
          message: message.message,
          timestamp: message.timestamp,
        });
        break;
    }
  };

  const addVisitorEvent = (event: VisitorEvent) => {
    setVisitorEvents((prev) => [event, ...prev.slice(0, 19)]);
  };

  const addStaffEvent = (event: StaffEvent) => {
    setStaffEvents((prev) => [event, ...prev.slice(0, 19)]);
  };

  const addAlert = (alert: Alert) => {
    setAlerts((prev) => [alert, ...prev.slice(0, 9)]);
    // Auto-dismiss after 10s
    setTimeout(
      () => setAlerts((prev) => prev.filter((a) => a.id !== alert.id)),
      10000
    );
  };

  return (
    <div className="location-dashboard">
      <header className="dashboard-header">
        <h1>Location Dashboard</h1>
        <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '● Live' : '● Offline'}
        </div>
      </header>

      {/* Metrics Cards */}
      <section className="metrics-grid">
        {metrics && (
          <>
            <MetricCard
              label="Active Visitors"
              value={metrics.active_visitors}
              unit="now"
            />
            <MetricCard
              label="Staff on Shift"
              value={metrics.staff_on_shift}
              unit="staff"
            />
            <MetricCard
              label="Today's Visitors"
              value={metrics.total_visitors}
              unit="total"
            />
            <MetricCard
              label="Avg Dwell Time"
              value={metrics.avg_dwell_minutes}
              unit="minutes"
            />
            <MetricCard
              label="Avg NPS Score"
              value={metrics.avg_nps_score}
              unit="/10"
              color={metrics.avg_nps_score >= 8 ? 'green' : 'orange'}
            />
            <MetricCard
              label="Feedback Count"
              value={metrics.feedback_count}
              unit="responses"
            />
          </>
        )}
      </section>

      {/* Alerts */}
      {alerts.length > 0 && (
        <section className="alerts-section">
          {alerts.map((alert) => (
            <div key={alert.id} className={`alert alert-${alert.severity}`}>
              <strong>[{alert.type}]</strong> {alert.message}
            </div>
          ))}
        </section>
      )}

      {/* Live Feed */}
      <div className="feed-container">
        {/* Visitor Events */}
        <section className="feed-section visitor-feed">
          <h2>Visitor Activity</h2>
          <div className="feed-list">
            {visitorEvents.map((event, idx) => (
              <div key={idx} className={`feed-item visitor-${event.type}`}>
                <span className="timestamp">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
                {event.type === 'checkin' && (
                  <span className="event-text">
                    ✓ {event.visitor_name} checked in via {event.checkin_type}
                  </span>
                )}
                {event.type === 'checkout' && (
                  <span className="event-text">
                    ✓ Visitor left after {event.dwell_minutes}m
                  </span>
                )}
                {event.type === 'feedback' && (
                  <span className={`event-text feedback nps-${event.nps_score}`}>
                    ⭐ NPS {event.nps_score}/10
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Staff Events */}
        <section className="feed-section staff-feed">
          <h2>Staff Performance</h2>
          <div className="feed-list">
            {staffEvents.map((event, idx) => (
              <div key={idx} className={`feed-item staff-${event.type}`}>
                <span className="timestamp">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
                {event.type === 'action' && (
                  <span className="event-text">
                    📍 {event.staff_name} — {event.action}
                  </span>
                )}
                {event.type === 'checkout' && (
                  <span className="event-text">
                    ✓ {event.staff_name} shift end:{' '}
                    {event.visitors_engaged} visitors, {event.sales} sales
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>

      <style>{`
        .location-dashboard {
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 30px;
          border-bottom: 2px solid #f0f0f0;
          padding-bottom: 15px;
        }

        .connection-status {
          font-size: 12px;
          font-weight: 600;
          padding: 5px 10px;
          border-radius: 4px;
        }

        .connection-status.connected {
          color: #22c55e;
          background: #f0fdf4;
        }

        .connection-status.disconnected {
          color: #ef4444;
          background: #fef2f2;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 15px;
          margin-bottom: 30px;
        }

        .alerts-section {
          margin-bottom: 20px;
        }

        .alert {
          padding: 12px 16px;
          border-radius: 6px;
          margin-bottom: 10px;
          font-size: 14px;
        }

        .alert-info {
          background: #dbeafe;
          color: #1e40af;
        }

        .alert-warning {
          background: #fef3c7;
          color: #92400e;
        }

        .alert-critical {
          background: #fee2e2;
          color: #991b1b;
        }

        .feed-container {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
        }

        .feed-section {
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          overflow: hidden;
        }

        .feed-section h2 {
          background: #f9fafb;
          padding: 12px 16px;
          margin: 0;
          font-size: 14px;
          font-weight: 600;
          border-bottom: 1px solid #e5e7eb;
        }

        .feed-list {
          max-height: 400px;
          overflow-y: auto;
        }

        .feed-item {
          padding: 12px 16px;
          border-bottom: 1px solid #f3f4f6;
          font-size: 13px;
          display: flex;
          gap: 12px;
        }

        .feed-item:last-child {
          border-bottom: none;
        }

        .timestamp {
          color: #6b7280;
          font-weight: 500;
          min-width: 50px;
        }

        .event-text {
          flex: 1;
          color: #1f2937;
        }

        .feedback {
          font-weight: 600;
        }

        .nps-9, .nps-10 {
          color: #22c55e;
        }

        .nps-7, .nps-8 {
          color: #f59e0b;
        }

        .nps-6 {
          color: #ef4444;
        }

        @media (max-width: 768px) {
          .feed-container {
            grid-template-columns: 1fr;
          }
          .metrics-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }
      `}</style>
    </div>
  );
};

interface MetricCardProps {
  label: string;
  value: number;
  unit: string;
  color?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, unit, color = 'blue' }) => (
  <div className="metric-card">
    <div className="metric-value">{value}</div>
    <div className="metric-unit">{unit}</div>
    <div className="metric-label">{label}</div>
    <style>{`
      .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
      }

      .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: ${color === 'green' ? '#22c55e' : color === 'orange' ? '#f59e0b' : '#1f2937'};
      }

      .metric-unit {
        font-size: 12px;
        color: #6b7280;
        margin-top: 4px;
      }

      .metric-label {
        font-size: 13px;
        color: #4b5563;
        margin-top: 8px;
        font-weight: 500;
      }
    `}</style>
  </div>
);
