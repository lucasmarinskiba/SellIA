'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

interface ObjectionResponse {
  response: string;
  psychology: string;
  next_step: string;
}

interface ObjectionHandlerProps {
  dealId: string;
  prospectRole: string;
}

export const ObjectionHandler = ({ dealId, prospectRole }: ObjectionHandlerProps) => {
  const [objection, setObjection] = useState('');
  const [response, setResponse] = useState<ObjectionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [objectionType, setObjectionType] = useState<string | null>(null);

  const commonObjections = [
    { type: 'price', label: 'Price / Budget Objection', examples: 'Too expensive, over budget, not in the budget' },
    { type: 'time', label: 'Timing Objection', examples: 'Not the right time, need to think about it, revisit later' },
    { type: 'need', label: 'Need Objection', examples: 'Don\'t need this, not a priority, works fine now' },
    { type: 'authority', label: 'Authority Objection', examples: 'Need to talk to my boss, committee decision, not my call' },
  ];

  const handleObjection = async () => {
    if (!objection.trim()) return;

    setLoading(true);
    try {
      const res = await fetch('/api/v1/psychology/handle-objection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deal_id: dealId,
          objection,
          prospect_role: prospectRole,
        }),
      });
      const data = await res.json();
      setResponse(data);
    } catch (error) {
      console.error('Failed to handle objection:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!response) {
    return (
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle>Psychology-Based Objection Handling</CardTitle>
          <p className="text-sm text-gray-600 mt-2">
            Never dismiss objections. Validate → Reframe → Question
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Quick Selection */}
          <div>
            <p className="text-sm font-semibold text-gray-700 mb-3">Quick Select Common Objections:</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {commonObjections.map((obj) => (
                <button
                  key={obj.type}
                  onClick={() => setObjectionType(obj.type)}
                  className={`p-3 text-left border-2 rounded-lg transition ${
                    objectionType === obj.type
                      ? 'border-red-500 bg-red-50'
                      : 'border-gray-200 hover:border-red-300'
                  }`}
                >
                  <p className="font-medium text-sm">{obj.label}</p>
                  <p className="text-xs text-gray-600 mt-1">{obj.examples}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Text Input */}
          <div>
            <label className="text-sm font-semibold text-gray-700 mb-2 block">
              What's the prospect's exact objection?
            </label>
            <Textarea
              placeholder="e.g., 'I think it's too expensive for what we need'"
              value={objection}
              onChange={(e) => setObjection(e.target.value)}
              rows={4}
              className="w-full"
            />
          </div>

          {/* Handle Button */}
          <Button
            onClick={handleObjection}
            disabled={!objection.trim() || loading}
            className="w-full bg-red-600 hover:bg-red-700"
          >
            {loading ? 'Analyzing...' : 'Get Psychology-Based Response'}
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Objection Response Strategy</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Original Objection */}
        <div className="bg-gray-100 p-4 rounded-lg border-2 border-gray-300">
          <p className="text-xs font-semibold text-gray-600 mb-1">Prospect Said:</p>
          <p className="text-gray-900 font-medium">{objection}</p>
        </div>

        {/* Psychology Framework */}
        <div className="bg-blue-50 border-l-4 border-blue-500 p-4">
          <p className="text-xs font-semibold text-blue-900 mb-2">Framework: {response.psychology}</p>
          <div className="text-sm text-blue-800 space-y-2">
            <div>
              <p className="font-semibold">Step 1: Validate</p>
              <p className="text-xs mt-1">Never say "No, you're wrong." Accept their concern as real.</p>
            </div>
            <div>
              <p className="font-semibold">Step 2: Reframe</p>
              <p className="text-xs mt-1">Shift perspective so the concern is less significant.</p>
            </div>
            <div>
              <p className="font-semibold">Step 3: Question</p>
              <p className="text-xs mt-1">Ask them to think deeper — they overcome their own objection.</p>
            </div>
          </div>
        </div>

        {/* AI-Generated Response */}
        <div className="bg-green-50 border-l-4 border-green-500 p-4">
          <p className="text-xs font-semibold text-green-900 mb-2">Your Response:</p>
          <p className="text-sm text-green-800 leading-relaxed">{response.response}</p>
        </div>

        {/* Next Step */}
        <div className="bg-orange-50 border-l-4 border-orange-500 p-4">
          <p className="text-xs font-semibold text-orange-900 mb-2">Next Step:</p>
          <p className="text-sm text-orange-800">{response.next_step}</p>
        </div>

        {/* Tips */}
        <div className="bg-purple-50 p-4 rounded-lg">
          <p className="text-xs font-semibold text-purple-900 mb-2">💡 Tips:</p>
          <ul className="text-sm text-purple-800 space-y-1">
            <li>✓ Pause after your response — let them think</li>
            <li>✓ Listen for their real concern (often buried deeper)</li>
            <li>✓ Don't push back with logic — psychology wins over logic</li>
            <li>✓ If they're still hesitant, loop back to their discovered pain</li>
          </ul>
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-4 border-t">
          <Button
            onClick={() => {
              setResponse(null);
              setObjection('');
              setObjectionType(null);
            }}
            variant="outline"
            className="flex-1"
          >
            Handle Another Objection
          </Button>
          <Button className="flex-1 bg-green-600 hover:bg-green-700">
            Move to Closing
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
