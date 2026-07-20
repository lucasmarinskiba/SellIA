"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface FeedbackItem {
  id: string;
  type: string;
  title: string;
  description: string;
  status: string;
  severity: string;
  category: string;
  votes_count: number;
  ai_analysis?: string;
  ai_solution_proposal?: string;
  ai_confidence?: number;
  target_plan?: string;
  created_at: string;
}

export default function AdminFeedbackPage() {
  const [items, setItems] = useState<FeedbackItem[]>([]);
  const [filterStatus, setFilterStatus] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchItems = async () => {
    try {
      const params = filterStatus ? { status: filterStatus } : {};
      const res = await api.get("/feedback/admin/all", { params });
      setItems(res.data.items || []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (id: string, status: string) => {
    try {
      await api.patch(`/feedback/admin/${id}`, { status });
      fetchItems();
    } catch {
      // silent
    }
  };

  const forceAnalyze = async (id: string) => {
    try {
      await api.post(`/feedback/admin/${id}/ai-analyze`);
      fetchItems();
    } catch {
      // silent
    }
  };

  useEffect(() => {
    fetchItems();
  }, [filterStatus]);

  const statusOptions = ["new", "under_review", "planned", "in_progress", "shipped", "declined"];

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Admin Feedback Hub</h1>

      <div className="flex items-center gap-2">
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="">Todos los estados</option>
          {statusOptions.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button onClick={fetchItems} className="bg-gray-100 px-3 py-2 rounded-lg text-sm hover:bg-gray-200">🔄</button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Cargando...</div>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <div key={item.id} className="bg-white p-5 rounded-xl shadow-sm border">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium capitalize bg-gray-100 px-2 py-0.5 rounded">{item.type}</span>
                    <span className="text-xs text-gray-400">{item.category || "general"}</span>
                    <span className="text-xs text-gray-400">{item.severity}</span>
                  </div>
                  <h3 className="font-semibold">{item.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold">{item.votes_count} votos</div>
                  <div className="text-xs text-gray-400">{new Date(item.created_at).toLocaleDateString("es-AR")}</div>
                </div>
              </div>

              {item.ai_analysis && (
                <div className="mt-3 p-3 bg-purple-50 rounded-lg">
                  <div className="text-xs font-medium text-purple-700">🤖 IA: {item.ai_analysis}</div>
                  {item.ai_solution_proposal && (
                    <div className="text-xs text-purple-600 mt-1">💡 {item.ai_solution_proposal.substring(0, 200)}...</div>
                  )}
                  {item.ai_confidence && (
                    <div className="text-xs text-purple-500 mt-1">Confianza: {(item.ai_confidence * 100).toFixed(0)}%</div>
                  )}
                  {item.target_plan && (
                    <div className="text-xs text-purple-500 mt-1">Plan objetivo: {item.target_plan}</div>
                  )}
                </div>
              )}

              <div className="flex items-center gap-2 mt-3">
                {statusOptions.map((s) => (
                  <button
                    key={s}
                    onClick={() => updateStatus(item.id, s)}
                    className={`text-xs px-2 py-1 rounded transition ${
                      item.status === s ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    }`}
                  >
                    {s}
                  </button>
                ))}
                <button
                  onClick={() => forceAnalyze(item.id)}
                  className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded hover:bg-purple-200"
                >
                  🔬 Re-analizar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
