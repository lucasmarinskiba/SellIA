'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export const CustomerHealthScorecard = ({ customerId }: { customerId: string }) => {
  const health = {
    score: 68,
    level: 'AT_RISK',
    churnRisk: 'MEDIUM',
    churnProb: 0.52,
    expansion: 35000,
    intent: 72,
    action: 'Schedule business review',
  };

  return (
    <Card className="border-2 border-yellow-200">
      <CardHeader className="bg-yellow-50">
        <CardTitle className="text-yellow-900">📊 Customer Health Scorecard</CardTitle>
      </CardHeader>
      <CardContent className="pt-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-yellow-100 rounded">
            <p className="text-3xl font-bold text-yellow-700">{health.score}</p>
            <p className="text-xs text-yellow-600">{health.level}</p>
          </div>
          <div className="text-center p-3 bg-blue-100 rounded">
            <p className="text-3xl font-bold text-blue-700">${(health.expansion / 1000).toFixed(0)}k</p>
            <p className="text-xs text-blue-600">Expansion potential</p>
          </div>
        </div>
        <div className="bg-orange-50 border-l-4 border-orange-500 p-3">
          <p className="text-sm font-semibold text-orange-900 mb-2">⚠️ Recommended Action:</p>
          <p className="text-sm text-orange-800">{health.action}</p>
        </div>
      </CardContent>
    </Card>
  );
};

