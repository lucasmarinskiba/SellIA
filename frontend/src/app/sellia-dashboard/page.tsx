'use client'

/**
 * Real dashboard · wired to backend via TanStack Query.
 * Replaces mock data in legacy /dashboard for new-auth-flow users.
 */
import { useState } from 'react'

import {
  QueryProvider,
  SellIAAuthProvider,
  useDeals,
  useSellIAAuth,
  useSellIAWebSocket,
  useTenantSubdomain,
  useCreateDeal,
  useUpdateDeal,
  useDeleteDeal,
  useLogout,
} from '@/lib/sellia-api'

function DashboardInner() {
  const { user, isAuthenticated, isLoading } = useSellIAAuth()
  const { tenant, subdomain } = useTenantSubdomain()
  const { data: deals, isLoading: dealsLoading, error: dealsError } = useDeals()
  const { status: wsStatus, lastEvent } = useSellIAWebSocket({ enabled: isAuthenticated })
  const updateDeal = useUpdateDeal()
  const deleteDeal = useDeleteDeal()
  const logout = useLogout()
  const [filter, setFilter] = useState<string>('all')

  if (isLoading) {
    return <div className="min-h-screen bg-[#060812] flex items-center justify-center text-white/50">Cargando…</div>
  }

  if (!isAuthenticated) {
    if (typeof window !== 'undefined') window.location.href = '/sellia-login'
    return null
  }

  const filteredDeals = filter === 'all' ? deals : deals?.filter((d) => d.stage === filter)
  const totalValue = deals?.reduce((s, d) => s + d.value_cents, 0) || 0
  const won = deals?.filter((d) => d.stage === 'won').length || 0

  return (
    <div className="min-h-screen bg-[#060812] p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-black">
            <span className="bg-gradient-to-r from-cyan-400 to-pink-400 bg-clip-text text-transparent uppercase tracking-widest">SellIA Dashboard</span>
          </h1>
          <p className="text-[11px] text-white/40 mt-1">
            {tenant?.name || 'Loading tenant…'}
            {subdomain && <span className="text-cyan-400 font-mono"> · {subdomain}.sellia.app</span>}
            <span className="ml-2 text-white/30">· {user?.role}</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border" style={{
            background: wsStatus === 'open' ? 'rgba(34,197,94,0.10)' : 'rgba(239,68,68,0.10)',
            borderColor: wsStatus === 'open' ? 'rgba(34,197,94,0.30)' : 'rgba(239,68,68,0.30)',
          }}>
            <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: wsStatus === 'open' ? '#22c55e' : '#ef4444' }} />
            <span className="text-[10px] font-mono uppercase tracking-widest" style={{ color: wsStatus === 'open' ? '#22c55e' : '#ef4444' }}>WS · {wsStatus}</span>
          </div>
          <button onClick={logout} className="text-[11px] px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white/70 hover:bg-white/10">
            Logout
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <Stat label="Total deals"   value={deals?.length ?? '—'} color="#06b6d4" />
        <Stat label="Won"           value={won} color="#22c55e" />
        <Stat label="Pipeline value" value={`$${(totalValue / 100).toLocaleString()}`} color="#fbbf24" />
        <Stat label="Plan"          value={tenant?.plan || '—'} color="#a855f7" />
      </div>

      {/* Last brain event */}
      {lastEvent && (
        <div className="max-w-7xl mx-auto mb-4 rounded-xl border border-purple-500/30 bg-purple-500/[0.06] p-3">
          <p className="text-[10px] uppercase tracking-widest font-bold text-purple-300 mb-1">⚡ Live brain event</p>
          <pre className="text-[10px] font-mono text-white/70 overflow-x-auto">{JSON.stringify(lastEvent, null, 2)}</pre>
        </div>
      )}

      {/* Deals */}
      <div className="max-w-7xl mx-auto rounded-2xl border border-white/[0.08] bg-[#0a0e1a]/80 p-5">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">Deals</h2>
          <div className="flex items-center gap-1.5">
            {(['all', 'prospect', 'qualified', 'negotiation', 'won', 'lost'] as const).map((s) => (
              <button key={s} onClick={() => setFilter(s)} className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase border ${
                filter === s ? 'bg-white/10 border-white/20 text-white' : 'bg-white/[0.02] border-white/[0.06] text-white/40'
              }`}>{s}</button>
            ))}
          </div>
        </div>

        {dealsLoading && <p className="text-white/40 text-sm">Loading deals…</p>}
        {dealsError && <p className="text-red-400 text-sm">Error: {String(dealsError)}</p>}

        {filteredDeals && filteredDeals.length === 0 && (
          <p className="text-white/30 text-sm text-center py-8">No deals · empty pipeline</p>
        )}

        <div className="space-y-1.5">
          {filteredDeals?.map((d) => (
            <div key={d.id} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 flex items-center gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold text-white">{d.title}</p>
                <p className="text-[10px] text-white/40 font-mono">{d.id.slice(0, 8)}… · prob {d.probability}%</p>
              </div>
              <span className="text-[9px] px-2 py-0.5 rounded font-mono uppercase font-bold" style={{
                background: d.stage === 'won' ? 'rgba(34,197,94,0.20)' : d.stage === 'lost' ? 'rgba(239,68,68,0.20)' : 'rgba(59,130,246,0.20)',
                color: d.stage === 'won' ? '#22c55e' : d.stage === 'lost' ? '#ef4444' : '#3b82f6',
              }}>{d.stage}</span>
              <p className="text-sm font-black tabular-nums text-emerald-400 w-24 text-right">
                ${(d.value_cents / 100).toLocaleString()} <span className="text-[9px] text-white/40">{d.currency}</span>
              </p>
              <button onClick={() => updateDeal.mutate({ id: d.id, stage: d.stage === 'won' ? 'qualified' : 'won' })}
                className="text-[10px] px-2 py-1 rounded bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/25">
                {d.stage === 'won' ? 'Reopen' : 'Mark won'}
              </button>
              <button onClick={() => { if (confirm('Delete?')) deleteDeal.mutate(d.id) }}
                className="text-[10px] px-2 py-1 rounded bg-red-500/15 border border-red-500/30 text-red-300 hover:bg-red-500/25">
                Del
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Stat({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-[#0a0e1a]/80 p-3">
      <p className="text-[9px] uppercase tracking-widest text-white/40 font-bold">{label}</p>
      <p className="text-xl font-black tabular-nums" style={{ color }}>{value}</p>
    </div>
  )
}

export default function SellIADashboardPage() {
  return (
    <QueryProvider>
      <SellIAAuthProvider>
        <DashboardInner />
      </SellIAAuthProvider>
    </QueryProvider>
  )
}
