/**
 * NPSDashboard — Real-time NPS monitoring + feedback alerts
 */

import React, { useEffect, useState } from 'react';

interface NPSMetric {
  date: string;
  nps_avg: number;
  promoters: number;
  passives: number;
  detractors: number;
  top_issues?: Array<{ topic: string; count: number }>;
}

interface FeedbackAlert {
  alert_id: string;
  nps_score: number;
  sentiment: 'positive' | 'neutral' | 'negative';
  comment: string;
  topics: string[];
  status: 'active' | 'acknowledged' | 'escalated' | 'resolved';
  visitor_name?: string;
  created_at: string;
}

interface NPSDashboardData {
  location_id: string;
  current_nps: number;
  avg_nps_period: number;
  nps_trend_30d: number;
  data_points: NPSMetric[];
  sentiment_trend: Array<{
    date: string;
    positive: number;
    neutral: number;
    negative: number;
    direction: string;
  }>;
}

export const NPSDashboard: React.FC<{ locationId: string }> = ({ locationId }) => {
  const [dashboardData, setDashboardData] = useState<NPSDashboardData | null>(null);
  const [alerts, setAlerts] = useState<FeedbackAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<FeedbackAlert | null>(null);

  useEffect(() => {
    loadDashboardData();
    loadAlerts();
  }, [locationId]);

  const loadDashboardData = async () => {
    try {
      const res = await fetch(`/api/v1/locations/${locationId}/nps-dashboard`);
      const data = await res.json();
      setDashboardData(data);
    } catch (e) {
      console.error('Failed to load NPS dashboard:', e);
    } finally {
      setLoading(false);
    }
  };

  const loadAlerts = async () => {
    try {
      const res = await fetch(`/api/v1/locations/${locationId}/alerts`);
      const data = await res.json();
      setAlerts(data.alerts || []);
    } catch (e) {
      console.error('Failed to load alerts:', e);
    }
  };

  const handleEscalateAlert = async (alertId: string, staffId: string) => {
    try {
      const res = await fetch(`/api/v1/alerts/${alertId}/escalate`, {
        method: 'POST',
        body: new URLSearchParams({ assigned_to_staff_id: staffId }),
      });

      if (res.ok) {
        loadAlerts();
      }
    } catch (e) {
      console.error('Failed to escalate alert:', e);
    }
  };

  const getSentimentColor = (sentiment: string): string => {
    switch (sentiment) {
      case 'positive':
        return '#10b981';
      case 'neutral':
        return '#f59e0b';
      case 'negative':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const getStatusBadgeColor = (status: string): string => {
    switch (status) {
      case 'active':
        return '#dc2626';
      case 'acknowledged':
        return '#f59e0b';
      case 'escalated':
        return '#3b82f6';
      case 'resolved':
        return '#10b981';
      default:
        return '#6b7280';
    }
  };

  const activeAlerts = alerts.filter((a) => a.status === 'active');
  const unresolved = alerts.filter((a) => ['active', 'acknowledged', 'escalated'].includes(a.status));

  if (loading) {
    return <div>Loading NPS data...</div>;
  }

  if (!dashboardData) {
    return <div>No data available</div>;
  }

  return (
    <div className="nps-dashboard">
      <header className="dashboard-header">
        <h1>NPS Dashboard</h1>
        <div className="header-stats">
          <div className="stat-card">
            <div className="stat-value" style={{ color: dashboardData.current_nps >= 7 ? '#10b981' : '#ef4444' }}>
              {dashboardData.current_nps.toFixed(1)}
            </div>
            <div className="stat-label">Current NPS</div>
          </div>

          <div className="stat-card">
            <div className="stat-value">{dashboardData.avg_nps_period.toFixed(1)}</div>
            <div className="stat-label">30-Day Avg</div>
          </div>

          <div className="stat-card">
            <div className={`stat-value ${dashboardData.nps_trend_30d > 0 ? 'positive' : 'negative'}`}>
              {dashboardData.nps_trend_30d > 0 ? '+' : ''}{dashboardData.nps_trend_30d.toFixed(1)}
            </div>
            <div className="stat-label">Trend</div>
          </div>

          <div className="alert-card">
            <div className="alert-value" style={{ color: activeAlerts.length > 0 ? '#dc2626' : '#10b981' }}>
              {activeAlerts.length}
            </div>
            <div className="alert-label">Active Alerts</div>
          </div>
        </div>
      </header>

      <div className="dashboard-grid">
        {/* NPS Trend Chart */}
        <section className="chart-section nps-trend">
          <h2>NPS Trend (30 Days)</h2>
          <div className="mini-chart">
            {dashboardData.data_points.map((point, idx) => (
              <div key={idx} className="chart-bar">
                <div
                  className="bar"
                  style={{
                    height: `${(point.nps_avg / 10) * 100}%`,
                    backgroundColor: point.nps_avg >= 7 ? '#10b981' : point.nps_avg >= 5 ? '#f59e0b' : '#ef4444',
                  }}
                  title={`${point.date}: ${point.nps_avg}`}
                ></div>
                <span className="date-label">{point.date.slice(5)}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Sentiment Breakdown */}
        <section className="chart-section sentiment">
          <h2>Sentiment Distribution</h2>
          {dashboardData.sentiment_trend.length > 0 && (
            <div className="sentiment-stacks">
              {dashboardData.sentiment_trend.slice(-7).map((day, idx) => (
                <div key={idx} className="sentiment-stack">
                  <div
                    className="sentiment-bar positive"
                    style={{ height: `${day.positive}%` }}
                    title={`Positive: ${day.positive.toFixed(0)}%`}
                  ></div>
                  <div
                    className="sentiment-bar neutral"
                    style={{ height: `${day.neutral}%` }}
                    title={`Neutral: ${day.neutral.toFixed(0)}%`}
                  ></div>
                  <div
                    className="sentiment-bar negative"
                    style={{ height: `${day.negative}%` }}
                    title={`Negative: ${day.negative.toFixed(0)}%`}
                  ></div>
                  <span className="date-label">{day.date.slice(5)}</span>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      {/* Active Alerts */}
      <section className="alerts-section">
        <h2>
          Active Alerts <span className="alert-badge">{activeAlerts.length}</span>
        </h2>

        {activeAlerts.length === 0 ? (
          <div className="empty-state">No active alerts</div>
        ) : (
          <div className="alerts-list">
            {activeAlerts.map((alert) => (
              <div
                key={alert.alert_id}
                className="alert-item"
                style={{ borderLeftColor: getSentimentColor(alert.sentiment) }}
                onClick={() => setSelectedAlert(alert)}
              >
                <div className="alert-header">
                  <h4>{alert.visitor_name || 'Anonymous'}</h4>
                  <span className="nps-badge" style={{ backgroundColor: getSentimentColor(alert.sentiment) }}>
                    NPS {alert.nps_score}
                  </span>
                </div>

                {alert.comment && <p className="alert-comment">{alert.comment}</p>}

                {alert.topics.length > 0 && (
                  <div className="topics">
                    {alert.topics.map((topic) => (
                      <span key={topic} className="topic-tag">
                        {topic}
                      </span>
                    ))}
                  </div>
                )}

                <div className="alert-footer">
                  <span className="timestamp">{new Date(alert.created_at).toLocaleString()}</span>
                  <span className="status-badge" style={{ backgroundColor: getStatusBadgeColor(alert.status) }}>
                    {alert.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* All Alerts Summary */}
      {unresolved.length > activeAlerts.length && (
        <section className="summary-section">
          <h3>Alert Summary</h3>
          <div className="summary-grid">
            <div className="summary-item">
              <span className="summary-label">Active</span>
              <span className="summary-value" style={{ color: '#dc2626' }}>
                {activeAlerts.length}
              </span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Acknowledged</span>
              <span className="summary-value" style={{ color: '#f59e0b' }}>
                {alerts.filter((a) => a.status === 'acknowledged').length}
              </span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Escalated</span>
              <span className="summary-value" style={{ color: '#3b82f6' }}>
                {alerts.filter((a) => a.status === 'escalated').length}
              </span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Resolved</span>
              <span className="summary-value" style={{ color: '#10b981' }}>
                {alerts.filter((a) => a.status === 'resolved').length}
              </span>
            </div>
          </div>
        </section>
      )}

      {selectedAlert && (
        <div className="alert-detail-modal" onClick={() => setSelectedAlert(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="close-btn" onClick={() => setSelectedAlert(null)}>
              ✕
            </button>

            <h3>{selectedAlert.visitor_name || 'Feedback from'} — NPS {selectedAlert.nps_score}</h3>

            <div className="detail-section">
              <h4>Feedback</h4>
              <p>{selectedAlert.comment || '(No comment provided)'}</p>
            </div>

            {selectedAlert.topics.length > 0 && (
              <div className="detail-section">
                <h4>Topics</h4>
                <div className="topics-full">
                  {selectedAlert.topics.map((topic) => (
                    <span key={topic} className="topic-tag-large">
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="detail-section">
              <h4>Status: {selectedAlert.status}</h4>
              <p className="timestamp">{new Date(selectedAlert.created_at).toLocaleString()}</p>
            </div>

            {selectedAlert.status === 'active' && (
              <div className="modal-actions">
                <button className="btn-primary" onClick={() => setSelectedAlert(null)}>
                  Acknowledge
                </button>
                <button className="btn-success" onClick={() => setSelectedAlert(null)}>
                  Escalate to Staff
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      <style>{`
        .nps-dashboard {
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .dashboard-header {
          margin-bottom: 30px;
        }

        .dashboard-header h1 {
          margin: 0 0 20px 0;
          font-size: 28px;
        }

        .header-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
          gap: 12px;
        }

        .stat-card {
          padding: 16px;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          text-align: center;
        }

        .stat-value {
          font-size: 24px;
          font-weight: 700;
          display: block;
        }

        .stat-value.positive {
          color: #10b981;
        }

        .stat-value.negative {
          color: #ef4444;
        }

        .stat-label {
          font-size: 12px;
          color: #6b7280;
          margin-top: 4px;
          text-transform: uppercase;
          font-weight: 600;
        }

        .alert-card {
          padding: 16px;
          background: #fffaf9;
          border: 2px solid #fecaca;
          border-radius: 8px;
          text-align: center;
        }

        .alert-value {
          font-size: 24px;
          font-weight: 700;
          color: #dc2626;
        }

        .alert-label {
          font-size: 12px;
          color: #6b7280;
          margin-top: 4px;
          text-transform: uppercase;
          font-weight: 600;
        }

        .dashboard-grid {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 20px;
          margin-bottom: 30px;
        }

        .chart-section {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 20px;
        }

        .chart-section h2 {
          margin: 0 0 16px 0;
          font-size: 16px;
          font-weight: 600;
        }

        .mini-chart {
          display: flex;
          align-items: flex-end;
          gap: 4px;
          height: 200px;
        }

        .chart-bar {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: flex-end;
          gap: 4px;
        }

        .bar {
          width: 100%;
          border-radius: 4px 4px 0 0;
          min-height: 4px;
        }

        .date-label {
          font-size: 10px;
          color: #9ca3af;
        }

        .sentiment-stacks {
          display: flex;
          gap: 6px;
          align-items: flex-end;
          height: 200px;
        }

        .sentiment-stack {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 0;
          height: 100%;
        }

        .sentiment-bar {
          width: 100%;
          flex: 1;
          border-radius: 0;
        }

        .sentiment-bar.positive {
          background: #10b981;
        }

        .sentiment-bar.neutral {
          background: #f59e0b;
        }

        .sentiment-bar.negative {
          background: #ef4444;
        }

        .alerts-section {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 20px;
          margin-bottom: 20px;
        }

        .alerts-section h2 {
          margin: 0 0 16px 0;
          font-size: 16px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .alert-badge {
          background: #dc2626;
          color: white;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
        }

        .alerts-list {
          display: grid;
          gap: 12px;
        }

        .alert-item {
          padding: 12px;
          border: 1px solid #e5e7eb;
          border-left: 4px solid;
          border-radius: 6px;
          background: #fafbfc;
          cursor: pointer;
          transition: all 0.2s;
        }

        .alert-item:hover {
          background: #f3f4f6;
        }

        .alert-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .alert-header h4 {
          margin: 0;
          font-size: 14px;
          font-weight: 600;
        }

        .nps-badge {
          padding: 4px 8px;
          border-radius: 4px;
          color: white;
          font-size: 12px;
          font-weight: 600;
        }

        .alert-comment {
          margin: 0 0 8px 0;
          font-size: 13px;
          color: #4b5563;
          line-height: 1.4;
        }

        .topics {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-bottom: 8px;
        }

        .topic-tag {
          background: #dbeafe;
          color: #1e40af;
          padding: 2px 8px;
          border-radius: 3px;
          font-size: 11px;
          font-weight: 600;
        }

        .alert-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 11px;
        }

        .timestamp {
          color: #9ca3af;
        }

        .status-badge {
          padding: 2px 8px;
          border-radius: 3px;
          color: white;
          font-weight: 600;
          text-transform: capitalize;
        }

        .empty-state {
          padding: 40px 20px;
          text-align: center;
          color: #9ca3af;
        }

        .summary-section {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 20px;
        }

        .summary-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 12px;
        }

        .summary-item {
          padding: 12px;
          background: #f9fafb;
          border-radius: 6px;
          text-align: center;
        }

        .summary-label {
          display: block;
          font-size: 12px;
          color: #6b7280;
          margin-bottom: 6px;
        }

        .summary-value {
          display: block;
          font-size: 20px;
          font-weight: 700;
        }

        .alert-detail-modal {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-content {
          background: white;
          border-radius: 12px;
          padding: 24px;
          max-width: 500px;
          max-height: 80vh;
          overflow-y: auto;
          position: relative;
        }

        .close-btn {
          position: absolute;
          top: 16px;
          right: 16px;
          background: none;
          border: none;
          font-size: 20px;
          cursor: pointer;
        }

        .detail-section {
          margin-bottom: 20px;
        }

        .detail-section h4 {
          margin: 0 0 8px 0;
          font-size: 12px;
          color: #6b7280;
          text-transform: uppercase;
          font-weight: 600;
        }

        .detail-section p {
          margin: 0;
          color: #1f2937;
          line-height: 1.5;
        }

        .topics-full {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        .topic-tag-large {
          background: #dbeafe;
          color: #1e40af;
          padding: 6px 12px;
          border-radius: 4px;
          font-size: 13px;
          font-weight: 600;
        }

        .modal-actions {
          display: flex;
          gap: 12px;
          margin-top: 20px;
        }

        .btn-primary {
          flex: 1;
          padding: 10px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 600;
        }

        .btn-success {
          flex: 1;
          padding: 10px;
          background: #10b981;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 600;
        }

        @media (max-width: 768px) {
          .dashboard-grid {
            grid-template-columns: 1fr;
          }

          .summary-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }
      `}</style>
    </div>
  );
};
