import React, { useState } from 'react';

interface WorkflowStep {
  id: string;
  type: 'trigger' | 'action' | 'condition';
  label: string;
  config: Record<string, any>;
}

interface Workflow {
  id: string;
  name: string;
  description: string;
  active: boolean;
  steps: WorkflowStep[];
  executions: number;
  successRate: number;
}

const AutomationBuilder: React.FC = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([
    {
      id: '1',
      name: 'Lead to MQL',
      description: 'Convert new leads to marketing qualified leads',
      active: true,
      steps: [
        { id: 's1', type: 'trigger', label: 'New Lead Received', config: {} },
        { id: 's2', type: 'action', label: 'Send Welcome Email', config: { template: 'welcome' } },
        { id: 's3', type: 'action', label: 'Add to Nurture Track', config: { track: 'mql' } },
      ],
      executions: 1245,
      successRate: 87,
    },
    {
      id: '2',
      name: 'Deal Stalled Alert',
      description: 'Alert when deals are stalled for 7+ days',
      active: true,
      steps: [
        { id: 's4', type: 'trigger', label: 'Deal No Activity', config: { days: 7 } },
        { id: 's5', type: 'condition', label: 'Deal Value > $50K', config: {} },
        { id: 's6', type: 'action', label: 'Notify Sales Rep', config: { channel: 'slack' } },
      ],
      executions: 456,
      successRate: 94,
    },
  ]);

  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [showBuilder, setShowBuilder] = useState(false);

  const triggerOptions = [
    '🚀 New Lead Received',
    '📅 Deal Created',
    '⏰ Time-based',
    '📧 Email Opened',
    '🔗 Link Clicked',
    '📞 Call Logged',
  ];

  const actionOptions = [
    '📧 Send Email',
    '💬 Send SMS',
    '🔔 Send Notification',
    '📞 Schedule Call',
    '➕ Add to List',
    '🏷️ Update CRM Field',
    '🤖 Assign to AI Agent',
  ];

  const conditionOptions = [
    '💰 Deal Value',
    '📊 Engagement Score',
    '👥 Company Size',
    '⏱️ Days in Stage',
    '🎯 Lead Score',
    '🌍 Location',
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Sales Automations</h1>
            <p className="text-slate-400">Create and manage automated workflows</p>
          </div>
          <button
            onClick={() => setShowBuilder(true)}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 transition"
          >
            + New Workflow
          </button>
        </div>

        {/* Workflows List */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {workflows.map(workflow => (
            <div
              key={workflow.id}
              onClick={() => setSelectedWorkflow(workflow)}
              className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-blue-500 cursor-pointer transition"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-bold text-white mb-2">{workflow.name}</h3>
                  <p className="text-slate-400 text-sm">{workflow.description}</p>
                </div>
                <div className={`px-3 py-1 rounded-full text-sm font-semibold ${workflow.active ? 'bg-green-900 text-green-200' : 'bg-gray-900 text-gray-400'}`}>
                  {workflow.active ? '🟢 Active' : '⚪ Inactive'}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-slate-700 p-3 rounded">
                  <p className="text-slate-400 text-xs mb-1">Executions</p>
                  <p className="text-xl font-bold text-white">{workflow.executions.toLocaleString()}</p>
                </div>
                <div className="bg-slate-700 p-3 rounded">
                  <p className="text-slate-400 text-xs mb-1">Success Rate</p>
                  <p className="text-xl font-bold text-green-400">{workflow.successRate}%</p>
                </div>
              </div>

              <div className="flex gap-2">
                <button className="flex-1 px-3 py-2 bg-slate-700 text-white rounded hover:bg-slate-600 transition text-sm">
                  Edit
                </button>
                <button className="flex-1 px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition text-sm">
                  View Details
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Workflow Builder Modal */}
        {showBuilder && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-slate-800 rounded-lg p-8 max-w-4xl w-full max-h-96 overflow-y-auto border border-slate-700">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-3xl font-bold text-white">Build New Workflow</h2>
                <button onClick={() => setShowBuilder(false)} className="text-slate-400 hover:text-white text-2xl">✕</button>
              </div>

              <div className="grid grid-cols-3 gap-6">
                {/* Triggers */}
                <div>
                  <h3 className="text-lg font-bold text-white mb-4">Triggers</h3>
                  <div className="space-y-2">
                    {triggerOptions.map((trigger, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-blue-900 text-blue-200 rounded-lg cursor-move hover:bg-blue-800 transition text-sm font-semibold"
                      >
                        {trigger}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Conditions */}
                <div>
                  <h3 className="text-lg font-bold text-white mb-4">Conditions</h3>
                  <div className="space-y-2">
                    {conditionOptions.map((condition, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-yellow-900 text-yellow-200 rounded-lg cursor-move hover:bg-yellow-800 transition text-sm font-semibold"
                      >
                        {condition}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div>
                  <h3 className="text-lg font-bold text-white mb-4">Actions</h3>
                  <div className="space-y-2">
                    {actionOptions.map((action, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-green-900 text-green-200 rounded-lg cursor-move hover:bg-green-800 transition text-sm font-semibold"
                      >
                        {action}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-8 flex gap-4">
                <button
                  onClick={() => setShowBuilder(false)}
                  className="flex-1 px-6 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition font-semibold"
                >
                  Cancel
                </button>
                <button className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold">
                  Create Workflow
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Workflow Detail Panel */}
        {selectedWorkflow && !showBuilder && (
          <div className="bg-slate-800 rounded-lg p-8 border border-slate-700">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-3xl font-bold text-white mb-2">{selectedWorkflow.name}</h2>
                <p className="text-slate-400">{selectedWorkflow.description}</p>
              </div>
              <button
                onClick={() => setSelectedWorkflow(null)}
                className="text-slate-400 hover:text-white text-2xl"
              >
                ✕
              </button>
            </div>

            {/* Workflow Steps */}
            <div className="mb-8">
              <h3 className="text-xl font-bold text-white mb-4">Workflow Steps</h3>
              <div className="space-y-4">
                {selectedWorkflow.steps.map((step, idx) => (
                  <div key={step.id} className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${
                      step.type === 'trigger' ? 'bg-blue-600' :
                      step.type === 'condition' ? 'bg-yellow-600' :
                      'bg-green-600'
                    }`}>
                      {idx + 1}
                    </div>
                    <div className="flex-grow bg-slate-700 p-4 rounded-lg">
                      <p className="text-white font-semibold capitalize">{step.type}</p>
                      <p className="text-slate-300">{step.label}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-slate-700 p-4 rounded-lg">
                <p className="text-slate-400 text-sm mb-1">Total Executions</p>
                <p className="text-2xl font-bold text-white">{selectedWorkflow.executions.toLocaleString()}</p>
              </div>
              <div className="bg-slate-700 p-4 rounded-lg">
                <p className="text-slate-400 text-sm mb-1">Success Rate</p>
                <p className="text-2xl font-bold text-green-400">{selectedWorkflow.successRate}%</p>
              </div>
              <div className="bg-slate-700 p-4 rounded-lg">
                <p className="text-slate-400 text-sm mb-1">Status</p>
                <p className="text-2xl font-bold text-blue-400">{selectedWorkflow.active ? 'Active' : 'Inactive'}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AutomationBuilder;
