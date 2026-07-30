/**
 * Custom Hooks for SellIA API
 * React Query / SWR wrappers para backend FastAPI
 */

import { useState, useEffect } from "react";
import { analyticsAPI, leadsAPI, workflowsAPI, progressionAPI, queueAPI } from "@/lib/sellia-api";

// ============================================================
// LEADS HOOKS
// ============================================================
export const useLeads = (filters?: { status?: string; score_min?: number }) => {
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await leadsAPI.list(filters);
        setLeads(data || []);
        setError(null);
      } catch (err) {
        setError((err as Error).message);
        setLeads([]);
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, [filters?.status, filters?.score_min]);

  return { leads, loading, error };
};

export const useLead = (id: number) => {
  const [lead, setLead] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await leadsAPI.get(id);
        setLead(data);
        setError(null);
      } catch (err) {
        setError((err as Error).message);
        setLead(null);
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, [id]);

  return { lead, loading, error };
};

// ============================================================
// ANALYTICS HOOKS
// ============================================================
export const useAnalyticsFunnel = () => {
  const [funnel, setFunnel] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await analyticsAPI.funnel();
        setFunnel(data?.data || null);
        setError(null);
      } catch (err) {
        setError((err as Error).message);
        setFunnel(null);
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, []);

  return { funnel, loading, error };
};

export const useAnalyticsEmail = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await analyticsAPI.emailMetrics();
        setMetrics(data?.data || null);
        setError(null);
      } catch (err) {
        setError((err as Error).message);
        setMetrics(null);
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, []);

  return { metrics, loading, error };
};

export const useAnalyticsLeadSources = () => {
  const [sources, setSources] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await analyticsAPI.leadSources();
        setSources(data?.data || null);
        setError(null);
      } catch (err) {
        setError((err as Error).message);
        setSources(null);
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, []);

  return { sources, loading, error };
};

export const useAnalyticsLeadHealth = () => {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await analyticsAPI.leadHealth();
        setHealth(data?.data || null);
        setError(null);
      } catch (err) {
        setError((err as Error).message);
        setHealth(null);
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, []);

  return { health, loading, error };
};

export const useAnalyticsSummary = () => {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await analyticsAPI.summary();
        setSummary(data?.data || null);
        setError(null);
      } catch (err) {
        setError((err as Error).message);
        setSummary(null);
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, []);

  return { summary, loading, error };
};

// ============================================================
// WORKFLOWS HOOKS
// ============================================================
export const useWorkflows = (status?: string) => {
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await workflowsAPI.list(status);
        setWorkflows(data || []);
        setError(null);
      } catch (err) {
        setError((err as Error).message);
        setWorkflows([]);
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, [status]);

  return { workflows, loading, error };
};

// ============================================================
// QUEUE HOOKS
// ============================================================
export const useQueueStats = (pollInterval: number = 5000) => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const data = await queueAPI.stats();
        setStats(data?.queue || null);
        setError(null);
      } catch (err) {
        setError((err as Error).message);
        setStats(null);
      } finally {
        setLoading(false);
      }
    };

    fetch();
    const interval = setInterval(fetch, pollInterval);

    return () => clearInterval(interval);
  }, [pollInterval]);

  return { stats, loading, error };
};

// ============================================================
// PROGRESSION HOOKS
// ============================================================
export const useLeadProgression = (leadId: number) => {
  const [executions, setExecutions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await progressionAPI.getExecutions(leadId);
        setExecutions(data?.executions || []);
        setError(null);
      } catch (err) {
        setError((err as Error).message);
        setExecutions([]);
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, [leadId]);

  return { executions, loading, error };
};
