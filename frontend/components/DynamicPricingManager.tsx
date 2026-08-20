/**
 * DynamicPricingManager — Location pricing tiers + flash sales + A/B tests
 */

import React, { useEffect, useState } from 'react';

interface PricingTier {
  configured: boolean;
  tier: 'flagship' | 'standard' | 'discount';
  tier_multiplier: number;
  peak_hours: string;
  peak_discount_pct: number;
}

interface RevenueImpact {
  date: string;
  transactions: number;
  base_revenue: number;
  final_revenue: number;
  discounts: number;
  impact: number;
}

interface AnalyticsData {
  location_id: string;
  period_days: number;
  total_transactions: number;
  total_base_revenue: number;
  total_final_revenue: number;
  total_discounts_given: number;
  net_revenue_impact: number;
  impact_pct: number;
  daily_breakdown: RevenueImpact[];
}

type Tab = 'tier' | 'codes' | 'tests' | 'analytics';

export const DynamicPricingManager: React.FC<{ locationId: string; locationName: string }> = ({
  locationId,
  locationName,
}) => {
  const [activeTab, setActiveTab] = useState<Tab>('tier');
  const [tier, setTier] = useState<PricingTier | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPricingData();
  }, [locationId]);

  const loadPricingData = async () => {
    try {
      const tierRes = await fetch(`/api/v1/locations/${locationId}/pricing-tier`);
      const tierData = await tierRes.json();
      setTier(tierData);

      const analyticsRes = await fetch(`/api/v1/locations/${locationId}/pricing-analytics?days=30`);
      const analyticsData = await analyticsRes.json();
      setAnalytics(analyticsData);
    } catch (e) {
      console.error('Failed to load pricing data:', e);
    } finally {
      setLoading(false);
    }
  };

  const getTierColor = (tier: string | undefined): string => {
    switch (tier) {
      case 'flagship':
        return '#dc2626';
      case 'standard':
        return '#3b82f6';
      case 'discount':
        return '#10b981';
      default:
        return '#6b7280';
    }
  };

  if (loading) {
    return <div>Loading pricing data...</div>;
  }

  return (
    <div className="pricing-manager">
      <header className="pricing-header">
        <h1>Dynamic Pricing — {locationName}</h1>
        {analytics && (
          <div className="header-stats">
            <div className="stat">
              <span className="stat-label">Revenue Impact (30d)</span>
              <span
                className="stat-value"
                style={{ color: analytics.net_revenue_impact > 0 ? '#10b981' : '#ef4444' }}
              >
                {analytics.net_revenue_impact > 0 ? '+' : ''}{analytics.net_revenue_impact.toFixed(2)}
              </span>
              <span className="stat-pct">{analytics.impact_pct.toFixed(1)}%</span>
            </div>
            <div className="stat">
              <span className="stat-label">Transactions</span>
              <span className="stat-value">{analytics.total_transactions}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Avg Final Price</span>
              <span className="stat-value">
                ${(analytics.total_final_revenue / Math.max(analytics.total_transactions, 1)).toFixed(2)}
              </span>
            </div>
          </div>
        )}
      </header>

      <nav className="pricing-tabs">
        <button className={activeTab === 'tier' ? 'active' : ''} onClick={() => setActiveTab('tier')}>
          Pricing Tier
        </button>
        <button className={activeTab === 'codes' ? 'active' : ''} onClick={() => setActiveTab('codes')}>
          Discount Codes
        </button>
        <button className={activeTab === 'tests' ? 'active' : ''} onClick={() => setActiveTab('tests')}>
          A/B Tests
        </button>
        <button className={activeTab === 'analytics' ? 'active' : ''} onClick={() => setActiveTab('analytics')}>
          Analytics
        </button>
      </nav>

      {/* Pricing Tier Tab */}
      {activeTab === 'tier' && (
        <section className="pricing-section">
          {tier?.configured ? (
            <div className="tier-card">
              <div className="tier-header">
                <h2>Current Tier</h2>
                <span className="tier-badge" style={{ backgroundColor: getTierColor(tier.tier) }}>
                  {tier.tier.toUpperCase()}
                </span>
              </div>

              <div className="tier-details">
                <div className="detail">
                  <span className="label">Multiplier</span>
                  <span className="value">
                    {tier.tier_multiplier > 1 ? '+' : ''}{((tier.tier_multiplier - 1) * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="detail">
                  <span className="label">Peak Hours</span>
                  <span className="value">{tier.peak_hours}</span>
                </div>
                <div className="detail">
                  <span className="label">Peak Discount</span>
                  <span className="value">{tier.peak_discount_pct}% off</span>
                </div>
              </div>

              <button className="btn-primary">Edit Tier</button>
            </div>
          ) : (
            <div className="empty-state">
              <p>No pricing tier configured</p>
              <button className="btn-primary">Create Tier</button>
            </div>
          )}
        </section>
      )}

      {/* Discount Codes Tab */}
      {activeTab === 'codes' && (
        <section className="pricing-section">
          <div className="section-header">
            <h2>Discount Codes</h2>
            <button className="btn-sm btn-add">+ Create Code</button>
          </div>

          <div className="codes-grid">
            <div className="code-card">
              <div className="code-header">
                <span className="code-badge">WELCOME20</span>
                <span className="code-status active">Active</span>
              </div>
              <div className="code-details">
                <span className="discount">20% off</span>
                <span className="usage">12/50 uses</span>
                <span className="expires">Expires in 15 days</span>
              </div>
            </div>

            <div className="code-card">
              <div className="code-header">
                <span className="code-badge">SUMMER15</span>
                <span className="code-status expired">Expired</span>
              </div>
              <div className="code-details">
                <span className="discount">15% off</span>
                <span className="usage">145/unlimited</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* A/B Tests Tab */}
      {activeTab === 'tests' && (
        <section className="pricing-section">
          <div className="section-header">
            <h2>A/B Tests</h2>
            <button className="btn-sm btn-add">+ Create Test</button>
          </div>

          <div className="tests-list">
            <div className="test-card">
              <h3>Holiday Pricing Test</h3>
              <div className="test-variants">
                <div className="variant">
                  <span className="variant-name">Control</span>
                  <span className="variant-price">$29.99</span>
                  <span className="variant-traffic">25%</span>
                  <span className="variant-revenue">$3,245</span>
                </div>
                <div className="variant">
                  <span className="variant-name">Variant A</span>
                  <span className="variant-price">$24.99</span>
                  <span className="variant-traffic">25%</span>
                  <span className="variant-revenue">$4,120</span>
                </div>
                <div className="variant">
                  <span className="variant-name">Variant B</span>
                  <span className="variant-price">$34.99</span>
                  <span className="variant-traffic">25%</span>
                  <span className="variant-revenue">$2,890</span>
                </div>
              </div>
              <div className="test-footer">
                <span className="test-status running">Running</span>
                <span className="test-end">Ends in 8 days</span>
                <span className="test-winner">Winner: Variant A (+27%)</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && analytics && (
        <section className="pricing-section">
          <h2>Revenue Impact (30 Days)</h2>

          <div className="analytics-grid">
            <div className="metric-card">
              <span className="metric-label">Base Revenue</span>
              <span className="metric-value">${analytics.total_base_revenue.toFixed(2)}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Final Revenue</span>
              <span className="metric-value">${analytics.total_final_revenue.toFixed(2)}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Discounts Given</span>
              <span className="metric-value negative">-${analytics.total_discounts_given.toFixed(2)}</span>
            </div>
            <div className="metric-card highlight">
              <span className="metric-label">Net Impact</span>
              <span className={`metric-value ${analytics.net_revenue_impact > 0 ? 'positive' : 'negative'}`}>
                {analytics.net_revenue_impact > 0 ? '+' : ''} ${Math.abs(analytics.net_revenue_impact).toFixed(2)}
              </span>
            </div>
          </div>

          <div className="chart-section">
            <h3>Daily Revenue Trend</h3>
            <div className="mini-chart">
              {analytics.daily_breakdown.slice(-14).map((day, idx) => (
                <div key={idx} className="chart-bar">
                  <div
                    className="bar"
                    style={{
                      height: `${(day.final_revenue / Math.max(...analytics.daily_breakdown.map((d) => d.final_revenue))) * 100}%`,
                      backgroundColor: day.impact > 0 ? '#10b981' : day.impact < 0 ? '#ef4444' : '#f59e0b',
                    }}
                    title={`${day.date}: $${day.final_revenue.toFixed(0)}`}
                  ></div>
                  <span className="date-label">{day.date.slice(5)}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      <style>{`
        .pricing-manager {
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .pricing-header {
          margin-bottom: 30px;
        }

        .pricing-header h1 {
          margin: 0 0 20px 0;
          font-size: 28px;
        }

        .header-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 12px;
        }

        .stat {
          padding: 16px;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
        }

        .stat-label {
          display: block;
          font-size: 12px;
          color: #6b7280;
          margin-bottom: 4px;
          text-transform: uppercase;
          font-weight: 600;
        }

        .stat-value {
          display: block;
          font-size: 24px;
          font-weight: 700;
        }

        .stat-pct {
          display: block;
          font-size: 12px;
          color: #6b7280;
          margin-top: 2px;
        }

        .pricing-tabs {
          display: flex;
          gap: 8px;
          margin-bottom: 20px;
          border-bottom: 1px solid #e5e7eb;
        }

        .pricing-tabs button {
          padding: 12px 16px;
          background: none;
          border: none;
          border-bottom: 2px solid transparent;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
          color: #6b7280;
          transition: all 0.2s;
        }

        .pricing-tabs button.active {
          border-bottom-color: #2563eb;
          color: #2563eb;
        }

        .pricing-section {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 20px;
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .section-header h2 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
        }

        .tier-card {
          padding: 20px;
          border: 2px solid #e5e7eb;
          border-radius: 8px;
          background: #f9fafb;
        }

        .tier-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .tier-header h2 {
          margin: 0;
          font-size: 18px;
        }

        .tier-badge {
          padding: 6px 12px;
          border-radius: 6px;
          color: white;
          font-size: 12px;
          font-weight: 700;
        }

        .tier-details {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 16px;
          margin-bottom: 16px;
        }

        .detail {
          display: flex;
          flex-direction: column;
        }

        .detail .label {
          font-size: 12px;
          color: #6b7280;
          margin-bottom: 4px;
          font-weight: 600;
        }

        .detail .value {
          font-size: 16px;
          font-weight: 700;
          color: #1f2937;
        }

        .btn-primary {
          padding: 10px 16px;
          background: #2563eb;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 600;
          transition: all 0.2s;
        }

        .btn-primary:hover {
          background: #1d4ed8;
        }

        .btn-sm {
          padding: 8px 12px;
          border: none;
          border-radius: 4px;
          background: #f3f4f6;
          cursor: pointer;
          font-size: 13px;
          font-weight: 600;
        }

        .btn-add {
          background: #10b981;
          color: white;
        }

        .codes-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
          gap: 12px;
        }

        .code-card {
          padding: 16px;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          background: #fafbfc;
        }

        .code-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .code-badge {
          font-weight: 700;
          font-family: monospace;
          font-size: 14px;
          color: #1f2937;
        }

        .code-status {
          padding: 2px 8px;
          border-radius: 3px;
          font-size: 11px;
          font-weight: 600;
          color: white;
        }

        .code-status.active {
          background: #10b981;
        }

        .code-status.expired {
          background: #9ca3af;
        }

        .code-details {
          display: flex;
          flex-direction: column;
          gap: 4px;
          font-size: 13px;
        }

        .discount {
          font-weight: 700;
          color: #10b981;
        }

        .usage {
          color: #6b7280;
        }

        .expires {
          color: #6b7280;
          font-size: 12px;
        }

        .tests-list {
          display: grid;
          gap: 12px;
        }

        .test-card {
          padding: 16px;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          background: #fafbfc;
        }

        .test-card h3 {
          margin: 0 0 12px 0;
          font-size: 16px;
        }

        .test-variants {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
          margin-bottom: 12px;
        }

        .variant {
          padding: 12px;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 4px;
          display: flex;
          flex-direction: column;
          gap: 4px;
          font-size: 12px;
        }

        .variant-name {
          font-weight: 600;
          color: #1f2937;
        }

        .variant-price {
          font-size: 16px;
          font-weight: 700;
          color: #2563eb;
        }

        .variant-traffic {
          color: #6b7280;
        }

        .variant-revenue {
          color: #10b981;
          font-weight: 600;
        }

        .test-footer {
          display: flex;
          gap: 12px;
          font-size: 12px;
        }

        .test-status {
          padding: 2px 8px;
          border-radius: 3px;
          background: #3b82f6;
          color: white;
          font-weight: 600;
        }

        .test-status.running {
          background: #3b82f6;
        }

        .test-end {
          color: #6b7280;
        }

        .test-winner {
          color: #10b981;
          font-weight: 600;
        }

        .analytics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 12px;
          margin-bottom: 30px;
        }

        .metric-card {
          padding: 16px;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          text-align: center;
        }

        .metric-card.highlight {
          border: 2px solid #2563eb;
          background: #eff6ff;
        }

        .metric-label {
          display: block;
          font-size: 12px;
          color: #6b7280;
          margin-bottom: 8px;
        }

        .metric-value {
          display: block;
          font-size: 18px;
          font-weight: 700;
          color: #1f2937;
        }

        .metric-value.positive {
          color: #10b981;
        }

        .metric-value.negative {
          color: #ef4444;
        }

        .chart-section {
          margin-top: 20px;
        }

        .chart-section h3 {
          margin: 0 0 12px 0;
          font-size: 14px;
          font-weight: 600;
        }

        .mini-chart {
          display: flex;
          align-items: flex-end;
          gap: 4px;
          height: 150px;
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
        }

        .date-label {
          font-size: 10px;
          color: #9ca3af;
        }

        .empty-state {
          padding: 40px 20px;
          text-align: center;
        }

        @media (max-width: 768px) {
          .tier-details {
            grid-template-columns: 1fr;
          }

          .analytics-grid {
            grid-template-columns: repeat(2, 1fr);
          }

          .test-variants {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};
