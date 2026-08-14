'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface ChurnPrediction {
  customer_id: string;
  churn_probability: number;
  risk_level: string;
  churn_reasons: Array<{ reason: string; impact: number }>;
  retention_offer: string;
}

export const ChurnRiskDashboard = () => {
  const [predictions, setPredictions] = useState<ChurnPrediction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPredictions();
  }, []);

  const fetchPredictions = async () => {
    setLoading(true);
    try {
      // Mock: in production fetch from multiple customers
      const mockPredictions: ChurnPrediction[] = [
        {
          customer_id: 'cust-001',
          churn_probability: 0.78,
          risk_level: 'HIGH',
          churn_reasons: [
            { reason: 'No login for 45 days', impact: 0.35 },
            { reason: 'Support tickets down 60%', impact: 0.28 },
          ],
          retention_offer: '40% discount 6 months',
        },
        {
          customer_id: 'cust-002',
          churn_probability: 0.52,
          risk_level: 'MEDIUM',
          churn_reasons: [{ reason: 'Competitor mentions', impact: 0.4 }],
          retention_offer: '20% discount + premium features',
        },
        {
          customer_id: 'cust-003',
          churn_probability: 0.28,
          risk_level: 'LOW',
          churn_reasons: [],
          retention_offer: 'Monitor',
        },
      ];
      setPredictions(mockPredictions);
    } catch (error) {
      console.error('Failed to fetch churn predictions:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading churn predictions...</div>;

  const riskColors = {
    HIGH: 'bg-red-100 border-red-500 text-red-900',
    MEDIUM: 'bg-yellow-100 border-yellow-500 text-yellow-900',
    LOW: 'bg-green-100 border-green-500 text-green-900',
  };

  const riskIcons = {
    HIGH: '🚨',
    MEDIUM: '⚠️',
    LOW: '✓',
  };

  const highRisk = predictions.filter((p) => p.risk_level === 'HIGH');
  const mediumRisk = predictions.filter((p) => p.risk_level === 'MEDIUM');

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6 text-center">
            <p className="text-4xl font-bold text-red-600">{highRisk.length}</p>
            <p className="text-sm text-red-700 mt-1">HIGH RISK</p>
            <p className="text-xs text-red-600">Immediate action needed</p>
          </CardContent>
        </Card>
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6 text-center">
            <p className="text-4xl font-bold text-yellow-600">{mediumRisk.length}</p>
            <p className="text-sm text-yellow-700 mt-1">MEDIUM RISK</p>
            <p className="text-xs text-yellow-600">Monitor closely</p>
          </CardContent>
        </Card>
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6 text-center">
            <p className="text-4xl font-bold text-green-600">{predictions.length - highRisk.length - mediumRisk.length}</p>
            <p className="text-sm text-green-700 mt-1">HEALTHY</p>
            <p className="text-xs text-green-600">No action needed</p>
          </CardContent>
        </Card>
      </div>

      {/* HIGH RISK Customers */}
      {highRisk.length > 0 && (
        <Card className="border-2 border-red-500">
          <CardHeader className="bg-red-50">
            <CardTitle className="text-red-900">🚨 High Risk - Immediate Action</CardTitle>
          </CardHeader>
          <CardContent className="pt-6 space-y-3">
            {highRisk.map((pred) => (
              <div key={pred.customer_id} className="border-l-4 border-red-500 pl-4 py-3 bg-gray-50 rounded">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-semibold text-gray-900">{pred.customer_id}</p>
                    <p className="text-xs text-gray-600 mt-1">Churn Risk: {Math.round(pred.churn_probability * 100)}%</p>
                  </div>
                  <button className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition">
                    Launch Campaign
                  </button>
                </div>
                <div className="mt-2 space-y-1">
                  {pred.churn_reasons.map((reason, idx) => (
                    <p key={idx} className="text-sm text-gray-700">
                      • {reason.reason} ({Math.round(reason.impact * 100)}%)
                    </p>
                  ))}
                </div>
                <p className="text-xs bg-green-100 text-green-900 mt-2 p-2 rounded">
                  💡 Suggested: {pred.retention_offer}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* MEDIUM RISK Customers */}
      {mediumRisk.length > 0 && (
        <Card>
          <CardHeader className="bg-yellow-50">
            <CardTitle className="text-yellow-900">⚠️ Medium Risk - Monitor & Engage</CardTitle>
          </CardHeader>
          <CardContent className="pt-6 space-y-2">
            {mediumRisk.map((pred) => (
              <div key={pred.customer_id} className="flex items-center justify-between p-3 bg-gray-50 rounded border-l-4 border-yellow-500">
                <div>
                  <p className="font-medium text-gray-900">{pred.customer_id}</p>
                  <p className="text-xs text-gray-600">{Math.round(pred.churn_probability * 100)}% risk</p>
                </div>
                <button className="px-3 py-1 text-xs bg-yellow-600 text-white rounded hover:bg-yellow-700 transition">
                  Check In
                </button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

