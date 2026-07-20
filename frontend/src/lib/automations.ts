import { api } from './api'

export interface Workflow {
  id: string
  business_id: string
  name: string
  description: string | null
  trigger_type: string
  trigger_config: Record<string, any>
  actions: Record<string, any>[]
  visual_data: Record<string, any> | null
  status: string
  execution_count: number
  conversion_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface EmailTemplate {
  id: string
  business_id: string
  name: string
  subject: string
  body_html: string | null
  body_text: string
  variables: string[]
  category: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SequenceStep {
  id: string
  sequence_id: string
  step_order: number
  delay_hours: number
  delay_minutes: number
  template_id: string | null
  subject_override: string | null
  body_override: string | null
  condition: string | null
  is_active: boolean
  created_at: string
}

export interface EmailSequence {
  id: string
  business_id: string
  name: string
  description: string | null
  category: string | null
  status: string
  trigger_type: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  steps: SequenceStep[]
}

export interface WorkflowVariant {
  id: string
  workflow_id: string
  business_id: string
  variant_name: string
  traffic_split: number
  actions: Record<string, any>[]
  execution_count: number
  conversion_count: number
  is_control: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ABTestResult {
  workflow_id: string
  workflow_name: string
  total_executions: number
  variants: {
    id: string
    variant_name: string
    is_control: boolean
    traffic_split: number
    execution_count: number
    conversion_count: number
    conversion_rate: number
    traffic_share: number
    is_active: boolean
  }[]
  winner: string | null
  recommendation: string
}

export interface ChatbotRule {
  id: string
  business_id: string
  name: string
  intent: string
  keywords: string[]
  response_template: string
  response_type: string
  priority: number
  channel_filter: string[]
  requires_human: boolean
  usage_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export const automationsApi = {
  // Workflows
  getWorkflows: (businessId: string) =>
    api.get<Workflow[]>('/automations/workflows', { params: { business_id: businessId } }).then(r => r.data),

  createWorkflow: (data: Omit<Workflow, 'id' | 'created_at' | 'updated_at' | 'execution_count' | 'conversion_count'>) =>
    api.post<Workflow>('/automations/workflows', data).then(r => r.data),

  updateWorkflow: (id: string, data: Partial<Workflow>) =>
    api.patch<Workflow>(`/automations/workflows/${id}`, data).then(r => r.data),

  deleteWorkflow: (id: string) =>
    api.delete(`/automations/workflows/${id}`).then(r => r.data),

  // Email Templates
  getEmailTemplates: (businessId: string) =>
    api.get<EmailTemplate[]>('/automations/email-templates', { params: { business_id: businessId } }).then(r => r.data),

  createEmailTemplate: (data: Omit<EmailTemplate, 'id' | 'created_at' | 'updated_at'>) =>
    api.post<EmailTemplate>('/automations/email-templates', data).then(r => r.data),

  updateEmailTemplate: (id: string, data: Partial<EmailTemplate>) =>
    api.patch<EmailTemplate>(`/automations/email-templates/${id}`, data).then(r => r.data),

  deleteEmailTemplate: (id: string) =>
    api.delete(`/automations/email-templates/${id}`).then(r => r.data),

  // Email Sequences
  getEmailSequences: (businessId: string) =>
    api.get<EmailSequence[]>('/automations/email-sequences', { params: { business_id: businessId } }).then(r => r.data),

  createEmailSequence: (data: Omit<EmailSequence, 'id' | 'created_at' | 'updated_at'>) =>
    api.post<EmailSequence>('/automations/email-sequences', data).then(r => r.data),

  updateEmailSequence: (id: string, data: Partial<EmailSequence>) =>
    api.patch<EmailSequence>(`/automations/email-sequences/${id}`, data).then(r => r.data),

  deleteEmailSequence: (id: string) =>
    api.delete(`/automations/email-sequences/${id}`).then(r => r.data),

  // Chatbot Rules
  getChatbotRules: (businessId: string) =>
    api.get<ChatbotRule[]>('/automations/chatbot-rules', { params: { business_id: businessId } }).then(r => r.data),

  createChatbotRule: (data: Omit<ChatbotRule, 'id' | 'created_at' | 'updated_at' | 'usage_count'>) =>
    api.post<ChatbotRule>('/automations/chatbot-rules', data).then(r => r.data),

  updateChatbotRule: (id: string, data: Partial<ChatbotRule>) =>
    api.patch<ChatbotRule>(`/automations/chatbot-rules/${id}`, data).then(r => r.data),

  deleteChatbotRule: (id: string) =>
    api.delete(`/automations/chatbot-rules/${id}`).then(r => r.data),

  // Workflow Variants (A/B Testing)
  getVariants: (workflowId: string) =>
    api.get<WorkflowVariant[]>(`/automations/workflows/${workflowId}/variants`).then(r => r.data),

  createVariant: (workflowId: string, data: Omit<WorkflowVariant, 'id' | 'workflow_id' | 'business_id' | 'execution_count' | 'conversion_count' | 'created_at' | 'updated_at'>) =>
    api.post<WorkflowVariant>(`/automations/workflows/${workflowId}/variants`, data).then(r => r.data),

  updateVariant: (workflowId: string, variantId: string, data: Partial<WorkflowVariant>) =>
    api.patch<WorkflowVariant>(`/automations/workflows/${workflowId}/variants/${variantId}`, data).then(r => r.data),

  deleteVariant: (workflowId: string, variantId: string) =>
    api.delete(`/automations/workflows/${workflowId}/variants/${variantId}`).then(r => r.data),

  getABTestResults: (workflowId: string) =>
    api.get<ABTestResult>(`/automations/workflows/${workflowId}/ab-test-results`).then(r => r.data),

  // Seed pre-built automations
  seedAutomations: (businessId: string) =>
    api.post('/automations/seed', null, { params: { business_id: businessId } }).then(r => r.data),
}
