'use client'

/**
 * ADMIN PANEL — CORE lobe — style migration.
 * Users, roles, API keys, permisos, configuración guiada.
 */

import { useState } from 'react'
import {
  Users, Key, Shield, Plus, Copy, Trash2, Crown, UserCog,
  Eye, EyeOff, ShieldCheck, Activity
} from 'lucide-react'

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

type Role = 'owner' | 'admin' | 'manager' | 'viewer'

interface Member {
  id: string
  email: string
  name: string
  role: Role
  avatar: string
  lastActive: string
  status: 'active' | 'invited' | 'suspended'
}

interface ApiKey {
  id: string
  name: string
  prefix: string
  hint: string
  scopes: string[]
  created: string
  lastUsed: string
  env: 'live' | 'test'
}

const MEMBERS: Member[] = [
  { id: 'u1', email: 'lucas@sellia.app',    name: 'Lucas Marín',  role: 'owner',   avatar: 'LM', lastActive: 'ahora',      status: 'active'  },
  { id: 'u2', email: 'maria@sellia.app',    name: 'María López',  role: 'admin',   avatar: 'ML', lastActive: 'hace 12min', status: 'active'  },
  { id: 'u3', email: 'pedro@sellia.app',    name: 'Pedro K.',     role: 'manager', avatar: 'PK', lastActive: 'hace 2h',    status: 'active'  },
  { id: 'u4', email: 'ana@sellia.app',      name: 'Ana Suárez',   role: 'viewer',  avatar: 'AS', lastActive: 'hace 1 día', status: 'active'  },
  { id: 'u5', email: 'tom@empresabeta.com', name: 'Tomás N.',     role: 'manager', avatar: 'TN', lastActive: 'pendiente',  status: 'invited' },
]

const API_KEYS: ApiKey[] = [
  { id: 'k1', name: 'Production Web', prefix: 'sk_live', hint: 'sk_live_••••••••••a7f2', scopes: ['read:all', 'write:deals', 'write:contacts'], created: 'Hace 47 días', lastUsed: 'hace 12s',    env: 'live' },
  { id: 'k2', name: 'Mobile App',     prefix: 'sk_live', hint: 'sk_live_••••••••••3c91', scopes: ['read:all', 'write:messages'],                 created: 'Hace 23 días', lastUsed: 'hace 47s',    env: 'live' },
  { id: 'k3', name: 'CI/CD pipeline', prefix: 'sk_test', hint: 'sk_test_••••••••••b88e', scopes: ['read:all', 'write:all', 'admin:tenants'],    created: 'Hace 89 días', lastUsed: 'hace 2 días', env: 'test' },
  { id: 'k4', name: 'Zapier webhook', prefix: 'sk_live', hint: 'sk_live_••••••••••f12c', scopes: ['read:webhooks'],                             created: 'Hace 5 días',  lastUsed: 'hace 18min',  env: 'live' },
]

const ROLE_CONFIG: Record<Role, { label: string; color: string; icon: React.ElementType }> = {
  owner:   { label: 'Owner',   color: '#F59E0B', icon: Crown     },
  admin:   { label: 'Admin',   color: '#ec4899', icon: ShieldCheck },
  manager: { label: 'Manager', color: '#06B6D4', icon: UserCog   },
  viewer:  { label: 'Viewer',  color: '#9CA3AF', icon: Eye       },
}

const ROLE_PERMS: Record<Role, string[]> = {
  owner:   ['Billing', 'Delete tenant', 'All deals', 'API keys', 'Invite'],
  admin:   ['All deals', 'API keys', 'Invite', 'Settings'],
  manager: ['Edit deals', 'View team', 'View reports'],
  viewer:  ['Read-only'],
}

