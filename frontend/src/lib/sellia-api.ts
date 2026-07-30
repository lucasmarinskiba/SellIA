/**
 * SellIA API Client
 * Conecta frontend Next.js con backend FastAPI
 * Endpoints: leads, workflows, analytics, webhooks
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ============================================================
// TIPOS
// ============================================================
export interface Lead {
  id: number;
  name: string;
  email: string;
  company?: string;
  job_title?: string;
  industry?: string;
  score: number;
  status: "new" | "contacted" | "engaged" | "qualified" | "won" | "bounced" | "unsubscribed" | "lost";
  source?: string;
  last_contacted?: string;
  created_at: string;
  updated_at: string;
}

export interface Workflow {
  id: number;
  name: string;
  description?: string;
  status: "draft" | "active" | "paused" | "completed";
  active_leads: number;
  created_at: string;
  updated_at: string;
}

export interface Analytics {
  funnel?: Record<string, number>;
  email_metrics?: {
    total_sent: number;
    delivered: number;
    opened: number;
    clicked: number;
    bounced: number;
    delivery_rate: number;
    open_rate: number;
    click_rate: number;
    bounce_rate: number;
  };
  lead_sources?: Record<string, any>;
  lead_health?: {
    hot: { count: number; leads: any[] };
    warm: { count: number; leads: any[] };
    cold: { count: number; leads: any[] };
    dead: { count: number; leads: any[] };
  };
}

// ============================================================
// LEADS API
// ============================================================
export const leadsAPI = {
  // List leads
  async list(filters?: { status?: string; score_min?: number }) {
    const params = new URLSearchParams();
    if (filters?.status) params.append("status", filters.status);
    if (filters?.score_min) params.append("score_min", filters.score_min.toString());

    const res = await fetch(`${API_BASE_URL}/api/v1/leads?${params}`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to list leads: ${res.status}`);
    return res.json();
  },

  // Create lead
  async create(data: Partial<Lead>) {
    const res = await fetch(`${API_BASE_URL}/api/v1/leads`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`Failed to create lead: ${res.status}`);
    return res.json();
  },

  // Get lead
  async get(id: number) {
    const res = await fetch(`${API_BASE_URL}/api/v1/leads/${id}`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to get lead: ${res.status}`);
    return res.json();
  },

  // Update lead
  async update(id: number, data: Partial<Lead>) {
    const res = await fetch(`${API_BASE_URL}/api/v1/leads/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`Failed to update lead: ${res.status}`);
    return res.json();
  },

  // Get stats
  async stats() {
    const res = await fetch(`${API_BASE_URL}/api/v1/leads/stats/summary`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to get stats: ${res.status}`);
    return res.json();
  },
};

// ============================================================
// WORKFLOWS API
// ============================================================
export const workflowsAPI = {
  // List workflows
  async list(status?: string) {
    const params = new URLSearchParams();
    if (status) params.append("status", status);

    const res = await fetch(`${API_BASE_URL}/api/v1/workflows?${params}`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to list workflows: ${res.status}`);
    return res.json();
  },

  // Get workflow
  async get(id: number) {
    const res = await fetch(`${API_BASE_URL}/api/v1/workflows/${id}`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to get workflow: ${res.status}`);
    return res.json();
  },

  // Activate workflow
  async activate(id: number) {
    const res = await fetch(`${API_BASE_URL}/api/v1/workflows/${id}/activate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to activate workflow: ${res.status}`);
    return res.json();
  },

  // Enroll lead
  async enrollLead(workflowId: number, leadId: number) {
    const res = await fetch(`${API_BASE_URL}/api/v1/workflows/${workflowId}/enroll-lead`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lead_id: leadId }),
    });
    if (!res.ok) throw new Error(`Failed to enroll lead: ${res.status}`);
    return res.json();
  },

  // List executions
  async listExecutions(filters?: { workflow_id?: number; lead_id?: number; status?: string }) {
    const params = new URLSearchParams();
    if (filters?.workflow_id) params.append("workflow_id", filters.workflow_id.toString());
    if (filters?.lead_id) params.append("lead_id", filters.lead_id.toString());
    if (filters?.status) params.append("status", filters.status);

    const res = await fetch(`${API_BASE_URL}/api/v1/workflows/executions/list?${params}`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to list executions: ${res.status}`);
    return res.json();
  },
};

// ============================================================
// ANALYTICS API
// ============================================================
export const analyticsAPI = {
  // Get funnel
  async funnel() {
    const res = await fetch(`${API_BASE_URL}/api/v1/analytics/funnel`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to get funnel: ${res.status}`);
    return res.json();
  },

  // Get email metrics
  async emailMetrics() {
    const res = await fetch(`${API_BASE_URL}/api/v1/analytics/email-metrics`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to get email metrics: ${res.status}`);
    return res.json();
  },

  // Get lead sources
  async leadSources() {
    const res = await fetch(`${API_BASE_URL}/api/v1/analytics/lead-sources`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to get lead sources: ${res.status}`);
    return res.json();
  },

  // Get lead health
  async leadHealth() {
    const res = await fetch(`${API_BASE_URL}/api/v1/analytics/lead-health`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to get lead health: ${res.status}`);
    return res.json();
  },

  // Get complete summary
  async summary() {
    const res = await fetch(`${API_BASE_URL}/api/v1/analytics/summary`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to get summary: ${res.status}`);
    return res.json();
  },
};

// ============================================================
// QUEUE API
// ============================================================
export const queueAPI = {
  // Get queue stats
  async stats() {
    const res = await fetch(`${API_BASE_URL}/api/v1/queue/stats`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to get queue stats: ${res.status}`);
    return res.json();
  },

  // Peek queue
  async peek(count: number = 5) {
    const res = await fetch(`${API_BASE_URL}/api/v1/queue/peek?count=${count}`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to peek queue: ${res.status}`);
    return res.json();
  },
};

// ============================================================
// PROGRESSION API
// ============================================================
export const progressionAPI = {
  // Get lead workflow executions
  async getExecutions(leadId: number) {
    const res = await fetch(`${API_BASE_URL}/api/v1/progression/${leadId}/workflow-executions`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to get executions: ${res.status}`);
    return res.json();
  },

  // Check no-engagement
  async checkNoEngagement(leadId: number, daysThreshold: number = 7) {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/progression/${leadId}/no-engagement-check?days_threshold=${daysThreshold}`,
      {
        headers: { "Content-Type": "application/json" },
      }
    );
    if (!res.ok) throw new Error(`Failed to check no-engagement: ${res.status}`);
    return res.json();
  },

  // Get lead health
  async getHealth() {
    const res = await fetch(`${API_BASE_URL}/api/v1/analytics/lead-health`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`Failed to get health: ${res.status}`);
    return res.json();
  },
};

export default {
  leadsAPI,
  workflowsAPI,
  analyticsAPI,
  queueAPI,
  progressionAPI,
};
