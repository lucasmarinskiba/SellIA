'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface FOOMTrigger {
  type: string;
  trigger: string;
  psychology: string;
  urgency: number;
  deployment: string;
  channel: string;
}

interface RealTimeFOOMDashboardProps {
  dealId: string;
  autoRefreshMs?: number;
}

export const RealTimeFOOMDashboard = ({ dealId, autoRefreshMs = 5000 }: RealTimeFOOMDashboardProps) => {
  const [foomData, setFoomData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFOMData();
    const interval = setInterval(fetchFOMData, autoRefreshMs);
    return () => clearInterval(interval);
  }, [dealId]);

  const fetchFOMData = async () => {
    try {
      const res = await fetch(`/api/v1/foom/deal/${dealId}`);
      const data = await res.json();
      setFoomData(data);
    } catch (error) {
      console.error('Failed to fetch FOOM data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !foomData) {
    return <div>Loading FOOM metrics...</div>;
  }

  const foomColors: Record<string, string> = {
    LOW: 'bg-green-100 border-green-500 text-green-900',
    MEDIUM: 'bg-yellow-100 border-yellow-500 text-yellow-900',
    HIGH: 'bg-orange-100 border-orange-500 text-orange-900',
    CRITICAL: 'bg-red-100 border-red-500 text-red-900',
  };

  const foomIcons: Record<string, string> = {
    LOW: '😐',
    MEDIUM: '😲',
    HIGH: '😰',
    CRITICAL: '🚨',
  };

  return (
    <div className="space-y-6">
      {/* Main FOOM Score */}
      <Card className={`border-2 ${foomColors[foomData.foom_level]}`}>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle>Real-Time FOOM Status</CardTitle>
              <p className="text-xs mt-2 opacity-75">Updates every 5 seconds</p>
            </div>
            <div className="text-5xl">{foomIcons[foomData.foom_level]}</div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-xs font-semibold opacity-75">FOOM Level</p>
              <p className="text-2xl font-bold">{foomData.foom_level}</p>
            </div>
            <div>
              <p className="text-xs font-semibold opacity-75">Urgency Score</p>
              <p className="text-2xl font-bold">{foomData.foom_score}/10</p>
            </div>
            <div>
              <p className="text-xs font-semibold opacity-75">Active Triggers</p>
              <p className="text-2xl font-bold">{foomData.active_triggers}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* All Triggers */}
      <div>
        <h3 className="text-lg font-bold mb-3">Active FOOM Triggers</h3>
        <div className="grid gap-3">
          {foomData.triggers.map((trigger: FOOMTrigger, idx: number) => {
            const urgencyColor =
              trigger.urgency >= 9 ? 'red' :
              trigger.urgency >= 7 ? 'orange' :
              trigger.urgency >= 5 ? 'yellow' :
              'green';

            const channelIcons: Record<string, string> = {
              in_app: '💬',
              social: '📱',
              personal: '👤',
            };

            return (
              <Card key={idx} className="border-l-4" style={{ borderLeftColor: `var(--color-${urgencyColor}-500)` }}>
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">{channelIcons[trigger.channel] || '⏰'}</span>
                      <div>
                        <p className="font-semibold text-gray-900">{trigger.trigger}</p>
                        <p className="text-xs text-gray-600">{trigger.type.replace('_', ' ').toUpperCase()}</p>
                      </div>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-sm font-bold text-${urgencyColor}-900 bg-${urgencyColor}-100`}>
                      {trigger.urgency}/10
                    </div>
                  </div>

                  {/* Psychology */}
                  <div className="bg-blue-50 border-l-4 border-blue-500 p-3 my-3">
                    <p className="text-xs font-semibold text-blue-900 mb-1">Psychology:</p>
                    <p className="text-sm text-blue-800">{trigger.psychology}</p>
                  </div>

                  {/* Deployment */}
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-xs font-semibold text-gray-700 mb-1">How to Deploy:</p>
                    <p className="text-sm text-gray-800">{trigger.deployment}</p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Use This FOOM</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-3">
          <button className="p-3 bg-blue-50 hover:bg-blue-100 rounded-lg text-left transition">
            <p className="font-semibold text-blue-900">📱 Social Post</p>
            <p className="text-xs text-blue-700">Generate shareable content</p>
          </button>
          <button className="p-3 bg-orange-50 hover:bg-orange-100 rounded-lg text-left transition">
            <p className="font-semibold text-orange-900">📧 Email Subject</p>
            <p className="text-xs text-orange-700">High open-rate subject line</p>
          </button>
          <button className="p-3 bg-purple-50 hover:bg-purple-100 rounded-lg text-left transition">
            <p className="font-semibold text-purple-900">🎥 Video Script</p>
            <p className="text-xs text-purple-700">30-second viral script</p>
          </button>
          <button className="p-3 bg-green-50 hover:bg-green-100 rounded-lg text-left transition">
            <p className="font-semibold text-green-900">💰 Cost of Delay</p>
            <p className="text-xs text-green-700">Show financial impact</p>
          </button>
        </CardContent>
      </Card>

      {/* Timestamp */}
      <p className="text-xs text-gray-500 text-center">
        Last updated: {new Date().toLocaleTimeString()}
      </p>
    </div>
  );
};

