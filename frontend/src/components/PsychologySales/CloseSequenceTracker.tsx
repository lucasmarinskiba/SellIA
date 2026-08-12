'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

interface CloseStep {
  next_close: string;
  step: number;
  psychology: string;
  is_positive_response: boolean;
}

interface CloseSequenceTrackerProps {
  dealId: string;
}

const CLOSE_SEQUENCE = [
  {
    step: 1,
    name: 'Small YES',
    description: 'Low-barrier commitment',
    psychology: 'Get them used to saying yes. Start with tiny commitment.',
    example: 'Can we schedule 30 minutes Friday to walk through this?',
  },
  {
    step: 2,
    name: 'Choice Between',
    description: 'Assume they\'re buying (not "will you" but "which")',
    psychology: 'Shift from whether to which. Frame as already decided.',
    example: 'Would you prefer weekly or bi-weekly implementation?',
  },
  {
    step: 3,
    name: 'Pilot',
    description: 'Remove risk perception',
    psychology: 'Lower barrier with time-limited trial. "Test drive" mentality.',
    example: 'Let\'s start with a 30-day pilot at 50% cost to prove ROI.',
  },
  {
    step: 4,
    name: 'Upsell',
    description: 'Ride the momentum',
    psychology: 'They\'re already committed. Expand scope while energized.',
    example: 'Since we\'re moving forward, let\'s add the premium module.',
  },
  {
    step: 5,
    name: 'Full Commitment',
    description: 'Final close',
    psychology: 'Momentum is huge. Saying no now breaks their own narrative.',
    example: 'Great! Let\'s get this signed and start next week.',
  },
];

export const CloseSequenceTracker = ({ dealId }: CloseSequenceTrackerProps) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [prospectResponse, setProspectResponse] = useState('');
  const [closeResponse, setCloseResponse] = useState<CloseStep | null>(null);
  const [loading, setLoading] = useState(false);
  const [conversationLog, setConversationLog] = useState<Array<{ step: number; response: string }>>([]);
  const [dealClosed, setDealClosed] = useState(false);

  const getCloseResponse = async () => {
    if (!prospectResponse.trim()) return;

    setLoading(true);
    try {
      const res = await fetch('/api/v1/psychology/close', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deal_id: dealId,
          current_step: currentStep,
          prospect_response: prospectResponse,
        }),
      });
      const data = await res.json();
      setCloseResponse(data);
      setConversationLog([...conversationLog, { step: currentStep, response: prospectResponse }]);

      // Check if closed
      if (data.step === 5 && data.is_positive_response) {
        setDealClosed(true);
      } else if (data.step > currentStep) {
        setCurrentStep(data.step);
      }

      setProspectResponse('');
    } catch (error) {
      console.error('Failed to get close:', error);
    } finally {
      setLoading(false);
    }
  };

  if (dealClosed) {
    return (
      <Card className="w-full max-w-2xl border-2 border-green-500">
        <CardHeader className="bg-green-50">
          <CardTitle className="text-green-700">🎉 DEAL CLOSED!</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 py-6">
          <div className="bg-green-50 p-4 rounded-lg">
            <p className="text-green-800 font-semibold mb-2">Closing Summary:</p>
            <ol className="space-y-2 text-sm text-green-700">
              {conversationLog.map((log) => (
                <li key={`${log.step}-${log.response}`}>
                  Step {log.step}: <span className="font-medium">"{log.response}"</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Psychology Principle:</strong> By step 5, saying no means breaking the momentum THEY built. Each
              small yes made the next yes more likely.
            </p>
          </div>

          <Button className="w-full bg-green-600 hover:bg-green-700" size="lg">
            Send Contract & Move to Implementation
          </Button>
        </CardContent>
      </Card>
    );
  }

  const currentCloseInfo = CLOSE_SEQUENCE[currentStep - 1];

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>5-Step Assumptive Close Sequence</CardTitle>
        <div className="mt-4 space-y-2">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-semibold text-gray-700">Step {currentStep}/5</span>
            <span className="text-xs text-gray-600">{(currentStep / 5) * 100}% Complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${(currentStep / 5) * 100}%` }}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Close Sequence Steps */}
        <div className="grid grid-cols-5 gap-2">
          {CLOSE_SEQUENCE.map((step) => (
            <button
              key={step.step}
              onClick={() => setCurrentStep(step.step)}
              className={`p-3 text-center rounded-lg border-2 transition ${
                currentStep === step.step
                  ? 'border-blue-500 bg-blue-50'
                  : conversationLog.some((log) => log.step === step.step)
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 hover:border-gray-400'
              }`}
            >
              <p className="text-xs font-bold">{step.step}</p>
              <p className="text-xs leading-tight mt-1">{step.name}</p>
            </button>
          ))}
        </div>

        {/* Current Step Details */}
        <div className="space-y-3">
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4">
            <p className="text-sm font-bold text-blue-900">{currentCloseInfo.name}</p>
            <p className="text-xs text-blue-800 mt-1">{currentCloseInfo.description}</p>
          </div>

          <div className="bg-purple-50 border-l-4 border-purple-500 p-4">
            <p className="text-xs font-bold text-purple-900 mb-1">Psychology:</p>
            <p className="text-sm text-purple-800">{currentCloseInfo.psychology}</p>
          </div>

          <div className="bg-gray-100 p-4 rounded-lg">
            <p className="text-xs font-semibold text-gray-700 mb-1">Example Close:</p>
            <p className="text-sm text-gray-900 italic">"{currentCloseInfo.example}"</p>
          </div>
        </div>

        {/* Response Input */}
        <div>
          <label className="text-sm font-semibold text-gray-700 mb-2 block">
            Prospect's Response to Step {currentStep}:
          </label>
          <Textarea
            placeholder="What did the prospect say?"
            value={prospectResponse}
            onChange={(e) => setProspectResponse(e.target.value)}
            rows={3}
            className="w-full"
          />
        </div>

        {/* AI Response */}
        {closeResponse && (
          <div className="space-y-3 pt-4 border-t">
            <div className="bg-green-50 border-l-4 border-green-500 p-4">
              <p className="text-xs font-bold text-green-900 mb-1">Your Next Close:</p>
              <p className="text-sm text-green-800">{closeResponse.next_close}</p>
            </div>

            {!closeResponse.is_positive_response && (
              <div className="bg-orange-50 border-l-4 border-orange-500 p-4">
                <p className="text-xs font-bold text-orange-900 mb-1">Note:</p>
                <p className="text-sm text-orange-800">
                  They objected. Stay on this step. Use objection handling psychology, then ask this close again.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Action Button */}
        <Button
          onClick={getCloseResponse}
          disabled={!prospectResponse.trim() || loading}
          className="w-full bg-blue-600 hover:bg-blue-700"
        >
          {loading ? 'Analyzing...' : `Get Step ${currentStep} Response`}
        </Button>

        {/* Conversation Log */}
        {conversationLog.length > 0 && (
          <div className="mt-6 pt-6 border-t">
            <p className="text-sm font-semibold text-gray-900 mb-3">Conversation Flow:</p>
            <div className="space-y-2">
              {conversationLog.map((log, idx) => (
                <div key={idx} className="text-sm bg-gray-50 p-3 rounded">
                  <p className="text-xs font-semibold text-gray-600">Step {log.step}</p>
                  <p className="text-gray-800">"{log.response}"</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
