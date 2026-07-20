"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface FeedbackCardProps {
  feedback: {
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
  };
  onVote?: () => void;
}

const typeLabels: Record<string, string> = {
  bug: "🐛 Bug",
  idea: "💡 Idea",
  complaint: "😤 Queja",
  praise: "❤️ Elogio",
};

const statusLabels: Record<string, string> = {
  new: "Nuevo",
  under_review: "En revisión",
  planned: "Planificado",
  in_progress: "En desarrollo",
  shipped: "Entregado",
  declined: "Declinado",
};

const statusColors: Record<string, string> = {
  new: "bg-gray-100 text-gray-600",
  under_review: "bg-yellow-100 text-yellow-700",
  planned: "bg-blue-100 text-blue-700",
  in_progress: "bg-purple-100 text-purple-700",
  shipped: "bg-green-100 text-green-700",
  declined: "bg-red-100 text-red-700",
};

export default function FeedbackCard({ feedback, onVote }: FeedbackCardProps) {
  const [voted, setVoted] = useState(feedback.user_voted);
  const [votes, setVotes] = useState(feedback.votes_count);
  const [expanded, setExpanded] = useState(false);

  const handleVote = async () => {
    if (voted) return;
    try {
      await api.post(`/feedback/${feedback.id}/vote`);
      setVoted(true);
      setVotes(votes + 1);
      onVote?.();
    } catch {
      // already voted or error
    }
  };

  return (
    <div className="bg-white p-5 rounded-xl shadow-sm border hover:shadow-md transition">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium text-gray-500">{typeLabels[feedback.type]}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[feedback.status]}`}>
              {statusLabels[feedback.status] || feedback.status}
            </span>
          </div>
          <h4 className="font-semibold text-gray-900">{feedback.title}</h4>
          <p className="text-sm text-gray-600 mt-1 line-clamp-2">{feedback.description}</p>
        </div>
        <button
          onClick={handleVote}
          className={`flex flex-col items-center px-3 py-2 rounded-lg transition ${
            voted ? "bg-blue-100 text-blue-700" : "bg-gray-50 text-gray-500 hover:bg-gray-100"
          }`}
        >
          <span className="text-lg">▲</span>
          <span className="text-sm font-bold">{votes}</span>
        </button>
      </div>

      {feedback.ai_analysis && (
        <div className="mt-3 p-3 bg-purple-50 rounded-lg border border-purple-100">
          <div className="text-xs font-medium text-purple-700 mb-1">🤖 Análisis IA</div>
          <div className="text-sm text-purple-800">{feedback.ai_analysis}</div>
          {feedback.ai_solution_proposal && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-purple-600 mt-1 underline"
            >
              {expanded ? "Ocultar propuesta" : "Ver propuesta de solución"}
            </button>
          )}
          {expanded && feedback.ai_solution_proposal && (
            <div className="text-sm text-purple-800 mt-2 whitespace-pre-wrap">
              {feedback.ai_solution_proposal}
            </div>
          )}
        </div>
      )}

      <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
        <span>{feedback.comments_count} comentarios</span>
        <span>{new Date(feedback.created_at).toLocaleDateString("es-AR")}</span>
      </div>
    </div>
  );
}
