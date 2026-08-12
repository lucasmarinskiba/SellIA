'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

interface Question {
  question: string;
  psychology: string;
  category: string;
}

interface DiscoveryQuestionsFlowProps {
  dealId: string;
  prospectId: string;
}

export const DiscoveryQuestionsFlow = ({ dealId, prospectId }: DiscoveryQuestionsFlowProps) => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [currentResponse, setCurrentResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState('rapport');

  const stages = ['rapport', 'problem', 'impact', 'status_quo', 'desired', 'authority'];
  const stageLabels = {
    rapport: 'Building Rapport',
    problem: 'Identifying Problems',
    impact: 'Quantifying Impact',
    status_quo: 'Current State',
    desired: 'Desired State',
    authority: 'Authority & Decision',
  };

  useEffect(() => {
    fetchQuestions();
  }, [stage]);

  const fetchQuestions = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/psychology/discovery-questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prospect_id: prospectId, deal_id: dealId, stage }),
      });
      const data = await res.json();
      setQuestions(data.questions || []);
      setCurrentIndex(0);
    } catch (error) {
      console.error('Failed to fetch questions:', error);
    } finally {
      setLoading(false);
    }
  };

  const recordResponse = async () => {
    if (!currentResponse.trim()) return;

    try {
      await fetch('/api/v1/psychology/record-response', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deal_id: dealId,
          question: questions[currentIndex].question,
          response: currentResponse,
        }),
      });

      responses[questions[currentIndex].question] = currentResponse;
      setResponses(responses);
      setCurrentResponse('');

      if (currentIndex < questions.length - 1) {
        setCurrentIndex(currentIndex + 1);
      } else {
        moveToNextStage();
      }
    } catch (error) {
      console.error('Failed to record response:', error);
    }
  };

  const moveToNextStage = () => {
    const nextStageIndex = stages.indexOf(stage) + 1;
    if (nextStageIndex < stages.length) {
      setStage(stages[nextStageIndex]);
    }
  };

  if (loading) {
    return <div>Loading questions...</div>;
  }

  if (!questions.length) {
    return <div>No questions available</div>;
  }

  const currentQuestion = questions[currentIndex];
  const progress = ((currentIndex + 1) / questions.length) * 100;

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="text-lg">
          {stageLabels[stage as keyof typeof stageLabels]} ({currentIndex + 1}/{questions.length})
        </CardTitle>
        <div className="mt-4 bg-gray-200 rounded-full h-2">
          <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${progress}%` }} />
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Psychology Principle */}
        <div className="bg-blue-50 border-l-4 border-blue-500 p-3">
          <p className="text-xs font-semibold text-blue-900">Psychology:</p>
          <p className="text-sm text-blue-800">{currentQuestion.psychology}</p>
        </div>

        {/* Question */}
        <div>
          <p className="text-lg font-semibold text-gray-900 mb-4">{currentQuestion.question}</p>
        </div>

        {/* Response Input */}
        <div>
          <Textarea
            placeholder="Prospect's response..."
            value={currentResponse}
            onChange={(e) => setCurrentResponse(e.target.value)}
            rows={4}
            className="w-full"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 justify-end">
          {currentIndex > 0 && (
            <Button
              variant="outline"
              onClick={() => setCurrentIndex(currentIndex - 1)}
            >
              Previous
            </Button>
          )}
          <Button
            onClick={recordResponse}
            disabled={!currentResponse.trim()}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {currentIndex === questions.length - 1 ? 'Complete Stage' : 'Next Question'}
          </Button>
        </div>

        {/* Previous Responses Summary */}
        {Object.keys(responses).length > 0 && (
          <div className="mt-6 pt-6 border-t">
            <p className="text-xs font-semibold text-gray-600 mb-3">Responses So Far:</p>
            <div className="space-y-2 text-sm">
              {Object.entries(responses).map(([q, r]) => (
                <div key={q} className="bg-gray-50 p-2 rounded">
                  <p className="font-medium text-gray-700">{q}</p>
                  <p className="text-gray-600">{r}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
