'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

interface MicroCommitmentSequenceProps {
  dealId: string;
}

const STEPS = [
  {
    step: 1,
    name: 'Quick Call',
    description: 'Tiny barrier to entry',
    psychology: 'Get them used to saying yes',
    ask: "Can we schedule 20 minutes Thursday?",
    ifno: "Stay on this. Don't push. Ask why.",
  },
  {
    step: 2,
    name: 'Share Challenge',
    description: 'They invest attention',
    psychology: 'When they talk, they own it',
    ask: "What's costing you the most right now?",
    ifno: "Ask what else matters to them.",
  },
  {
    step: 3,
    name: 'Use Case Walk',
    description: 'See value indirectly',
    psychology: 'Visualizing solution = ownership',
    ask: "Let me show how we'd handle your exact situation",
    ifno: "Ask which part concerns them most.",
  },
  {
    step: 4,
    name: 'See Pricing',
    description: 'Remove fear/mystery',
    psychology: 'Knowledge removes objections',
    ask: "Want to see how pricing would work for you?",
    ifno: "Say: 'Most companies like you are at X tier'",
  },
  {
    step: 5,
    name: 'Pilot Proposal',
    description: 'Lower risk trial',
    psychology: 'Trial removes perceived risk',
    ask: "Start with 30-day pilot at 50% cost?",
    ifno: "Ask what would make pilot safe.",
  },
  {
    step: 6,
    name: 'Legal Review',
    description: 'Assume they\'re buying',
    psychology: 'Shift from IF to WHEN',
    ask: "Can your legal team review the agreement this week?",
    ifno: "Ask what legal needs to see first.",
  },
  {
    step: 7,
    name: 'Implementation',
    description: 'Momentum is unstoppable',
    psychology: 'Saying NO breaks momentum they built',
    ask: "Let's schedule your team's first training day",
    ifno: "Move to CFO for final sign-off.",
  },
];

export const MicroCommitmentSequence = ({ dealId }: MicroCommitmentSequenceProps) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [prospectResponse, setProspectResponse] = useState('');
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [dealClosed, setDealClosed] = useState(false);

  const handleYes = () => {
    if (!completedSteps.includes(currentStep)) {
      setCompletedSteps([...completedSteps, currentStep]);
    }

    if (currentStep < 7) {
      setCurrentStep(currentStep + 1);
    } else {
      setDealClosed(true);
    }

    setProspectResponse('');
  };

  const handleNo = () => {
    // Stay on current step, ask differently
    setProspectResponse('');
  };

  const currentStepInfo = STEPS[currentStep - 1];

  if (dealClosed) {
    return (
      <Card className="w-full border-2 border-green-500 bg-green-50">
        <CardHeader className="bg-green-100">
          <CardTitle className="text-green-700">🎉 Deal Closed!</CardTitle>
        </CardHeader>
        <CardContent className="pt-6 space-y-4">
          <div className="bg-white border-2 border-green-300 p-4 rounded-lg">
            <p className="font-semibold text-green-900 mb-3">Micro-Commitments That Led to Closed Deal:</p>
            <ol className="space-y-2">
              {completedSteps.map((step) => {
                const stepInfo = STEPS[step - 1];
                return (
                  <li key={step} className="flex items-center gap-2 text-sm">
                    <span className="text-green-600 font-bold">✓</span>
                    <span className="text-gray-800">
                      Step {step}: {stepInfo.name}
                    </span>
                  </li>
                );
              })}
            </ol>
          </div>

          <div className="bg-blue-50 border-l-4 border-blue-500 p-4">
            <p className="text-sm font-semibold text-blue-900 mb-2">Why This Worked:</p>
            <p className="text-sm text-blue-800">
              Each small YES made the next YES more likely. By step 7, saying NO breaks the momentum THEY built.
              They convinced themselves through a series of tiny agreements.
            </p>
          </div>

          <Button className="w-full bg-green-600 hover:bg-green-700" size="lg">
            Send Contract & Move to Implementation
          </Button>
        </CardContent>
      </Card>
    );
  }

  const progress = (currentStep / 7) * 100;

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>7-Step Micro-Commitment Sequence</CardTitle>
        <div className="mt-4 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="font-semibold text-gray-700">Step {currentStep}/7</span>
            <span className="text-gray-600">{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Step Indicators */}
        <div className="grid grid-cols-7 gap-1">
          {STEPS.map((s) => (
            <button
              key={s.step}
              onClick={() => s.step <= currentStep && setCurrentStep(s.step)}
              className={`p-2 rounded text-xs font-bold transition ${
                currentStep === s.step
                  ? 'bg-blue-500 text-white'
                  : completedSteps.includes(s.step)
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
              }`}
            >
              {s.step}
            </button>
          ))}
        </div>

        {/* Current Step Details */}
        <div className="space-y-3 border-t pt-4">
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4">
            <p className="text-lg font-bold text-blue-900">{currentStepInfo.name}</p>
            <p className="text-sm text-blue-800 mt-1">{currentStepInfo.description}</p>
          </div>

          <div className="bg-purple-50 border-l-4 border-purple-500 p-4">
            <p className="text-xs font-bold text-purple-900 mb-1">Psychology:</p>
            <p className="text-sm text-purple-800">{currentStepInfo.psychology}</p>
          </div>

          <div className="bg-gray-100 p-4 rounded-lg">
            <p className="text-xs font-semibold text-gray-700 mb-1">What You Ask:</p>
            <p className="text-sm text-gray-900 font-medium">"{currentStepInfo.ask}"</p>
          </div>

          <div className="bg-orange-50 border-l-4 border-orange-500 p-4">
            <p className="text-xs font-bold text-orange-900 mb-1">If They Hesitate:</p>
            <p className="text-sm text-orange-800">{currentStepInfo.ifno}</p>
          </div>
        </div>

        {/* Response Input */}
        <div>
          <label className="text-sm font-semibold text-gray-700 mb-2 block">
            What did they say?
          </label>
          <Textarea
            placeholder="Enter their response..."
            value={prospectResponse}
            onChange={(e) => setProspectResponse(e.target.value)}
            rows={3}
            className="w-full"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button
            onClick={handleNo}
            variant="outline"
            className="flex-1"
          >
            ❌ They Hesitated
          </Button>
          <Button
            onClick={handleYes}
            disabled={!prospectResponse.trim()}
            className="flex-1 bg-green-600 hover:bg-green-700"
          >
            ✓ They Said YES
          </Button>
        </div>

        {/* Completed Steps Summary */}
        {completedSteps.length > 0 && (
          <div className="mt-6 pt-6 border-t">
            <p className="text-sm font-semibold text-gray-900 mb-3">
              Completed Steps ({completedSteps.length}/7)
            </p>
            <div className="bg-green-50 p-3 rounded-lg">
              <div className="space-y-1">
                {completedSteps.map((step) => {
                  const stepInfo = STEPS[step - 1];
                  return (
                    <div key={step} className="text-sm text-green-700">
                      ✓ Step {step}: {stepInfo.name}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Momentum info */}
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4">
          <p className="text-sm font-semibold text-yellow-900 mb-2">⚡ Momentum:</p>
          <p className="text-sm text-yellow-800">
            Each YES builds on the last. By step {Math.min(currentStep + 2, 7)}, they'll be hard to stop. Don't jump
            steps. The tiny wins matter more than the big ask.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

