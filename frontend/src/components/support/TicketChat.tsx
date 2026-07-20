"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface Message {
  id: string;
  sender_type: "user" | "agent" | "ai" | "system";
  content: string;
  created_at: string;
}

interface TicketChatProps {
  ticketId: string;
  messages: Message[];
  status: string;
  onMessageSent: () => void;
}

export default function TicketChat({ ticketId, messages, status, onMessageSent }: TicketChatProps) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;
    setLoading(true);
    try {
      await api.post(`/support/tickets/${ticketId}/messages`, { content });
      setContent("");
      onMessageSent();
    } catch (err) {
      // handled silently
    } finally {
      setLoading(false);
    }
  };

  const senderLabels: Record<string, string> = {
    user: "Vos",
    agent: "Soporte",
    ai: "Asistente IA",
    system: "Sistema",
  };

  const senderColors: Record<string, string> = {
    user: "bg-blue-100 text-blue-800",
    agent: "bg-green-100 text-green-800",
    ai: "bg-purple-100 text-purple-800",
    system: "bg-gray-100 text-gray-600",
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-xl shadow-sm border">
      <div className="flex-1 overflow-y-auto p-4 space-y-3 max-h-[400px]">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 text-sm py-8">
            Escribe tu primer mensaje para iniciar la conversación.
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className="flex flex-col">
            <div className="flex items-center gap-2 mb-1">
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${senderColors[msg.sender_type]}`}>
                {senderLabels[msg.sender_type] || msg.sender_type}
              </span>
              <span className="text-xs text-gray-400">
                {new Date(msg.created_at).toLocaleString("es-AR")}
              </span>
            </div>
            <div className="text-sm text-gray-800 whitespace-pre-wrap">{msg.content}</div>
          </div>
        ))}
      </div>

      {status !== "resolved" && status !== "closed" && (
        <form onSubmit={handleSubmit} className="p-3 border-t flex gap-2">
          <input
            type="text"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Escribí tu mensaje..."
            className="flex-1 border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={loading || !content.trim()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "..." : "Enviar"}
          </button>
        </form>
      )}

      {status === "resolved" && (
        <div className="p-3 border-t bg-green-50 text-green-700 text-sm text-center">
          ✅ Este ticket fue resuelto. ¿Necesitás más ayuda? <a href="/soporte" className="underline">Creá uno nuevo</a>.
        </div>
      )}
    </div>
  );
}
