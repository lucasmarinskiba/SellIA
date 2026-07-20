"use client";

interface SupportStats {
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets: number;
  resolved_today: number;
  avg_resolution_hours?: number;
  ai_resolution_rate?: number;
  csat_avg?: number;
}

interface SupportMetricsProps {
  stats: SupportStats;
}

export default function SupportMetrics({ stats }: SupportMetricsProps) {
  const cards = [
    { label: "Total tickets", value: stats.total_tickets, color: "bg-gray-100 text-gray-800" },
    { label: "Abiertos", value: stats.open_tickets, color: "bg-yellow-100 text-yellow-800" },
    { label: "En progreso", value: stats.in_progress_tickets, color: "bg-blue-100 text-blue-800" },
    { label: "Resueltos hoy", value: stats.resolved_today, color: "bg-green-100 text-green-800" },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {cards.map((card) => (
          <div key={card.label} className={`p-4 rounded-xl ${card.color}`}>
            <div className="text-2xl font-bold">{card.value}</div>
            <div className="text-xs opacity-80">{card.label}</div>
          </div>
        ))}
      </div>

      {(stats.avg_resolution_hours !== undefined || stats.csat_avg !== undefined) && (
        <div className="grid grid-cols-2 gap-4">
          {stats.avg_resolution_hours !== undefined && (
            <div className="bg-white p-4 rounded-xl border">
              <div className="text-sm text-gray-500">Tiempo medio de resolución</div>
              <div className="text-xl font-semibold">{stats.avg_resolution_hours.toFixed(1)}h</div>
            </div>
          )}
          {stats.csat_avg !== undefined && (
            <div className="bg-white p-4 rounded-xl border">
              <div className="text-sm text-gray-500">Satisfacción (CSAT)</div>
              <div className="text-xl font-semibold">{stats.csat_avg.toFixed(1)} / 5</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
