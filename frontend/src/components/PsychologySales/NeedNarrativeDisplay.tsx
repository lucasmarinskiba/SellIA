'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface NeedNarrative {
  narrative: string;
  financial_impact: number;
  urgency_level: number;
}

interface NeedNarrativeDisplayProps {
  dealId: string;
  discoveryResponses: string[];
}

export const NeedNarrativeDisplay = ({ dealId, discoveryResponses }: NeedNarrativeDisplayProps) => {
  const [narrative, setNarrative] = useState<NeedNarrative | null>(null);
  const [loading, setLoading] = useState(false);

  const generateNarrative = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/psychology/create-need-narrative', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deal_id: dealId,
          discovery_responses: discoveryResponses,
        }),
      });
      const data = await res.json();
      setNarrative(data);
    } catch (error) {
      console.error('Failed to generate narrative:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!narrative) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Need Creation Narrative</CardTitle>
          <p className="text-sm text-gray-600 mt-2">
            Generate personalized need narrative from discovery responses to create urgency and quantify impact.
          </p>
        </CardHeader>
        <CardContent>
          <Button
            onClick={generateNarrative}
            disabled={loading || discoveryResponses.length === 0}
            className="w-full bg-green-600 hover:bg-green-700"
          >
            {loading ? 'Generating...' : 'Generate Need Narrative'}
          </Button>
        </CardContent>
      </Card>
    );
  }

  const urgencyColor = narrative.urgency_level > 7 ? 'red' : narrative.urgency_level > 4 ? 'yellow' : 'green';

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex justify-between items-start">
          <CardTitle>Need Creation Narrative</CardTitle>
          <div className={`text-sm font-semibold px-3 py-1 rounded-full bg-${urgencyColor}-50 text-${urgencyColor}-800`}>
            Urgency: {narrative.urgency_level}/10
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Narrative Text */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-sm leading-relaxed text-gray-800">
            {narrative.narrative}
          </p>
        </div>

        {/* Financial Impact Highlight */}
        <div className="border-2 border-red-500 rounded-lg p-4 bg-red-50">
          <p className="text-xs font-semibold text-red-900 mb-1">Annual Financial Impact</p>
          <p className="text-3xl font-bold text-red-700">
            ${(narrative.financial_impact / 1000).toFixed(0)}K
          </p>
          <p className="text-xs text-red-600 mt-2">
            This is what they're losing annually by not solving the problem
          </p>
        </div>

        {/* Psychology Points */}
        <div className="bg-blue-50 border-l-4 border-blue-500 p-4">
          <p className="text-xs font-semibold text-blue-900 mb-2">Psychology Framework:</p>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>✓ Validates their pain (they see it's real)</li>
            <li>✓ Quantifies impact (makes it visceral)</li>
            <li>✓ Creates urgency (cost of inaction)</li>
            <li>✓ Self-generated belief (they convinced themselves)</li>
          </ul>
        </div>

        {/* Next Steps */}
        <div className="pt-4 border-t">
          <p className="text-sm font-semibold text-gray-900 mb-2">Next Steps:</p>
          <ol className="text-sm text-gray-700 space-y-1 list-decimal list-inside">
            <li>Read this narrative to the prospect (don't pitch, let them absorb)</li>
            <li>Ask: "Does this match what you're experiencing?"</li>
            <li>Let them quantify further if they can</li>
            <li>Move to urgency triggers when ready</li>
          </ol>
        </div>

        <Button
          onClick={generateNarrative}
          variant="outline"
          className="w-full"
        >
          Regenerate Narrative
        </Button>
      </CardContent>
    </Card>
  );
};
