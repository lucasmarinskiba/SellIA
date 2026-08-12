'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface UrgencyTrigger {
  type: string;
  trigger: string;
  psychology: string;
  how_to_deploy: string;
}

interface UrgencyTriggersPanelProps {
  dealId: string;
  stage: string;
  industry: string;
}

export const UrgencyTriggersPanel = ({ dealId, stage, industry }: UrgencyTriggersPanelProps) => {
  const [triggers, setTriggers] = useState<UrgencyTrigger[]>([]);
  const [loading, setLoading] = useState(true);
  const [deployed, setDeployed] = useState<string[]>([]);

  useEffect(() => {
    fetchTriggers();
  }, [stage, industry]);

  const fetchTriggers = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/psychology/urgency-triggers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ deal_id: dealId, stage, industry }),
      });
      const data = await res.json();
      setTriggers(data.triggers || []);
    } catch (error) {
      console.error('Failed to fetch triggers:', error);
    } finally {
      setLoading(false);
    }
  };

  const deployTrigger = (triggerType: string) => {
    setDeployed([...deployed, triggerType]);
  };

  const triggerIcons: Record<string, string> = {
    supply_scarcity: '📦',
    price_increase: '💰',
    social_proof: '👥',
    competitive_threat: '⚔️',
  };

  if (loading) {
    return <div>Loading urgency triggers...</div>;
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>FOMO & Urgency Triggers</CardTitle>
        <p className="text-sm text-gray-600 mt-2">
          Legitimate triggers to create buying urgency (supply scarcity, pricing, social proof, competitive threats)
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {triggers.map((trigger) => {
          const isDeployed = deployed.includes(trigger.type);

          return (
            <div
              key={trigger.type}
              className={`border-2 rounded-lg p-4 transition ${
                isDeployed
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 hover:border-orange-400'
              }`}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{triggerIcons[trigger.type] || '⏰'}</span>
                  <div>
                    <p className="font-semibold text-gray-900">{trigger.trigger}</p>
                    <p className="text-xs text-gray-600">
                      {trigger.type.replace('_', ' ').toUpperCase()}
                    </p>
                  </div>
                </div>
                {isDeployed && (
                  <span className="text-xs font-semibold text-green-700 px-2 py-1 bg-green-100 rounded">
                    ✓ Deployed
                  </span>
                )}
              </div>

              {/* Psychology */}
              <div className="bg-blue-50 border-l-4 border-blue-500 p-3 mb-3">
                <p className="text-xs font-semibold text-blue-900 mb-1">Psychology:</p>
                <p className="text-sm text-blue-800">{trigger.psychology}</p>
              </div>

              {/* How to Deploy */}
              <div className="bg-orange-50 p-3 mb-3">
                <p className="text-xs font-semibold text-orange-900 mb-1">How to Deploy:</p>
                <p className="text-sm text-orange-800">{trigger.how_to_deploy}</p>
              </div>

              {/* Deploy Button */}
              {!isDeployed && (
                <button
                  onClick={() => deployTrigger(trigger.type)}
                  className="w-full py-2 px-3 text-sm font-semibold text-white bg-orange-600 hover:bg-orange-700 rounded transition"
                >
                  Use This Trigger
                </button>
              )}
            </div>
          );
        })}

        {/* Deployed Summary */}
        {deployed.length > 0 && (
          <div className="mt-6 pt-6 border-t">
            <p className="text-sm font-semibold text-gray-900 mb-3">
              Deployed Triggers ({deployed.length})
            </p>
            <div className="bg-green-50 p-4 rounded-lg">
              <ul className="space-y-2">
                {deployed.map((trigger) => (
                  <li key={trigger} className="text-sm text-green-700">
                    ✓ {trigger.replace('_', ' ')}
                  </li>
                ))}
              </ul>
            </div>
            <p className="text-xs text-gray-600 mt-3">
              Remember: Deploy triggers naturally throughout the conversation. Never feel pushy — the urgency should feel
              legitimate to the prospect.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
