import React, { useState } from 'react';

interface Deal {
  id: string;
  name: string;
  customer: string;
  value: number;
  stage: 'prospect' | 'qualified' | 'proposal' | 'negotiation' | 'won';
  daysInStage: number;
  owner: string;
  probability: number;
}

interface Stage {
  id: string;
  name: string;
  deals: Deal[];
  color: string;
}

const SalesFunnel: React.FC = () => {
  const [stages, setStages] = useState<Stage[]>([
    {
      id: 'prospect',
      name: 'Prospect',
      color: 'from-blue-500 to-blue-600',
      deals: [
        { id: '1', name: 'Initial Call', customer: 'Global Corp', value: 50000, stage: 'prospect', daysInStage: 3, owner: 'Alice', probability: 20 },
        { id: '2', name: 'Research Phase', customer: 'TechFlow', value: 75000, stage: 'prospect', daysInStage: 5, owner: 'Bob', probability: 25 },
      ],
    },
    {
      id: 'qualified',
      name: 'Qualified',
      color: 'from-yellow-500 to-yellow-600',
      deals: [
        { id: '3', name: 'Needs Assessment', customer: 'Innovation Labs', value: 120000, stage: 'qualified', daysInStage: 7, owner: 'Charlie', probability: 45 },
        { id: '4', name: 'Budget Confirmed', customer: 'Enterprise Inc', value: 185000, stage: 'qualified', daysInStage: 4, owner: 'Alice', probability: 50 },
      ],
    },
    {
      id: 'proposal',
      name: 'Proposal',
      color: 'from-purple-500 to-purple-600',
      deals: [
        { id: '5', name: 'Custom Solution', customer: 'Future Corp', value: 95000, stage: 'proposal', daysInStage: 2, owner: 'David', probability: 65 },
        { id: '6', name: 'ROI Presentation', customer: 'Growth Partners', value: 140000, stage: 'proposal', daysInStage: 6, owner: 'Eve', probability: 70 },
      ],
    },
    {
      id: 'negotiation',
      name: 'Negotiation',
      color: 'from-orange-500 to-orange-600',
      deals: [
        { id: '7', name: 'Final Terms', customer: 'Apex Solutions', value: 165000, stage: 'negotiation', daysInStage: 3, owner: 'Frank', probability: 80 },
      ],
    },
    {
      id: 'won',
      name: 'Won',
      color: 'from-green-500 to-green-600',
      deals: [
        { id: '8', name: 'Signed Contract', customer: 'Success Inc', value: 200000, stage: 'won', daysInStage: 0, owner: 'Grace', probability: 100 },
        { id: '9', name: 'Implementation', customer: 'Victory Ltd', value: 180000, stage: 'won', daysInStage: 0, owner: 'Henry', probability: 100 },
      ],
    },
  ]);

  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null);
  const totalPipeline = stages.reduce((sum, stage) => sum + stage.deals.reduce((s, d) => s + d.value, 0), 0);
  const averageDealSize = totalPipeline / stages.reduce((sum, stage) => sum + stage.deals.length, 0);

  const moveDeal = (dealId: string, newStage: string) => {
    setStages(stages.map(stage => ({
      ...stage,
      deals: stage.deals.filter(d => d.id !== dealId),
    })).map(stage => {
      if (stage.id === newStage) {
        const deal = stages.flatMap(s => s.deals).find(d => d.id === dealId);
        if (deal) {
          return {
            ...stage,
            deals: [...stage.deals, { ...deal, stage: newStage as any, daysInStage: 0 }],
          };
        }
      }
      return stage;
    }));
    setSelectedDeal(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
      <div className="max-w-full mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-4">Sales Pipeline</h1>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
              <p className="text-slate-400 text-sm mb-1">Total Pipeline</p>
              <p className="text-2xl font-bold text-white">${(totalPipeline / 1000000).toFixed(2)}M</p>
            </div>
            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
              <p className="text-slate-400 text-sm mb-1">Active Deals</p>
              <p className="text-2xl font-bold text-white">{stages.reduce((sum, s) => sum + s.deals.length, 0)}</p>
            </div>
            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
              <p className="text-slate-400 text-sm mb-1">Avg Deal Size</p>
              <p className="text-2xl font-bold text-white">${(averageDealSize / 1000).toFixed(0)}K</p>
            </div>
          </div>
        </div>

        {/* Kanban Board */}
        <div className="flex gap-6 overflow-x-auto pb-6">
          {stages.map(stage => (
            <div key={stage.id} className="flex-shrink-0 w-80">
              <div className={`bg-gradient-to-br ${stage.color} rounded-t-lg p-4 text-white`}>
                <h2 className="text-lg font-bold">{stage.name}</h2>
                <p className="text-sm opacity-90">{stage.deals.length} deals • ${(stage.deals.reduce((s, d) => s + d.value, 0) / 1000).toFixed(0)}K</p>
              </div>
              <div className="bg-slate-800 rounded-b-lg p-4 min-h-96 border-l-2" style={{ borderColor: stage.color.split(' ')[1] }}>
                <div className="space-y-3">
                  {stage.deals.map(deal => (
                    <div
                      key={deal.id}
                      onClick={() => setSelectedDeal(deal)}
                      className="bg-slate-700 p-4 rounded-lg cursor-pointer hover:bg-slate-600 transition border border-slate-600 hover:border-blue-500"
                    >
                      <p className="text-white font-semibold">{deal.name}</p>
                      <p className="text-slate-400 text-sm">{deal.customer}</p>
                      <div className="flex justify-between items-center mt-3">
                        <p className="text-green-400 font-bold">${(deal.value / 1000).toFixed(0)}K</p>
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">{deal.owner[0]}</div>
                          <span className="text-slate-400 text-sm">{deal.probability}%</span>
                        </div>
                      </div>
                      <div className="mt-2 pt-2 border-t border-slate-600">
                        <p className="text-slate-500 text-xs">{deal.daysInStage} days in stage</p>
                      </div>
                    </div>
                  ))}
                  {stage.deals.length === 0 && (
                    <div className="text-center py-8 text-slate-500">
                      <p>No deals</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Deal Detail Modal */}
        {selectedDeal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full border border-slate-700">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-xl font-bold text-white">{selectedDeal.name}</h3>
                <button onClick={() => setSelectedDeal(null)} className="text-slate-400 hover:text-white">✕</button>
              </div>

              <div className="space-y-3 mb-6">
                <div>
                  <p className="text-slate-400 text-sm">Customer</p>
                  <p className="text-white font-semibold">{selectedDeal.customer}</p>
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Deal Value</p>
                  <p className="text-2xl font-bold text-green-400">${(selectedDeal.value / 1000).toFixed(0)}K</p>
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Win Probability</p>
                  <div className="w-full bg-slate-700 rounded-full h-2 mt-1">
                    <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${selectedDeal.probability}%` }}></div>
                  </div>
                  <p className="text-white font-semibold mt-1">{selectedDeal.probability}%</p>
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Owner</p>
                  <p className="text-white font-semibold">{selectedDeal.owner}</p>
                </div>
              </div>

              <div className="mb-6">
                <p className="text-slate-400 text-sm mb-2">Move to Stage</p>
                <div className="grid grid-cols-2 gap-2">
                  {stages.map(stage => (
                    <button
                      key={stage.id}
                      onClick={() => moveDeal(selectedDeal.id, stage.id)}
                      disabled={stage.id === selectedDeal.stage}
                      className="px-3 py-2 rounded bg-slate-700 text-white text-sm hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
                    >
                      {stage.name}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={() => setSelectedDeal(null)}
                className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SalesFunnel;
