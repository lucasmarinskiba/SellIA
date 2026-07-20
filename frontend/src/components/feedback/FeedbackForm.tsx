"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface FeedbackFormProps {
  onCreated?: () => void;
}

export default function FeedbackForm({ onCreated }: FeedbackFormProps) {
  const [type, setType] = useState("idea");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState("medium");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const types = [
    { value: "bug", label: "🐛 Reportar un bug", color: "bg-red-100 text-red-800" },
    { value: "idea", label: "💡 Sugerir una idea", color: "bg-blue-100 text-blue-800" },
    { value: "complaint", label: "😤 Queja", color: "bg-orange-100 text-orange-800" },
    { value: "praise", label: "❤️ Elogio", color: "bg-green-100 text-green-800" },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/feedback", { type, title, description, severity });
      setSuccess(true);
      setTitle("");
      setDescription("");
      onCreated?.();
      setTimeout(() => setSuccess(false), 3000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-sm border space-y-4">
      <h3 className="text-lg font-semibold">Compartí tu experiencia</h3>

      {success && (
        <div className="bg-green-50 text-green-700 px-4 py-2 rounded-lg text-sm">
          ✅ ¡Gracias! Tu feedback fue enviado. El equipo de IA ya lo está analizando.
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {types.map((t) => (
          <button
            key={t.value}
            type="button"
            onClick={() => setType(t.value)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition ${
              type === t.value ? t.color + " ring-2 ring-offset-1" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        required
        placeholder="Título breve"
        className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
      />

      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        required
        rows={4}
        placeholder="Describí tu experiencia con detalle..."
        className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
      />

      {type === "bug" && (
        <select
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
          className="w-full border rounded-lg px-3 py-2"
        >
          <option value="low">Bajo - Molestia menor</option>
          <option value="medium">Medio - Afecta el uso</option>
          <option value="high">Alto - Dificulta el trabajo</option>
          <option value="critical">Crítico - Bloquea completamente</option>
        </select>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "Enviando..." : "Enviar feedback"}
      </button>
    </form>
  );
}
