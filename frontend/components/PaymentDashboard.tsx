import React, { useState, useEffect } from 'react';
import { CreditCard, DollarSign, TrendingUp, AlertCircle, Download, RefreshCw, CheckCircle, XCircle } from 'lucide-react';

const PaymentDashboard: React.FC<{ businessId: string }> = ({ businessId }) => {
  const [metrics, setMetrics] = useState<any>(null);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState(30);
  const [settlementMetrics, setSettlementMetrics] = useState<any>(null);

  useEffect(() => {
    fetchPaymentMetrics();
    fetchTransactions();
    fetchSettlementMetrics();
  }, [businessId, selectedPeriod]);

  const fetchPaymentMetrics = async () => {
    try {
      const res = await fetch(
        `/api/v1/businesses/${businessId}/payments/metrics`
      );
      const data = await res.json();
      setMetrics(data);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    }
  };

  const fetchTransactions = async () => {
    try {
      const res = await fetch(
        `/api/v1/businesses/${businessId}/transactions?limit=10&status=approved`
      );
      const data = await res.json();
      setTransactions(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
      setLoading(false);
    }
  };

  const fetchSettlementMetrics = async () => {
    try {
      const res = await fetch(
        `/api/v1/businesses/${businessId}/settlements/metrics?period_days=${selectedPeriod}`
      );
      const data = await res.json();
      setSettlementMetrics(data);
    } catch (error) {
      console.error('Failed to fetch settlement metrics:', error);
    }
  };

  if (loading) {
    return (
      <div className="w-full flex items-center justify-center p-8">
        <div className="text-gray-500">Cargando datos de pagos...</div>
      </div>
    );
  }

  return (
    <div className="w-full space-y-6 p-6 bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Pagos & Settlement</h1>
          <p className="text-gray-600 mt-1">Gestión de pagos con Mercado Pago</p>
        </div>
        <button
          onClick={() => {
            fetchPaymentMetrics();
            fetchTransactions();
            fetchSettlementMetrics();
          }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <RefreshCw className="w-4 h-4" />
          Actualizar
        </button>
      </div>

      {/* Period Selector */}
      <div className="flex gap-2">
        {[7, 30, 90].map((days) => (
          <button
            key={days}
            onClick={() => setSelectedPeriod(days)}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              selectedPeriod === days
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            Últimos {days} días
          </button>
        ))}
      </div>

      {/* KPI Cards */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Ingresos Totales</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  ${metrics.total_revenue?.toLocaleString() || 0}
                </p>
              </div>
              <DollarSign className="w-10 h-10 text-green-600 opacity-50" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Transacciones</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {metrics.total_transactions || 0}
                </p>
              </div>
              <CreditCard className="w-10 h-10 text-blue-600 opacity-50" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Tasa Éxito</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {metrics.success_rate || 0}%
                </p>
              </div>
              <CheckCircle className="w-10 h-10 text-emerald-600 opacity-50" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Ticket Promedio</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  ${metrics.avg_transaction_value?.toLocaleString() || 0}
                </p>
              </div>
              <TrendingUp className="w-10 h-10 text-orange-600 opacity-50" />
            </div>
          </div>
        </div>
      )}

      {/* Settlement Metrics */}
      {settlementMetrics && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Settlement - Últimos {selectedPeriod} días</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Monto Bruto</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                ${settlementMetrics.total_amount?.toLocaleString() || 0}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Comisiones</p>
              <p className="text-2xl font-bold text-red-600 mt-1">
                -${settlementMetrics.total_fees?.toLocaleString() || 0}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Neto (después refunds)</p>
              <p className="text-2xl font-bold text-green-600 mt-1">
                ${settlementMetrics.net_after_refunds?.toLocaleString() || 0}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Recent Transactions */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-bold text-gray-900">Transacciones Recientes</h2>
        </div>
        {transactions.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No hay transacciones aprobadas
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">ID</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Monto</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Método</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Estado</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Fecha</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {transactions.map((tx) => (
                  <tr key={tx.transaction_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900 font-mono">
                      {tx.transaction_id.slice(0, 8)}...
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                      ${tx.amount?.toLocaleString()} {tx.currency}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {tx.method === 'mercadopago' ? 'Mercado Pago' : tx.method}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                        {tx.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {new Date(tx.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Payment Methods Breakdown */}
      {metrics?.method_breakdown && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Métodos de Pago</h2>
          <div className="space-y-3">
            {Object.entries(metrics.method_breakdown).map(([method, amount]: any) => (
              <div key={method} className="flex items-center justify-between">
                <span className="text-sm text-gray-600 capitalize">{method}</span>
                <div className="flex items-center gap-3">
                  <div className="w-40 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{
                        width: `${(amount / (metrics.total_revenue || 1)) * 100}%`,
                      }}
                    ></div>
                  </div>
                  <span className="text-sm font-semibold text-gray-900 w-24 text-right">
                    ${amount.toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info Card */}
      <div className="bg-blue-50 border border-blue-200 p-6 rounded-lg">
        <div className="flex gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-blue-900">Pagos con Mercado Pago</h3>
            <p className="text-sm text-blue-800 mt-1">
              Los pagos se procesan automáticamente mediante Mercado Pago. Los webhooks actualizan el estado en tiempo real.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentDashboard;
