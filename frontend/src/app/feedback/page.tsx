"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import FeedbackForm from "@/components/feedback/FeedbackForm";
import FeedbackCard from "@/components/feedback/FeedbackCard";

interface FeedbackItem {
  id: string;
  type: string;
  title: string;
  description: string;
  status: string;
  severity: string;
  votes_count: number;
  comments_count: number;
  ai_analysis?: string;
  ai_solution_proposal?: string;
  user_voted?: boolean;
  created_at: string;
}

interface RoadmapData {
  planned: any[];
  in_progress: any[];
  shipped: any[];
}

export default function FeedbackPage() {
  const [items, setItems] = useState<FeedbackItem[]>([]);
  const [roadmap, setRoadmap] = useState<RoadmapData | null>(null);
  const [filterType, setFilterType] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchFeedback = async () => {
    try {
      const params = filterType ? { type: filterType } : {};
      const res = await api.get("/feedback", { params });
      setItems(res.data.items || []);
    } catch {
      // silent
    }
  };

  const fetchRoadmap = async () => {
    try {
      const res = await api.get("/feedback/roadmap/public");
      setRoadmap(res.data);
    } catch {
      // silent
    }
  };

  useEffect(() => {
    Promise.all([fetchFeedback(), fetchRoadmap()]).finally(() => setLoading(false));
  }, [filterType]);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Feedback Hub</h1>
          <p className="text-gray-500 mt-2">
            Reportá bugs, sugerí ideas, o contanos qué te gusta. Nuestra IA analiza cada feedback y propone soluciones automáticamente.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left: Form */}
          <div>
            <FeedbackForm onCreated={fetchFeedback} />

            {/* Roadmap mini */}
            {roadmap && (
              <div className="mt-6 bg-white p-5 rounded-xl shadow-sm border">
                <h3 className="font-semibold text-gray-900 mb-3">Roadmap</h3>
                <div className="space-y-3">
                  <div>
                    <div className="text-xs font-medium text-blue-600 mb-1">📋 Planificado ({roadmap.planned.length})</div>
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-400 rounded-full" style={{ width: `${Math.min(roadmap.planned.length * 5, 100)}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="text-xs font-medium text-purple-600 mb-1">🔧 En progreso ({roadmap.in_progress.length})</div>
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-purple-400 rounded-full" style={{ width: `${Math.min(roadmap.in_progress.length * 5, 100)}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="text-xs font-medium text-green-600 mb-1">🚀 Entregado ({roadmap.shipped.length})</div>
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-green-400 rounded-full" style={{ width: `${Math.min(roadmap.shipped.length * 5, 100)}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Center: Feedback list */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center gap-2">
              {["", "bug", "idea", "complaint", "praise"].map((t) => (
                <button
                  key={t || "all"}
                  onClick={() => setFilterType(t)}
                  className={`px-3 py-1.5 rounded-full text-sm transition ${
                    filterType === t ? "bg-blue-600 text-white" : "bg-white text-gray-600 border hover:bg-gray-50"
                  }`}
                >
                  {t === "" ? "Todos" : t === "bug" ? "Bugs" : t === "idea" ? "Ideas" : t === "complaint" ? "Quejas" : "Elogios"}
                </button>
              ))}
            </div>

            {loading ? (
              <div className="text-center py-12 text-gray-400">Cargando...</div>
            ) : items.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                No hay feedback aún. ¡Sé el primero en enviar uno!
              </div>
            ) : (
              items.map((item) => (
                <FeedbackCard key={item.id} feedback={item} onVote={fetchFeedback} />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
