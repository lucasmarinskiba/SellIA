import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Play, Pause, MoreVertical, ChevronDown } from 'lucide-react';

const WorkflowBuilder: React.FC<{ businessId: string }> = ({ businessId }) => {
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingWorkflow, setEditingWorkflow] = useState<any>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    trigger_type: 'order.created',
    conditions: [],
    actions: [],
  });

  useEffect(() => {
    fetchWorkflows();
  }, [businessId]);

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      const res = await fetch(
        `/api/v1/businesses/${businessId}/workflows?active_only=false`
      );
      const data = await res.json();
      setWorkflows(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch workflows:', error);
      setLoading(false);
    }
  };

  const triggerTypes = [
    { value: 'order.created', label: 'Order Created' },
    { value: 'order.paid', label: 'Order Paid' },
    { value: 'customer.created', label: 'Customer Created' },
    { value: 'customer.added_to_segment', label: 'Customer Added to Segment' },
    { value: 'churn_risk.detected', label: 'Churn Risk Detected' },
    { value: 'email.opened', label: 'Email Opened' },
    { value: 'custom.webhook', label: 'Custom Webhook' },
  ];

  const actionTypes = [
    { value: 'send_email', label: 'Send Email' },
    { value: 'send_sms', label: 'Send SMS' },
    { value: 'send_whatsapp', label: 'Send WhatsApp' },
    { value: 'add_to_segment', label: 'Add to Segment' },
    { value: 'remove_from_segment', label: 'Remove from Segment' },
    { value: 'create_task', label: 'Create Task' },
    { value: 'add_tag', label: 'Add Tag' },
    { value: 'create_deal', label: 'Create Deal' },
  ];

  const handleCreateWorkflow = async () => {
    try {
      const payload = {
        name: formData.name,
        description: formData.description,
        trigger_type: formData.trigger_type,
        trigger_config: {},
        conditions: formData.conditions.length > 0 ? formData.conditions : null,
        actions: formData.actions.length > 0 ? formData.actions : null,
      };

      const res = await fetch(
        `/api/v1/businesses/${businessId}/workflows`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        }
      );

      if (!res.ok) throw new Error('Failed to create workflow');

      setShowModal(false);
      setFormData({
        name: '',
        description: '',
        trigger_type: 'order.created',
        conditions: [],
        actions: [],
      });
      fetchWorkflows();
    } catch (error) {
      console.error('Error creating workflow:', error);
    }
  };

  const handleActivateWorkflow = async (workflowId: string) => {
    try {
      const res = await fetch(
        `/api/v1/workflows/${workflowId}/activate`,
        { method: 'POST' }
      );
      if (res.ok) fetchWorkflows();
    } catch (error) {
      console.error('Error activating workflow:', error);
    }
  };

  const handlePauseWorkflow = async (workflowId: string) => {
    try {
      const res = await fetch(
        `/api/v1/workflows/${workflowId}/pause`,
        { method: 'POST' }
      );
      if (res.ok) fetchWorkflows();
    } catch (error) {
      console.error('Error pausing workflow:', error);
    }
  };

  const handleAddAction = () => {
    setFormData({
      ...formData,
      actions: [...formData.actions, { action_type: 'send_email', action_config: {} }],
    });
  };

  const handleRemoveAction = (index: number) => {
    setFormData({
      ...formData,
      actions: formData.actions.filter((_, i) => i !== index),
    });
  };

  if (loading) {
    return (
      <div className="w-full flex items-center justify-center p-8">
        <div className="text-gray-500">Loading workflows...</div>
      </div>
    );
  }

  return (
    <div className="w-full space-y-6 p-6 bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Workflow Automation</h1>
          <p className="text-gray-600 mt-1">Build triggered automations for your business</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Create Workflow
        </button>
      </div>

      {/* Workflows List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {workflows.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <p>No workflows created yet. Create your first workflow to get started.</p>
          </div>
        ) : (
          <div className="divide-y">
            {workflows.map((workflow) => (
              <div key={workflow.workflow_id} className="p-6 hover:bg-gray-50 transition">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {workflow.name}
                      </h3>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          workflow.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {workflow.is_active ? 'Active' : 'Paused'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      Trigger: {workflow.trigger_type}
                    </p>
                    <p className="text-xs text-gray-500 mt-2">
                      Executions: {workflow.total_executions} • Last run:{' '}
                      {workflow.last_executed ? new Date(workflow.last_executed).toLocaleDateString() : 'Never'}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    {workflow.is_active ? (
                      <button
                        onClick={() => handlePauseWorkflow(workflow.workflow_id)}
                        className="p-2 text-gray-600 hover:bg-red-100 hover:text-red-600 rounded-lg transition"
                        title="Pause workflow"
                      >
                        <Pause className="w-5 h-5" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleActivateWorkflow(workflow.workflow_id)}
                        className="p-2 text-gray-600 hover:bg-green-100 hover:text-green-600 rounded-lg transition"
                        title="Activate workflow"
                      >
                        <Play className="w-5 h-5" />
                      </button>
                    )}
                    <button className="p-2 text-gray-600 hover:bg-gray-200 rounded-lg transition">
                      <MoreVertical className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Workflow Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-96 overflow-y-auto">
            <div className="p-6 border-b border-gray-200 sticky top-0 bg-white">
              <h2 className="text-2xl font-bold text-gray-900">Create Workflow</h2>
            </div>

            <div className="p-6 space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Workflow Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Welcome Email Sequence"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Describe what this workflow does"
                  rows={2}
                />
              </div>

              {/* Trigger Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Trigger Event
                </label>
                <select
                  value={formData.trigger_type}
                  onChange={(e) =>
                    setFormData({ ...formData, trigger_type: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {triggerTypes.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Actions */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm font-medium text-gray-700">
                    Actions
                  </label>
                  <button
                    onClick={handleAddAction}
                    className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                  >
                    <Plus className="w-4 h-4" />
                    Add Action
                  </button>
                </div>
                <div className="space-y-2">
                  {formData.actions.map((action, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <select
                        value={action.action_type}
                        onChange={(e) => {
                          const updatedActions = [...formData.actions];
                          updatedActions[idx].action_type = e.target.value;
                          setFormData({ ...formData, actions: updatedActions });
                        }}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        {actionTypes.map((a) => (
                          <option key={a.value} value={a.value}>
                            {a.label}
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={() => handleRemoveAction(idx)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  {formData.actions.length === 0 && (
                    <p className="text-sm text-gray-500">No actions configured yet.</p>
                  )}
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end gap-3 sticky bottom-0 bg-white">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateWorkflow}
                disabled={!formData.name}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Create Workflow
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowBuilder;
