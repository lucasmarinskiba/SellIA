"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import TicketForm from "@/components/support/TicketForm";
import TicketChat from "@/components/support/TicketChat";
import FAQAccordion from "@/components/support/FAQAccordion";

interface Ticket {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  category: string;
  created_at: string;
  message_count?: number;
}

interface FAQ {
  id: string;
  question: string;
  answer: string;
}

export default function SoportePage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [ticketMessages, setTicketMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTickets = async () => {
    try {
      const res = await api.get("/support/tickets");
      setTickets(res.data.items || []);
    } catch (err) {
      // handled silently
    }
  };

  const fetchFAQs = async () => {
    try {
      const res = await api.get("/support/faq");
      setFaqs(res.data || []);
    } catch (err) {
      // handled silently
    }
  };

  const fetchTicketDetail = async (ticketId: string) => {
    try {
      const res = await api.get(`/support/tickets/${ticketId}`);
      setSelectedTicket(res.data);
      setTicketMessages(res.data.messages || []);
    } catch (err) {
      // handled silently
    }
  };

  useEffect(() => {
    Promise.all([fetchTickets(), fetchFAQs()]).finally(() => setLoading(false));
  }, []);

  const statusLabels: Record<string, string> = {
    open: "Abierto",
    in_progress: "En progreso",
    waiting_user: "Esperando usuario",
    resolved: "Resuelto",
    closed: "Cerrado",
    escalated: "Escalado",
  };

  const statusColors: Record<string, string> = {
    open: "bg-yellow-100 text-yellow-800",
    in_progress: "bg-blue-100 text-blue-800",
    waiting_user: "bg-orange-100 text-orange-800",
    resolved: "bg-green-100 text-green-800",
    closed: "bg-gray-100 text-gray-600",
    escalated: "bg-red-100 text-red-800",
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Centro de Soporte</h1>

        {loading ? (
          <div className="text-center py-12 text-gray-400">Cargando...</div>
        ) : (
          <div className="grid md:grid-cols-3 gap-6">
            {/* Left sidebar: Tickets */}
            <div className="space-y-4">
              <TicketForm onCreated={fetchTickets} />

              <div className="bg-white rounded-xl shadow-sm border p-4">
                <h3 className="font-semibold text-gray-900 mb-3">Mis tickets</h3>
                {tickets.length === 0 ? (
                  <div className="text-sm text-gray-400">No tenés tickets aún.</div>
                ) : (
                  <div className="space-y-2">
                    {tickets.map((ticket) => (
                      <button
                        key={ticket.id}
                        onClick={() => fetchTicketDetail(ticket.id)}
                        className={`w-full text-left p-3 rounded-lg border transition hover:bg-gray-50 ${
                          selectedTicket?.id === ticket.id ? "ring-2 ring-blue-500" : ""
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium truncate">{ticket.title}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[ticket.status]}`}>
                            {statusLabels[ticket.status] || ticket.status}
                          </span>
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          {new Date(ticket.created_at).toLocaleDateString("es-AR")}
                          {ticket.message_count ? ` · ${ticket.message_count} mensajes` : ""}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Center: Chat */}
            <div className="md:col-span-2 space-y-4">
              {selectedTicket ? (
                <>
                  <div className="bg-white p-4 rounded-xl shadow-sm border">
                    <div className="flex items-center justify-between">
                      <h2 className="font-semibold text-gray-900">{selectedTicket.title}</h2>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[selectedTicket.status]}`}>
                        {statusLabels[selectedTicket.status] || selectedTicket.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{selectedTicket.description}</p>
                  </div>
                  <TicketChat
                    ticketId={selectedTicket.id}
                    messages={ticketMessages}
                    status={selectedTicket.status}
                    onMessageSent={() => fetchTicketDetail(selectedTicket.id)}
                  />
                </>
              ) : (
                <div className="bg-white p-8 rounded-xl shadow-sm border text-center text-gray-400">
                  Seleccioná un ticket para ver la conversación.
                </div>
              )}

              {/* FAQ Section */}
              <div className="bg-white p-6 rounded-xl shadow-sm border">
                <h3 className="font-semibold text-gray-900 mb-4">Preguntas frecuentes</h3>
                <FAQAccordion faqs={faqs} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
