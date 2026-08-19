/**
 * LocationInventoryManager — View/manage per-location stock + low-stock alerts
 */

import React, { useEffect, useState } from 'react';

interface InventoryItem {
  inventory_id: string;
  product_id: string;
  product_name: string;
  quantity_on_hand: number;
  quantity_available: number;
  quantity_reserved: number;
  reorder_point: number;
  status: 'in_stock' | 'low_stock' | 'out_of_stock';
  is_demo_unit: boolean;
  unit_price: number;
  last_stock_check?: string;
}

interface LowStockAlert {
  alert_id: string;
  product_id: string;
  product_name: string;
  quantity_available: number;
  reorder_point: number;
  acknowledged: boolean;
  reorder_initiated: boolean;
  created_at: string;
}

interface StockMovement {
  movement_id: string;
  movement_type: string;
  quantity_changed: number;
  quantity_before: number;
  quantity_after: number;
  reason?: string;
  created_at: string;
}

type SelectedTab = 'inventory' | 'alerts' | 'history';

export const LocationInventoryManager: React.FC<{ locationId: string; locationName: string }> = ({
  locationId,
  locationName,
}) => {
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [alerts, setAlerts] = useState<LowStockAlert[]>([]);
  const [history, setHistory] = useState<StockMovement[]>([]);
  const [selectedTab, setSelectedTab] = useState<SelectedTab>('inventory');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInventory();
    loadAlerts();
  }, [locationId]);

  const loadInventory = async () => {
    try {
      const res = await fetch(`/api/v1/locations/${locationId}/inventory`);
      const data = await res.json();
      setInventory(data.inventory || []);
    } catch (e) {
      console.error('Failed to load inventory:', e);
    } finally {
      setLoading(false);
    }
  };

  const loadAlerts = async () => {
    try {
      const res = await fetch(`/api/v1/locations/${locationId}/low-stock-alerts`);
      const data = await res.json();
      setAlerts(data.alerts || []);
    } catch (e) {
      console.error('Failed to load alerts:', e);
    }
  };

  const loadHistory = async (productId?: string) => {
    try {
      let url = `/api/v1/locations/${locationId}/stock-movements`;
      if (productId) url += `?product_id=${productId}`;

      const res = await fetch(url);
      const data = await res.json();
      setHistory(data.movements || []);
    } catch (e) {
      console.error('Failed to load history:', e);
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      const res = await fetch('/api/v1/inventory/acknowledge-alert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_id: alertId }),
      });

      if (res.ok) {
        loadAlerts();
      }
    } catch (e) {
      console.error('Failed to acknowledge alert:', e);
    }
  };

  const handleStockUpdate = async (productId: string, quantityChange: number, movementType: string) => {
    try {
      const res = await fetch('/api/v1/inventory/update-stock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location_id: locationId,
          product_id: productId,
          quantity_change: quantityChange,
          movement_type: movementType,
          reason: `Manual adjustment: ${movementType}`,
        }),
      });

      if (res.ok) {
        loadInventory();
        loadHistory();
      }
    } catch (e) {
      console.error('Failed to update stock:', e);
    }
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'in_stock':
        return '#22c55e';
      case 'low_stock':
        return '#f59e0b';
      case 'out_of_stock':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  if (loading) {
    return <div>Loading inventory...</div>;
  }

  return (
    <div className="inventory-manager">
      <header className="inv-header">
        <h1>Inventory — {locationName}</h1>
        <div className="inv-stats">
          <div className="stat">
            <span className="stat-label">Total SKUs</span>
            <span className="stat-value">{inventory.length}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Low Stock Alerts</span>
            <span className="stat-value alert-badge">{alerts.length}</span>
          </div>
        </div>
      </header>

      <nav className="inv-tabs">
        <button
          className={selectedTab === 'inventory' ? 'active' : ''}
          onClick={() => setSelectedTab('inventory')}
        >
          Inventory
        </button>
        <button
          className={selectedTab === 'alerts' ? 'active' : ''}
          onClick={() => setSelectedTab('alerts')}
        >
          Low Stock ({alerts.length})
        </button>
        <button
          className={selectedTab === 'history' ? 'active' : ''}
          onClick={() => {
            setSelectedTab('history');
            loadHistory();
          }}
        >
          Movement History
        </button>
      </nav>

      {/* Inventory Tab */}
      {selectedTab === 'inventory' && (
        <section className="inv-section">
          <table className="inv-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>On Hand</th>
                <th>Available</th>
                <th>Reserved</th>
                <th>Reorder Point</th>
                <th>Status</th>
                <th>Price</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {inventory.map((item) => (
                <tr key={item.inventory_id} className={`status-${item.status}`}>
                  <td className="product-cell">
                    <span className="product-name">{item.product_name}</span>
                    <span className="product-id">{item.product_id}</span>
                    {item.is_demo_unit && <span className="demo-badge">Demo Unit</span>}
                  </td>
                  <td>{item.quantity_on_hand}</td>
                  <td className="available-qty">{item.quantity_available}</td>
                  <td>{item.quantity_reserved}</td>
                  <td>{item.reorder_point}</td>
                  <td>
                    <span className="status-badge" style={{ backgroundColor: getStatusColor(item.status) }}>
                      {item.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td>${item.unit_price.toFixed(2)}</td>
                  <td className="actions-cell">
                    <button
                      className="btn-sm btn-add"
                      onClick={() => handleStockUpdate(item.product_id, 1, 'stock_in')}
                      title="Add 1 unit"
                    >
                      +1
                    </button>
                    <button
                      className="btn-sm btn-remove"
                      onClick={() => handleStockUpdate(item.product_id, -1, 'stock_out')}
                      title="Remove 1 unit"
                      disabled={item.quantity_available === 0}
                    >
                      -1
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* Low Stock Alerts Tab */}
      {selectedTab === 'alerts' && (
        <section className="inv-section">
          {alerts.length === 0 ? (
            <div className="empty-state">No low-stock alerts</div>
          ) : (
            <div className="alerts-list">
              {alerts.map((alert) => (
                <div key={alert.alert_id} className={`alert-item ${alert.acknowledged ? 'acknowledged' : 'active'}`}>
                  <div className="alert-header">
                    <h3>{alert.product_name}</h3>
                    <span className="alert-created">{new Date(alert.created_at).toLocaleDateString()}</span>
                  </div>

                  <div className="alert-details">
                    <div className="detail">
                      <span className="label">Available:</span>
                      <span className="value">{alert.quantity_available}</span>
                    </div>
                    <div className="detail">
                      <span className="label">Reorder Point:</span>
                      <span className="value">{alert.reorder_point}</span>
                    </div>
                  </div>

                  <div className="alert-actions">
                    {!alert.acknowledged && (
                      <button
                        className="btn-sm btn-acknowledge"
                        onClick={() => handleAcknowledgeAlert(alert.alert_id)}
                      >
                        Acknowledge
                      </button>
                    )}
                    {alert.acknowledged && <span className="acknowledged-badge">✓ Acknowledged</span>}
                    {alert.reorder_initiated && (
                      <span className="reorder-badge">Reorder Initiated</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* History Tab */}
      {selectedTab === 'history' && (
        <section className="inv-section">
          <div className="history-list">
            {history.length === 0 ? (
              <div className="empty-state">No stock movements</div>
            ) : (
              history.map((movement) => (
                <div key={movement.movement_id} className={`history-item type-${movement.movement_type}`}>
                  <div className="movement-time">
                    {new Date(movement.created_at).toLocaleTimeString()}
                  </div>
                  <div className="movement-type">{movement.movement_type.replace('_', ' ')}</div>
                  <div className="movement-qty">
                    <span className={movement.quantity_changed > 0 ? 'positive' : 'negative'}>
                      {movement.quantity_changed > 0 ? '+' : ''}{movement.quantity_changed}
                    </span>
                    <span className="movement-summary">
                      {movement.quantity_before} → {movement.quantity_after}
                    </span>
                  </div>
                  {movement.reason && <div className="movement-reason">{movement.reason}</div>}
                </div>
              ))
            )}
          </div>
        </section>
      )}

      <style>{`
        .inventory-manager {
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .inv-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 30px;
          border-bottom: 2px solid #f0f0f0;
          padding-bottom: 15px;
        }

        .inv-header h1 {
          margin: 0;
          font-size: 24px;
        }

        .inv-stats {
          display: flex;
          gap: 20px;
        }

        .stat {
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .stat-label {
          font-size: 12px;
          color: #6b7280;
          margin-bottom: 4px;
        }

        .stat-value {
          font-size: 20px;
          font-weight: 600;
          color: #1f2937;
        }

        .alert-badge {
          background: #fee2e2;
          color: #991b1b;
          padding: 2px 8px;
          border-radius: 12px;
        }

        .inv-tabs {
          display: flex;
          gap: 12px;
          margin-bottom: 20px;
          border-bottom: 1px solid #e5e7eb;
        }

        .inv-tabs button {
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

        .inv-tabs button.active {
          border-bottom-color: #2563eb;
          color: #2563eb;
        }

        .inv-section {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          overflow: hidden;
        }

        .inv-table {
          width: 100%;
          border-collapse: collapse;
        }

        .inv-table thead {
          background: #f9fafb;
          border-bottom: 2px solid #e5e7eb;
        }

        .inv-table th {
          padding: 12px 16px;
          text-align: left;
          font-size: 13px;
          font-weight: 600;
          color: #4b5563;
        }

        .inv-table td {
          padding: 12px 16px;
          border-bottom: 1px solid #f3f4f6;
        }

        .inv-table tbody tr.status-in_stock {
          background: #fafbf9;
        }

        .inv-table tbody tr.status-low_stock {
          background: #fffbf0;
        }

        .inv-table tbody tr.status-out_of_stock {
          background: #fffaf9;
        }

        .product-cell {
          max-width: 200px;
        }

        .product-name {
          display: block;
          font-weight: 500;
          color: #1f2937;
        }

        .product-id {
          display: block;
          font-size: 12px;
          color: #9ca3af;
          margin-top: 2px;
        }

        .demo-badge {
          display: inline-block;
          background: #dbeafe;
          color: #1e40af;
          padding: 2px 8px;
          border-radius: 3px;
          font-size: 11px;
          font-weight: 600;
          margin-top: 4px;
        }

        .available-qty {
          font-weight: 600;
          color: #22c55e;
        }

        .status-badge {
          display: inline-block;
          padding: 4px 10px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 600;
          color: white;
        }

        .actions-cell {
          display: flex;
          gap: 6px;
        }

        .btn-sm {
          padding: 6px 10px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          background: white;
          cursor: pointer;
          font-size: 12px;
          font-weight: 500;
          transition: all 0.2s;
        }

        .btn-sm:hover:not(:disabled) {
          background: #f3f4f6;
        }

        .btn-sm:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-add {
          color: #22c55e;
          border-color: #22c55e;
        }

        .btn-remove {
          color: #ef4444;
          border-color: #ef4444;
        }

        .alerts-list {
          padding: 20px;
        }

        .alert-item {
          padding: 16px;
          border: 1px solid #fecaca;
          border-radius: 6px;
          margin-bottom: 12px;
          background: #fffaf9;
        }

        .alert-item.acknowledged {
          border-color: #bbf7d0;
          background: #f0fdf4;
        }

        .alert-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .alert-header h3 {
          margin: 0;
          font-size: 16px;
        }

        .alert-created {
          font-size: 12px;
          color: #6b7280;
        }

        .alert-details {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
          margin-bottom: 12px;
        }

        .detail {
          display: flex;
          justify-content: space-between;
        }

        .detail .label {
          color: #6b7280;
          font-size: 13px;
        }

        .detail .value {
          font-weight: 600;
          color: #1f2937;
        }

        .alert-actions {
          display: flex;
          gap: 8px;
        }

        .btn-acknowledge {
          background: #fbbf24;
          color: white;
          border: none;
        }

        .acknowledged-badge {
          display: inline-block;
          background: #22c55e;
          color: white;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 600;
        }

        .reorder-badge {
          display: inline-block;
          background: #3b82f6;
          color: white;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 600;
        }

        .history-list {
          padding: 0;
        }

        .history-item {
          padding: 12px 16px;
          border-bottom: 1px solid #e5e7eb;
          display: grid;
          grid-template-columns: 100px 120px 100px 1fr;
          gap: 16px;
          align-items: center;
        }

        .history-item:last-child {
          border-bottom: none;
        }

        .movement-time {
          font-size: 12px;
          color: #6b7280;
          font-family: monospace;
        }

        .movement-type {
          font-size: 13px;
          font-weight: 600;
          color: #1f2937;
        }

        .movement-qty {
          display: flex;
          gap: 8px;
          align-items: center;
        }

        .movement-qty span.positive {
          color: #22c55e;
          font-weight: 600;
        }

        .movement-qty span.negative {
          color: #ef4444;
          font-weight: 600;
        }

        .movement-summary {
          font-size: 12px;
          color: #6b7280;
        }

        .movement-reason {
          font-size: 12px;
          color: #6b7280;
        }

        .empty-state {
          padding: 40px 20px;
          text-align: center;
          color: #9ca3af;
        }

        @media (max-width: 1024px) {
          .inv-table {
            font-size: 13px;
          }

          .inv-table th,
          .inv-table td {
            padding: 8px 12px;
          }

          .history-item {
            grid-template-columns: 1fr;
            gap: 4px;
          }
        }
      `}</style>
    </div>
  );
};
