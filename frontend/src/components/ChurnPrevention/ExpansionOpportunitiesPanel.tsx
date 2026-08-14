'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export const ExpansionOpportunitiesPanel = ({ customerId }: { customerId: string }) => {
  const opportunities = [
    { feature: 'Automation', revenue: 20000, likelihood: 0.7 },
    { feature: 'Custom Dashboards', revenue: 15000, likelihood: 0.6 },
    { feature: 'Seat Expansion (5 seats)', revenue: 10000, likelihood: 0.85 },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>💰 Expansion Opportunities</CardTitle>
        <p className="text-sm text-gray-600 mt-2">Upsell + Cross-sell ranked by expected value</p>
      </CardHeader>
      <CardContent className="space-y-3">
        {opportunities.map((opp, idx) => (
          <div key={idx} className="flex items-center justify-between p-3 bg-blue-50 rounded border-l-4 border-blue-500">
            <div>
              <p className="font-medium text-gray-900">{opp.feature}</p>
              <p className="text-xs text-gray-600">Expected value: ${(opp.revenue * opp.likelihood).toFixed(0)}/year</p>
            </div>
            <button className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700">
              Launch
            </button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

