'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export const ABMIntentDashboard = ({ accountId }: { accountId: string }) => {
  const intentScore = 72;
  const signals = [
    { signal: 'Page views', weight: 0.2, value: 15 },
    { signal: 'Email opens', weight: 0.15, value: '55%' },
    { signal: 'Demo request', weight: 0.3, value: 1 },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>🎯 ABM Intent Score</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-center p-4 bg-blue-50 rounded-lg">
          <p className="text-4xl font-bold text-blue-600">{intentScore}</p>
          <p className="text-sm text-blue-700 mt-1">CONSIDERATION (60-80)</p>
        </div>
        <div className="space-y-2">
          <p className="font-semibold text-sm">Top Signals:</p>
          {signals.map((s, idx) => (
            <div key={idx} className="flex justify-between items-center p-2 bg-gray-50 rounded">
              <span className="text-sm">{s.signal}</span>
              <span className="font-semibold">{s.value}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
