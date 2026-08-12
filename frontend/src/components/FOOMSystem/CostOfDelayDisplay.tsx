'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface CostOfDelayDisplayProps {
  annualLoss: number;
}

export const CostOfDelayDisplay = ({ annualLoss }: CostOfDelayDisplayProps) => {
  const [showBreakdown, setShowBreakdown] = useState(false);

  const monthly = annualLoss / 12;
  const daily = annualLoss / 365;
  const hourly = annualLoss / 8760;
  const perMinute = hourly / 60;

  // Calculate delay scenarios
  const scenarios = [
    { delay: 1, unit: 'day', cost: daily },
    { delay: 7, unit: 'week', cost: daily * 7 },
    { delay: 30, unit: 'month', cost: monthly },
    { delay: 90, unit: 'quarter', cost: monthly * 3 },
  ];

  return (
    <div className="space-y-4">
      {/* Main Cost Display */}
      <Card className="border-2 border-red-500 bg-red-50">
        <CardHeader>
          <CardTitle className="text-red-900">⏳ Cost of Every Delay</CardTitle>
          <p className="text-sm text-red-700 mt-2">
            What they lose by waiting instead of deciding NOW
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Minute-level cost */}
          <div className="text-center p-4 bg-red-100 rounded-lg">
            <p className="text-xs font-semibold text-red-900 mb-1">Per Minute</p>
            <p className="text-4xl font-bold text-red-700">${perMinute.toFixed(0)}</p>
            <p className="text-xs text-red-600 mt-1">While we're talking, they're losing this</p>
          </div>

          {/* Hour/Day cost */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-red-100 rounded-lg text-center">
              <p className="text-xs font-semibold text-red-900">Per Hour</p>
              <p className="text-2xl font-bold text-red-700">${hourly.toFixed(0)}</p>
            </div>
            <div className="p-3 bg-red-100 rounded-lg text-center">
              <p className="text-xs font-semibold text-red-900">Per Day</p>
              <p className="text-2xl font-bold text-red-700">${daily.toFixed(0)}</p>
            </div>
          </div>

          {/* Urgency message */}
          <div className="bg-red-600 text-white p-4 rounded-lg text-center">
            <p className="text-lg font-bold">
              Every week you wait costs ${(daily * 7).toFixed(0)}
            </p>
            <p className="text-sm mt-2 opacity-90">
              This is real money. Today vs next week = ${(daily * 7).toFixed(0)} difference.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Delay Scenarios */}
      <Card>
        <CardHeader>
          <CardTitle>If They Wait...</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {scenarios.map((scenario, idx) => (
            <div
              key={idx}
              className="flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
            >
              <div>
                <p className="font-semibold text-gray-900">Wait {scenario.delay} {scenario.unit}</p>
                <p className="text-xs text-gray-600">from now</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-red-600">${scenario.cost.toFixed(0)}</p>
                <p className="text-xs text-gray-500">lost</p>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Psychology explanation */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <p className="text-sm font-semibold text-blue-900 mb-2">💡 Psychology:</p>
          <ul className="space-y-2 text-sm text-blue-800">
            <li>✓ Loss aversion: Framing cost of inaction (not action)</li>
            <li>✓ Urgency: Time has a price. Waiting = hemorrhaging money</li>
            <li>✓ Concreteness: $X/day is more real than problems discussed</li>
            <li>✓ Regret aversion: "I'll have wasted $XXX by waiting"</li>
          </ul>
        </CardContent>
      </Card>

      {/* How to use */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">How to Deploy This</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="space-y-3 text-sm">
            <li>
              <span className="font-semibold">1. Calculate their annual loss</span>
              <p className="text-xs text-gray-600 mt-1">"So that's $X/year you're losing today. Correct?"</p>
            </li>
            <li>
              <span className="font-semibold">2. Show daily cost</span>
              <p className="text-xs text-gray-600 mt-1">"That's ${daily.toFixed(0)}/day. Every single day."</p>
            </li>
            <li>
              <span className="font-semibold">3. Apply to their hesitation</span>
              <p className="text-xs text-gray-600 mt-1">
                "If you think about it for 2 weeks, that's ${(daily * 14).toFixed(0)} in lost opportunity."
              </p>
            </li>
            <li>
              <span className="font-semibold">4. Create decision urgency</span>
              <p className="text-xs text-gray-600 mt-1">
                "Does it make sense to lose ${daily.toFixed(0)}/day while you decide?"
              </p>
            </li>
          </ol>
        </CardContent>
      </Card>
    </div>
  );
};
