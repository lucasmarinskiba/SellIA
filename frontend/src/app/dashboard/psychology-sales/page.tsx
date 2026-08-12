'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  DiscoveryQuestionsFlow,
  NeedNarrativeDisplay,
  UrgencyTriggersPanel,
  ObjectionHandler,
  CloseSequenceTracker,
} from '@/components/PsychologySales';

interface DealParams {
  dealId?: string;
  prospectId?: string;
  industry?: string;
  stage?: string;
}

export default function PsychologySalesPage() {
  const [dealParams, setDealParams] = useState<DealParams>({
    dealId: 'deal-001',
    prospectId: 'prospect-001',
    industry: 'technology',
    stage: 'discovery',
  });

  const [activeTab, setActiveTab] = useState('discovery');
  const [discoveryResponses, setDiscoveryResponses] = useState<string[]>([]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="text-3xl">🎯</div>
          <h1 className="text-4xl font-bold text-gray-900">Jordan Belfort Psychology Sales</h1>
        </div>
        <p className="text-gray-600">
          Master the psychology of selling: Discovery → Needs → Urgency → Objections → Closing
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">Target Close Rate</p>
            <p className="text-3xl font-bold text-green-600">60%</p>
            <p className="text-xs text-gray-500 mt-2">vs 18% baseline</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">Sales Cycle</p>
            <p className="text-3xl font-bold text-blue-600">30 days</p>
            <p className="text-xs text-gray-500 mt-2">vs 85 days baseline</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">ACV Growth</p>
            <p className="text-3xl font-bold text-purple-600">3x</p>
            <p className="text-xs text-gray-500 mt-2">$50k → $150k+</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">Revenue Impact</p>
            <p className="text-3xl font-bold text-orange-600">$30M+</p>
            <p className="text-xs text-gray-500 mt-2">Year 1 ARR</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Workflow Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5 mb-8">
          <TabsTrigger value="discovery" className="flex flex-col items-center gap-1">
            <span className="text-lg">1</span>
            <span className="text-xs">Discovery</span>
          </TabsTrigger>
          <TabsTrigger value="needs" className="flex flex-col items-center gap-1">
            <span className="text-lg">2</span>
            <span className="text-xs">Needs</span>
          </TabsTrigger>
          <TabsTrigger value="urgency" className="flex flex-col items-center gap-1">
            <span className="text-lg">3</span>
            <span className="text-xs">Urgency</span>
          </TabsTrigger>
          <TabsTrigger value="objections" className="flex flex-col items-center gap-1">
            <span className="text-lg">4</span>
            <span className="text-xs">Objections</span>
          </TabsTrigger>
          <TabsTrigger value="close" className="flex flex-col items-center gap-1">
            <span className="text-lg">5</span>
            <span className="text-xs">Close</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Discovery */}
        <TabsContent value="discovery" className="space-y-6">
          <Card className="border-2 border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-blue-900">🔍 Stage 1: Discovery Questions</CardTitle>
              <p className="text-sm text-blue-700 mt-2">
                "The key to selling is not talking about the product, but asking questions to know the buyer's needs,
                desires and problems."
              </p>
            </CardHeader>
          </Card>

          <DiscoveryQuestionsFlow
            dealId={dealParams.dealId || 'deal-001'}
            prospectId={dealParams.prospectId || 'prospect-001'}
          />

          <div className="flex justify-end">
            <Button
              onClick={() => setActiveTab('needs')}
              className="bg-blue-600 hover:bg-blue-700"
              size="lg"
            >
              Responses Complete → Next: Create Need
            </Button>
          </div>
        </TabsContent>

        {/* Tab 2: Needs */}
        <TabsContent value="needs" className="space-y-6">
          <Card className="border-2 border-red-200 bg-red-50">
            <CardHeader>
              <CardTitle className="text-red-900">📊 Stage 2: Need Creation</CardTitle>
              <p className="text-sm text-red-700 mt-2">
                Quantify financial impact. Show the gap between current pain and desired state. Make pain REAL and
                URGENT.
              </p>
            </CardHeader>
          </Card>

          <NeedNarrativeDisplay
            dealId={dealParams.dealId || 'deal-001'}
            discoveryResponses={discoveryResponses}
          />

          <div className="flex justify-end gap-3">
            <Button
              onClick={() => setActiveTab('discovery')}
              variant="outline"
            >
              Back: Discovery
            </Button>
            <Button
              onClick={() => setActiveTab('urgency')}
              className="bg-red-600 hover:bg-red-700"
              size="lg"
            >
              Need Established → Next: Create FOMO
            </Button>
          </div>
        </TabsContent>

        {/* Tab 3: Urgency */}
        <TabsContent value="urgency" className="space-y-6">
          <Card className="border-2 border-orange-200 bg-orange-50">
            <CardHeader>
              <CardTitle className="text-orange-900">⏰ Stage 3: Urgency & FOMO</CardTitle>
              <p className="text-sm text-orange-700 mt-2">
                Generate legitimate urgency triggers. Supply scarcity, pricing, social proof, competitive threats.
                Deploy naturally throughout conversation.
              </p>
            </CardHeader>
          </Card>

          <UrgencyTriggersPanel
            dealId={dealParams.dealId || 'deal-001'}
            stage={dealParams.stage || 'proposal'}
            industry={dealParams.industry || 'technology'}
          />

          <div className="flex justify-end gap-3">
            <Button
              onClick={() => setActiveTab('needs')}
              variant="outline"
            >
              Back: Needs
            </Button>
            <Button
              onClick={() => setActiveTab('objections')}
              className="bg-orange-600 hover:bg-orange-700"
              size="lg"
            >
              Urgency Deployed → Next: Handle Objections
            </Button>
          </div>
        </TabsContent>

        {/* Tab 4: Objections */}
        <TabsContent value="objections" className="space-y-6">
          <Card className="border-2 border-purple-200 bg-purple-50">
            <CardHeader>
              <CardTitle className="text-purple-900">🛡️ Stage 4: Objection Handling</CardTitle>
              <p className="text-sm text-purple-700 mt-2">
                Never dismiss objections. Validate → Reframe → Question. Psychology beats logic.
              </p>
            </CardHeader>
          </Card>

          <ObjectionHandler
            dealId={dealParams.dealId || 'deal-001'}
            prospectRole="decision_maker"
          />

          <div className="flex justify-end gap-3">
            <Button
              onClick={() => setActiveTab('urgency')}
              variant="outline"
            >
              Back: Urgency
            </Button>
            <Button
              onClick={() => setActiveTab('close')}
              className="bg-purple-600 hover:bg-purple-700"
              size="lg"
            >
              Objections Handled → Next: Close
            </Button>
          </div>
        </TabsContent>

        {/* Tab 5: Closing */}
        <TabsContent value="close" className="space-y-6">
          <Card className="border-2 border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="text-green-900">✅ Stage 5: 5-Step Assumptive Close</CardTitle>
              <p className="text-sm text-green-700 mt-2">
                Build momentum with small commitments. By step 5, saying NO breaks the momentum THEY built.
              </p>
            </CardHeader>
          </Card>

          <CloseSequenceTracker dealId={dealParams.dealId || 'deal-001'} />

          <div className="flex justify-end">
            <Button
              onClick={() => setActiveTab('objections')}
              variant="outline"
            >
              Back: Objections
            </Button>
          </div>
        </TabsContent>
      </Tabs>

      {/* Psychology Framework Summary */}
      <div className="mt-12 grid grid-cols-1 md:grid-cols-5 gap-4">
        {[
          {
            stage: 'Discovery',
            icon: '🔍',
            principle: 'Ask, don\'t tell',
            psychology: 'Make them see their own problem',
          },
          {
            stage: 'Needs',
            icon: '📊',
            principle: 'Quantify pain',
            psychology: 'Self-generated belief > sales pitch',
          },
          {
            stage: 'Urgency',
            icon: '⏰',
            principle: 'Create legitimate FOMO',
            psychology: 'Decision: delay costs more than deciding now',
          },
          {
            stage: 'Objections',
            icon: '🛡️',
            principle: 'Validate → Reframe → Question',
            psychology: 'They overcome their own objections',
          },
          {
            stage: 'Close',
            icon: '✅',
            principle: 'Momentum building',
            psychology: 'Saying NO breaks momentum they built',
          },
        ].map((item, idx) => (
          <Card key={idx}>
            <CardContent className="pt-6 text-center">
              <div className="text-4xl mb-2">{item.icon}</div>
              <p className="font-semibold text-gray-900 text-sm">{item.stage}</p>
              <p className="text-xs text-gray-600 mt-2">{item.principle}</p>
              <p className="text-xs text-purple-600 font-semibold mt-2 italic">"{item.psychology}"</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-12 text-center text-gray-600 text-sm">
        <p>"The money's not in closing. The money's in the NEED." — Jordan Belfort</p>
        <p className="mt-2 text-xs text-gray-500">
          Every stage builds on the last. Skip none. Master all five.
        </p>
      </div>
    </div>
  );
}
