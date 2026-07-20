'use client'

/**
 * AUDIT LOGS — CORE lobe — FULL RICH REWRITE
 *
 * Filter bar, log entries with avatar chips + action badges, color coding, stats, export.
 */

import { useState, useMemo } from 'react'
import { FileSearch, Filter, Download, Bot, User, Lock, Shield } from 'lucide-react'

const T = {
  bgApp:       '#0B0F19',
  bgCard:      '#151B2B',
  bgCardHov:   '#1A2235',
  border:      '#2A3441',
  textPrim:    '#F3F4F6',
  textSub:     '#9CA3AF',
  violet:      '#a855f7',
  cyan:        '#06B6D4',
  emerald:     '#10B981',
  amber:       '#F59E0B',
  rose:        '#ef4444',
  glowViolet:  '0 0 22px rgba(168,85,247,0.50)',
  glowCyan:    '0 0 22px rgba(6,182,212,0.50)',
  glowEmerald: '0 0 22px rgba(16,185,129,0.50)',
} as const

type ActionType = 'create' | 'update' | 'delete' | 'login' | 'system' | 'warning' | 'critical'
type Actor = 'user' | 'ai' | 'system'

interface LogEntry {
  id: string
  ts: string
  actor: Actor
  actorName: string
  actionType: ActionType
  action: string
  resource: string
  ip: string
  tenant: string
}

const ACTION_COLORS: Record<ActionType, string> = {
  create:   '#10B981',
  update:   '#06B6D4',
  delete:   '#ef4444',
  login:    '#a855f7',
  system:   '#9CA3AF',
  warning:  '#F59E0B',
  critical: '#dc2626',
}

const ACTOR_COLORS: Record<Actor, string> = {
  user:   '#a855f7',
  ai:     '#10B981',
  system: '#9CA3AF',
}

const ACTOR_ICONS: Record<Actor, React.ElementType> = {
  user:   User,
  ai:     Bot,
  system: Lock,
}

const ENTRIES: LogEntry[] = [
  { id: 'a1',  ts: '17:42:03', actor: 'ai',     actorName: 'SellIA · Payment-Bot',   actionType: 'create',   action: 'STRIPE_CHARGE_SUCCESS',         resource: 'invoice/INV-2847 · $980',         ip: '10.0.4.12',      tenant: 'tenant-7'  },
  { id: 'a2',  ts: '17:41:18', actor: 'ai',     actorName: 'SellIA · Browser-Bot',   actionType: 'system',   action: 'SESSION_COMPLETED',              resource: 'session/2174 · whatsapp.web',      ip: '10.0.4.12',      tenant: 'tenant-7'  },
  { id: 'a3',  ts: '17:38:47', actor: 'user',   actorName: 'lucas@sellia.app',       actionType: 'update',   action: 'APPROVE_HIGH_VALUE_DEAL',        resource: 'deal/D-4892 · $2,400',            ip: '186.140.34.12',  tenant: 'tenant-7'  },
  { id: 'a4',  ts: '17:35:11', actor: 'system', actorName: 'AutoFailover',           actionType: 'warning',  action: 'FAILED_PAYMENT_RETRY',           resource: 'sub/SUB-184 · $49',               ip: '10.0.1.4',       tenant: 'tenant-12' },
  { id: 'a5',  ts: '17:32:54', actor: 'ai',     actorName: 'SellIA · AFIP-Bot',      actionType: 'create',   action: 'INVOICE_CAE_ISSUED',             resource: 'CAE 75412988411',                  ip: '10.0.4.12',      tenant: 'tenant-7'  },
  { id: 'a6',  ts: '17:28:09', actor: 'system', actorName: 'RateLimit',              actionType: 'warning',  action: 'API_RATE_LIMIT_EXCEEDED',        resource: 'meta-ads · 60/min',               ip: '10.0.1.7',       tenant: 'tenant-19' },
  { id: 'a7',  ts: '17:24:38', actor: 'ai',     actorName: 'SellIA · Risk-Assessor', actionType: 'critical', action: 'CHARGEBACK_DETECTED',            resource: 'tx/CH-2018 · $1,247',             ip: '10.0.4.12',      tenant: 'tenant-7'  },
  { id: 'a8',  ts: '17:18:22', actor: 'user',   actorName: 'team@empresabeta.com',   actionType: 'create',   action: 'INVITE_TEAM_MEMBER',             resource: 'role: viewer',                    ip: '201.78.144.7',   tenant: 'tenant-12' },
  { id: 'a9',  ts: '17:14:01', actor: 'system', actorName: 'TenantIsolation',        actionType: 'critical', action: 'CROSS_TENANT_QUERY_BLOCKED',     resource: 'attempted: tenant-7 ← tenant-12', ip: '10.0.1.4',       tenant: 'tenant-12' },
  { id: 'a10', ts: '17:09:47', actor: 'ai',     actorName: 'SellIA · Messenger-Bot', actionType: 'create',   action: 'WA_MESSAGE_SENT',                resource: 'phone/+54911...341',              ip: '10.0.4.12',      tenant: 'tenant-7'  },
  { id: 'a11', ts: '17:02:14', actor: 'user',   actorName: 'lucas@sellia.app',       actionType: 'update',   action: 'UPDATE_PRICING_TIER',            resource: 'starter → pro',                   ip: '186.140.34.12',  tenant: 'tenant-7'  },
  { id: 'a12', ts: '16:58:33', actor: 'system', actorName: 'BackupScheduler',        actionType: 'system',   action: 'DAILY_BACKUP_COMPLETED',         resource: 'pg+r2 · 4.2GB',                   ip: '10.0.1.1',       tenant: 'system'    },
  { id: 'a13', ts: '16:47:12', actor: 'user',   actorName: 'lucas@sellia.app',       actionType: 'login',    action: 'USER_LOGIN',                     resource: 'web · 2FA OK',                    ip: '186.140.34.12',  tenant: 'tenant-7'  },
  { id: 'a14', ts: '16:42:08', actor: 'ai',     actorName: 'SellIA · Lead-Scorer',   actionType: 'update',   action: 'LEAD_SCORE_UPDATED',             resource: 'lead/L-7841 · score 92/100',      ip: '10.0.4.12',      tenant: 'tenant-7'  },
  { id: 'a15', ts: '16:38:54', actor: 'user',   actorName: 'maria@sellia.app',       actionType: 'delete',   action: 'CONTACT_DELETED',                resource: 'contact/C-1284 · duplicado',      ip: '192.168.1.42',   tenant: 'tenant-7'  },
]