export default function AdminPanel() {
  const [tab, setTab] = useState<'team' | 'keys'>('team')
  const [showKey, setShowKey] = useState<string | null>(null)

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, #a855f780, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: T.violet + '22', border: '1px solid ' + T.violet + '44', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Shield style={{ width: 20, height: 20, color: T.violet, filter: 'drop-shadow(0 0 8px rgba(168,85,247,0.7))' }} />
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase' }}>
              Admin Panel
              <span style={{ fontSize: 11, color: T.textSub, fontWeight: 400, textTransform: 'none', marginLeft: 8, letterSpacing: 0 }}>· Team + API keys + tenants</span>
            </div>
            <div style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>
              <span style={{ color: T.violet, textShadow: '0 0 20px ' + T.violet + '88', fontWeight: 700 }}>{MEMBERS.length}</span>
              <span> miembros · </span>
              <span style={{ color: T.cyan, textShadow: '0 0 20px ' + T.cyan + '88', fontWeight: 700 }}>{API_KEYS.length}</span>
              <span> API keys · tenant-7</span>
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, padding: 4, borderRadius: 8, background: T.bgApp, border: '1px solid ' + T.border }}>
          {(['team', 'keys'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)}
              style={{ padding: '5px 14px', borderRadius: 6, fontSize: 11, fontWeight: 700, cursor: 'pointer', transition: 'all .15s', display: 'flex', alignItems: 'center', gap: 6, background: tab === t ? T.violet + '28' : 'transparent', border: '1px solid ' + (tab === t ? T.violet + '55' : 'transparent'), color: tab === t ? T.violet : T.textSub }}>
              {t === 'team' ? <Users style={{ width: 12, height: 12 }} /> : <Key style={{ width: 12, height: 12 }} />}
              {t === 'team' ? 'Team' : 'API Keys'}
            </button>
          ))}
        </div>
      </div>

      {/* Team tab */}
      {tab === 'team' && (
        <div style={{ padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub }}>MIEMBROS · {MEMBERS.length}</div>
            <button style={{ padding: '6px 14px', borderRadius: 8, fontSize: 11, fontWeight: 700, cursor: 'pointer', background: T.violet + '22', border: '1px solid ' + T.violet + '44', color: T.violet, display: 'flex', alignItems: 'center', gap: 6 }}>
              <Plus style={{ width: 12, height: 12 }} /> Invitar miembro
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {MEMBERS.map(m => {
              const role = ROLE_CONFIG[m.role]
              const RoleIcon = role.icon
              return (
                <div key={m.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', borderRadius: 10, background: T.bgApp, border: '1px solid ' + T.border, opacity: m.status === 'invited' ? 0.7 : 1 }}>
                  <div style={{ width: 36, height: 36, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, flexShrink: 0, background: role.color + '20', border: '1px solid ' + role.color + '40', color: role.color }}>
                    {m.avatar}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim }}>{m.name}</div>
                      {m.status === 'invited' && (
                        <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 9, fontFamily: 'monospace', background: T.amber + '18', border: '1px solid ' + T.amber + '28', color: T.amber }}>PENDIENTE</span>
                      )}
                    </div>
                    <div style={{ fontSize: 11, color: T.textSub }}>{m.email}</div>
                  </div>
                  <div style={{ fontSize: 10, color: T.textSub, flexShrink: 0 }}>{m.lastActive}</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '4px 10px', borderRadius: 6, flexShrink: 0, background: role.color + '15', border: '1px solid ' + role.color + '30' }}>
                    <RoleIcon style={{ width: 12, height: 12, color: role.color }} />
                    <span style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', color: role.color }}>{role.label}</span>
                  </div>
                  <button style={{ padding: 6, borderRadius: 6, background: 'transparent', border: 'none', cursor: 'pointer', color: T.textSub }}>
                    <Trash2 style={{ width: 12, height: 12 }} />
                  </button>
                </div>
              )
            })}
          </div>

          {/* Role matrix */}
          <div style={{ marginTop: 14, background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 10, padding: 14 }}>
            <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginBottom: 10 }}>PERMISOS POR ROL</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
              {(['owner', 'admin', 'manager', 'viewer'] as Role[]).map(r => {
                const cfg = ROLE_CONFIG[r]
                const Icon = cfg.icon
                return (
                  <div key={r} style={{ borderRadius: 8, padding: 10, background: cfg.color + '10', border: '1px solid ' + cfg.color + '30' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                      <Icon style={{ width: 12, height: 12, color: cfg.color }} />
                      <span style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.04em', color: cfg.color }}>{cfg.label}</span>
                    </div>
                    {ROLE_PERMS[r].map((p, i) => (
                      <div key={i} style={{ fontSize: 10, color: T.textSub, marginBottom: 1 }}>· {p}</div>
                    ))}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* API Keys tab */}
      {tab === 'keys' && (
        <div style={{ padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub }}>API KEYS · {API_KEYS.length}</div>
            <button style={{ padding: '6px 14px', borderRadius: 8, fontSize: 11, fontWeight: 700, cursor: 'pointer', background: T.violet + '22', border: '1px solid ' + T.violet + '44', color: T.violet, display: 'flex', alignItems: 'center', gap: 6 }}>
              <Plus style={{ width: 12, height: 12 }} /> Crear API key
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {API_KEYS.map(k => {
              const isLive = k.env === 'live'
              const envColor = isLive ? T.emerald : T.amber
              return (
                <div key={k.id} style={{ background: envColor + '06', border: '1px solid ' + envColor + '25', borderRadius: 10, padding: 14 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Key style={{ width: 14, height: 14, color: envColor }} />
                      <span style={{ fontSize: 13, fontWeight: 700, color: T.textPrim }}>{k.name}</span>
                      <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 9, fontFamily: 'monospace', background: envColor + '20', border: '1px solid ' + envColor + '35', color: envColor }}>{k.env}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <button onClick={() => setShowKey(showKey === k.id ? null : k.id)} style={{ padding: 6, borderRadius: 6, background: 'transparent', border: 'none', cursor: 'pointer', color: T.textSub }}>
                        {showKey === k.id ? <EyeOff style={{ width: 13, height: 13 }} /> : <Eye style={{ width: 13, height: 13 }} />}
                      </button>
                      <button style={{ padding: 6, borderRadius: 6, background: 'transparent', border: 'none', cursor: 'pointer', color: T.textSub }}><Copy style={{ width: 13, height: 13 }} /></button>
                      <button style={{ padding: 6, borderRadius: 6, background: 'transparent', border: 'none', cursor: 'pointer', color: T.textSub }}><Trash2 style={{ width: 13, height: 13 }} /></button>
                    </div>
                  </div>
                  <code style={{ display: 'block', padding: '7px 12px', borderRadius: 6, background: T.bgApp, fontSize: 11, fontFamily: 'JetBrains Mono,monospace', color: T.textPrim, marginBottom: 8 }}>
                    {showKey === k.id ? `${k.prefix}_a8f47e2c91b3d6f...` : k.hint}
                  </code>
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
                    {k.scopes.map(s => (
                      <span key={s} style={{ padding: '2px 8px', borderRadius: 4, fontSize: 9, fontFamily: 'JetBrains Mono,monospace', background: T.border, color: T.textSub, border: '1px solid ' + T.border }}>{s}</span>
                    ))}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: T.textSub }}>
                    <span>Created: {k.created}</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <Activity style={{ width: 10, height: 10 }} /> last used: {k.lastUsed}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </section>
  )
}
