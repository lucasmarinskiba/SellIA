"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import SupportMetrics from "@/components/support/SupportMetrics";
import TicketChat from "@/components/support/TicketChat";

interface Ticket {
  id: string;
  user_id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  category: string;
  assigned_to?: string;
  ai_suggested_answer?: string;
  ai_confidence?: number;
  created_at: string;
  message_count?: number;
}

interface SupportStats {
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets: number;
  resolved_today: number;
  avg_resolution_hours?: number;
  ai_resolution_rate?: number;
  csat_avg?: number;
}

export default function AdminSoportePage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [stats, setStats] = useState<SupportStats | null>(null);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [ticketMessages, setTicketMessages] = useState<any[]>([]);
  const [replyContent, setReplyContent] = useState("");
  const [isInternal, setIsInternal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState("");

  const fetchTickets = async () => {
    try {
      const params = filterStatus ? { status: filterStatus } : {};
      const res = await api.get("/support/admin/tickets", { params });
      setTickets(res.data.items || []);
    } catch (err) {
      // handled silently
    }
  };

  const fetchStats = async () => {
    try {
      const res = await api.get("/support/admin/stats");
      setStats(res.data);
    } catch (err) {
      // handled silently
    }
  };

  const fetchTicketDetail = async (ticketId: string) => {
    try {
      const res = await api.get(`/support/admin/tickets/${ticketId}`);
      setSelectedTicket(res.data);
      setTicketMessages(res.data.messages || []);
    } catch (err) {
      // handled silently
    }
  };

  const handleAssign = async (ticketId: string) => {
    try {
      await api.patch(`/support/admin/tickets/${ticketId}`, { status: "in_progress" });
      fetchTickets();
      if (selectedTicket?.id === ticketId) fetchTicketDetail(ticketId);
    } catch (err) {
      // handled silently
    }
  };

  const handleResolve = async (ticketId: string) => {
    try {
      await api.patch(`/support/admin/tickets/${ticketId}`, { status: "resolved" });
      fetchTickets();
      if (selectedTicket?.id === ticketId) fetchTicketDetail(ticketId);
    } catch (err) {
      // handled silently
    }
  };

  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicket || !replyContent.trim()) return;
    try {
      await api.post(`/support/admin/tickets/${selectedTicket.id}/messages`, {
        content: replyContent,
        is_internal: isInternal,
      });
      setReplyContent("");
      setIsInternal(false);
      fetchTicketDetail(selectedTicket.id);
      fetchTickets();
    } catch (err) {
      // handled silently
    }
  };

  useEffect(() => {
    Promise.all([fetchTickets(), fetchStats()]).finally(() => setLoading(false));
  }, [filterStatus]);

  const statusLabels: Record<string, string> = {
    open: "Abierto",
    in_progress: "En progreso",
    waiting_user: "Esperando usuario",
    resolved: "Resuelto",
    closed: "Cerrado",
    escalated: "Escalado",
  };

  const priorityLabels: Record<string, string> = {
    low: "Baja",
    medium: "Media",
    high: "Alta",
    critical: "Crítica",
  };

  const priorityColors: Record<string, string> = {
    low: "bg-gray-100 text-gray-600",
    medium: "bg-yellow-100 text-yellow-800",
    high: "bg-orange-100 text-orange-800",
    critical: "bg-red-100 text-red-800",
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Panel de Soporte</h1>

      {stats && <SupportMetrics stats={stats} />}

      {loading ? (
        <div className="text-center py-12 text-gray-400">Cargando...</div>
      ) : (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Ticket list */}
          <div className="lg:col-span-1 space-y-4">
            <div className="flex items-center gap-2">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="border rounded-lg px-3 py-2 text-sm"
              >
                <option value="">Todos los estados</option>
                <option value="open">Abiertos</option>
                <option value="in_progress">En progreso</option>
                <option value="escalated">Escalados</option>
                <option value="resolved">Resueltos</option>
              </select>
              <button
                onClick={() => { fetchTickets(); fetchStats(); }}
                className="bg-gray-100 text-gray-700 px-3 py-2 rounded-lg text-sm hover:bg-gray-200"
              >
                🔄
              </button>
            </div>

            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {tickets.map((ticket) => (
                <button
                  key={ticket.id}
                  onClick={() => fetchTicketDetail(ticket.id)}
                  className={`w-full text-left p-3 rounded-lg border transition hover:bg-gray-50 ${
                    selectedTicket?.id === ticket.id ? "ring-2 ring-blue-500" : ""
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium truncate">{ticket.title}</span>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${priorityColors[ticket.priority]}`}>
                      {priorityLabels[ticket.priority]}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                      {statusLabels[ticket.status] || ticket.status}
                    </span>
                    <span className="text-xs text-gray-400">
                      {new Date(ticket.created_at).toLocaleDateString("es-AR")}
                    </span>
                  </div>
                  {ticket.ai_confidence && (
                    <div className="text-xs text-purple-600 mt-1">
                      🤖 AI confianza: {(ticket.ai_confidence * 100).toFixed(0)}%
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Ticket detail */}
          <div className="lg:col-span-2 space-y-4">
            {selectedTicket ? (
              <>
                <div className="bg-white p-4 rounded-xl shadow-sm border">
                  <div className="flex items-center justify-between">
                    <h2 className="font-semibold text-gray-900">{selectedTicket.title}</h2>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${priorityColors[selectedTicket.priority]}`}>
                        {priorityLabels[selectedTicket.priority]}
                      </span>
                      {selectedTicket.status !== "resolved" && (
                        <>
                          <button
                            onClick={() => handleAssign(selectedTicket.id)}
                            className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded hover:bg-blue-200"
                          >
                            Asignarme
                          </button>
                          <button
                            onClick={() => handleResolve(selectedTicket.id)}
                            className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded hover:bg-green-200"
                          >
                            Resolver
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mt-2">{selectedTicket.description}</p>
                  {selectedTicket.ai_suggested_answer && (
                    <div className="mt-3 p-3 bg-purple-50 rounded-lg border border-purple-100">
                      <div className="text-xs font-medium text-purple-700 mb-1">🤖 Sugerencia IA</div>
                      <div className="text-sm text-purple-800">{selectedTicket.ai_suggested_answer}</div>
                    </div>
                  )}
                </div>

                <TicketChat
                  ticketId={selectedTicket.id}
                  messages={ticketMessages}
                  status={selectedTicket.status}
                  onMessageSent={() => fetchTicketDetail(selectedTicket.id)}
                />

                {/* Admin reply form */}
                {selectedTicket.status !== "resolved" && (
                  <form onSubmit={handleReply} className="bg-white p-4 rounded-xl shadow-sm border space-y-3">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="internal"
                        checked={isInternal}
                        onChange={(e) => setIsInternal(e.target.checked)}
                        className="rounded"
                      />
                      <label htmlFor="internal" className="text-sm text-gray-600">
                        Nota interna (no visible para el usuario)
                      </label>
                    </div>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={replyContent}
                        onChange={(e) => setReplyContent(e.target.value)}
                        placeholder="Responder al ticket..."
                        className="flex-1 border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                      />
                      <button
                        type="submit"
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700"
                      >
                        Responder
                      </button>
                    </div>
                  </form>
                )}
              </>
            ) : (
              <div className="bg-white p-12 rounded-xl shadow-sm border text-center text-gray-400">
                Seleccioná un ticket para ver el detalle.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