const ACTOR_LABELS: Record<Actor, string> = { user: 'Usuario', ai: 'IA', system: 'Sistema' }

export default function AuditLogs() {
  const [actorFilter, setActorFilter] = useState<Actor | 'all'>('all')
  const [actionFilter, setActionFilter] = useState<ActionType | 'all'>('all')
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    let list = ENTRIES
    if (actorFilter !== 'all') list = list.filter(e => e.actor === actorFilter)
    if (actionFilter !== 'all') list = list.filter(e => e.actionType === actionFilter)
    if (search.trim()) list = list.filter(e =>
      e.action.toLowerCase().includes(search.toLowerCase()) ||
      e.actorName.toLowerCase().includes(search.toLowerCase()) ||
      e.resource.toLowerCase().includes(search.toLowerCase()),
    )
    return list
  }, [actorFilter, actionFilter, search])

  const stats = useMemo(() => ({
    today: ENTRIES.length,
    activeUsers: [...new Set(ENTRIES.filter(e => e.actor === 'user').map(e => e.actorName))].length,
    aiActions: ENTRIES.filter(e => e.actor === 'ai').length,
    criticals: ENTRIES.filter(e => e.actionType === 'critical').length,
  }), [])

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, #a855f780, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: T.violet + '22', border: '1px solid ' + T.violet + '44', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <FileSearch style={{ width: 20, height: 20, color: T.violet }} />
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase' }}>
              Audit Logs
              <span style={{ fontSize: 11, color: T.textSub, fontWeight: 400, textTransform: 'none', marginLeft: 8, letterSpacing: 0 }}>· Compliance · debug · forense</span>
            </div>
            <div style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>{stats.today} eventos · retención 90 días</div>
          </div>
        </div>
        <button style={{ padding: '6px 14px', borderRadius: 8, fontSize: 11, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.04em', textTransform: 'uppercase', cursor: 'pointer', background: T.cyan + '18', border: '1px solid ' + T.cyan + '40', color: T.cyan, display: 'flex', alignItems: 'center', gap: 6 }}>
          <Download style={{ width: 12, height: 12 }} /> Exportar
        </button>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, padding: '12px 20px', borderBottom: '1px solid ' + T.border }}>
        {[
          { label: 'Eventos hoy',      value: stats.today,       color: T.cyan    },
          { label: 'Usuarios activos', value: stats.activeUsers, color: T.violet  },
          { label: 'Acciones IA',      value: stats.aiActions,   color: T.emerald },
          { label: 'Críticos',         value: stats.criticals,   color: T.rose    },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 10, padding: '10px 14px', textAlign: 'center' }}>
            <div style={{ fontSize: 22, fontWeight: 800, color, textShadow: '0 0 20px ' + color + '88' }}>{value}</div>
            <div style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Filter bar */}
      <div style={{ padding: '10px 16px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <Filter style={{ width: 12, height: 12, color: T.textSub }} />

        {/* Search */}
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar acción, actor, recurso…"
          style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 6, padding: '4px 10px', fontSize: 11, color: T.textPrim, fontFamily: 'JetBrains Mono,monospace', outline: 'none', width: 200 }} />

        <div style={{ width: 1, height: 16, background: T.border }} />

        {/* Actor filter */}
        {(['all', 'user', 'ai', 'system'] as const).map(a => (
          <button key={a} onClick={() => setActorFilter(a)}
            style={{ padding: '2px 10px', borderRadius: 4, fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', cursor: 'pointer', background: actorFilter === a ? (a === 'all' ? T.textPrim + '18' : ACTOR_COLORS[a as Actor] + '22') : 'transparent', border: '1px solid ' + (actorFilter === a ? (a === 'all' ? T.textPrim + '44' : ACTOR_COLORS[a as Actor] + '55') : T.border), color: actorFilter === a ? (a === 'all' ? T.textPrim : ACTOR_COLORS[a as Actor]) : T.textSub }}>
            {a === 'all' ? 'Todos' : ACTOR_LABELS[a]}
          </button>
        ))}

        <div style={{ width: 1, height: 16, background: T.border }} />

        {/* Action type filter */}
        {(['create', 'update', 'delete', 'login'] as ActionType[]).map(type => (
          <button key={type} onClick={() => setActionFilter(actionFilter === type ? 'all' : type)}
            style={{ padding: '2px 10px', borderRadius: 4, fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', cursor: 'pointer', background: actionFilter === type ? ACTION_COLORS[type] + '22' : 'transparent', border: '1px solid ' + (actionFilter === type ? ACTION_COLORS[type] + '55' : T.border), color: actionFilter === type ? ACTION_COLORS[type] : T.textSub }}>
            {type}
          </button>
        ))}
      </div>

      {/* Log list */}
      <div style={{ maxHeight: 460, overflowY: 'auto', padding: '8px 12px', display: 'flex', flexDirection: 'column', gap: 4, fontFamily: 'JetBrains Mono,monospace' }}>
        {filtered.map(e => {
          const actColor = ACTOR_COLORS[e.actor]
          const actionColor = ACTION_COLORS[e.actionType]
          const ActorIcon = ACTOR_ICONS[e.actor]
          return (
            <div key={e.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 10px', borderRadius: 8, background: T.bgApp, border: '1px solid ' + (e.actionType === 'critical' ? T.rose + '30' : T.border) }}>

              {/* Timestamp */}
              <span style={{ fontSize: 9, color: T.textSub, flexShrink: 0, width: 56 }}>{e.ts}</span>

              {/* Actor chip */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '2px 8px', borderRadius: 4, background: actColor + '18', border: '1px solid ' + actColor + '28', flexShrink: 0, minWidth: 80 }}>
                <ActorIcon style={{ width: 10, height: 10, color: actColor }} />
                <span style={{ fontSize: 9, color: actColor, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 60 }}>{e.actorName}</span>
              </div>

              {/* Action badge */}
              <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 9, fontFamily: 'monospace', background: actionColor + '18', border: '1px solid ' + actionColor + '28', color: actionColor, flexShrink: 0, width: 70, textAlign: 'center', textTransform: 'uppercase' }}>
                {e.actionType}
              </span>

              {/* Action name */}
              <span style={{ fontSize: 10, fontWeight: 700, color: T.textPrim, flexShrink: 0, width: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.action}</span>

              {/* Resource */}
              <span style={{ fontSize: 10, color: T.textSub, flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.resource}</span>

              {/* Tenant */}
              <span style={{ fontSize: 9, color: T.textSub + '88', flexShrink: 0, width: 72, textAlign: 'right' }}>{e.tenant}</span>

              {/* IP */}
              <span style={{ fontSize: 9, color: T.textSub + '66', flexShrink: 0, width: 88, textAlign: 'right' }}>{e.ip}</span>
            </div>
          )
        })}
        {filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: 32, color: T.textSub, fontSize: 12 }}>Sin resultados para ese filtro.</div>
        )}
      </div>

      {/* Footer */}
      <div style={{ borderTop: '1px solid ' + T.border, padding: '10px 20px', display: 'flex', alignItems: 'center', gap: 8 }}>
        <Shield style={{ width: 12, height: 12, color: T.violet }} />
        <span style={{ fontSize: 11, color: T.textSub }}>
          Mostrando {filtered.length} de {ENTRIES.length} eventos · retención 90 días · inmutable · GDPR compliant
        </span>
      </div>
    </section>
  )
}
