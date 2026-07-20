"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface TicketFormProps {
  onCreated?: () => void;
}

export default function TicketForm({ onCreated }: TicketFormProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("other");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const categories = [
    { value: "account", label: "Cuenta y acceso" },
    { value: "billing", label: "Facturación y pagos" },
    { value: "technical", label: "Problemas técnicos" },
    { value: "sales", label: "Ventas y productos" },
    { value: "security", label: "Seguridad" },
    { value: "feature_request", label: "Sugerencia de función" },
    { value: "other", label: "Otro" },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.post("/support/tickets", {
        title,
        description,
        category,
      });
      setSuccess(true);
      setTitle("");
      setDescription("");
      setCategory("other");
      onCreated?.();
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Error al crear el ticket");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 bg-white p-6 rounded-xl shadow-sm border">
      <h3 className="text-lg font-semibold text-gray-900">Crear ticket de soporte</h3>

      {success && (
        <div className="bg-green-50 text-green-700 px-4 py-2 rounded-lg text-sm">
          ✅ Ticket creado correctamente. Te responderemos pronto.
        </div>
      )}
      {error && (
        <div className="bg-red-50 text-red-700 px-4 py-2 rounded-lg text-sm">
          {error}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Categoría</label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
        >
          {categories.map((c) => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Título</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          maxLength={255}
          placeholder="Resumen breve del problema"
          className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          rows={4}
          placeholder="Describe tu problema con el mayor detalle posible..."
          className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "Creando..." : "Enviar ticket"}
      </button>
    </form>
  );
}
