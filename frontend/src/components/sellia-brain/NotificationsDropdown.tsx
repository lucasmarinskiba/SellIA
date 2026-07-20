'use client'

/**
 * NOTIFICATIONS DROPDOWN
 *
 * Bell button with live backend feed. Polling GET /api/v1/notifications every 15s.
 * Categorizes by type: action, approval, alert, info.
 * Local-only fallback when backend offline.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Bell, BellOff, Check, ChevronRight, Activity, ShieldAlert,
  Zap, Inbox, AlertTriangle, Sparkles,
} from 'lucide-react'

const NOTIFY_BASE = '/api/v1/notifications'
const POLL_MS     = 15000
const LS_KEY      = 'sellia_notifications_seen_v1'

// ── Types ──────────────────────────────────────────────────────────────────────
type NotifKind = 'action' | 'approval' | 'alert' | 'info' | 'win'

export interface Notification {
  id:        string
  ts:        string         // ISO
  kind:      NotifKind
  title:     string
  body?:     string
  agent?:    string         // dept code (sdr/ads/pr/cs/cua)
  href?:     string         // deep link
  read?:     boolean
}

// ── Demo seed (only if backend offline) ────────────────────────────────────────
const NOW = Date.now()
const isoOff = (sec: number): string => new Date(NOW - sec * 1000).toISOString()

const SEED: Notification[] = [
  { id: 'n1', ts: isoOff(35),   kind: 'approval', title: 'Aprobación pendiente · Aumento de presupuesto',           body: 'Growth/Ads solicita escalar campaña #G-12 +30%',         agent: 'ads', href: '#sec-collab' },
  { id: 'n2', ts: isoOff(78),   kind: 'action',   title: 'Outbound enviado · 27 prospectos',                         body: 'SDR completó secuencia LinkedIn · 4 respuestas',          agent: 'sdr' },
  { id: 'n3', ts: isoOff(140),  kind: 'win',      title: 'Deal cerrado · USD 4,820',                                 body: 'Acme Corp · pipeline → Customer Success',                 agent: 'cs' },
  { id: 'n4', ts: isoOff(200),  kind: 'alert',    title: 'CAPTCHA detectado en checkout proveedor',                  body: 'CUA pausó la tarea · esperando aprobación humana',        agent: 'cua', href: '#sec-collab' },
  { id: 'n5', ts: isoOff(420),  kind: 'info',     title: 'Sentimiento de marca +0.62',                               body: 'PR detectó momentum favorable · ventana óptima de post', agent: 'pr' },
]

// ── Helpers ────────────────────────────────────────────────────────────────────
const KIND_CONFIG: Record<NotifKind, { color: string; icon: React.ElementType; label: string }> = {
  action:   { color: '#06B6D4', icon: Activity,     label: 'Acción'      },
  approval: { color: '#F59E0B', icon: ShieldAlert,  label: 'Aprobación'  },
  alert:    { color: '#EF4444', icon: AlertTriangle, label: 'Alerta'     },
  info:     { color: '#8B5CF6', icon: Sparkles,     label: 'Info'        },
  win:      { color: '#10B981', icon: Zap,          label: 'Logro'       },
}

const timeAgo = (iso: string): string => {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 60)    return `${diff}s`
  if (diff < 3600)  return `${Math.floor(diff / 60)}m`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`
  return `${Math.floor(diff / 86400)}d`
}

const loadSeen = (): Set<string> => {
  if (typeof window === 'undefined') return new Set()
  try {
    const raw = localStorage.getItem(LS_KEY)
    return new Set(raw ? (JSON.parse(raw) as string[]) : [])
  } catch { return new Set() }
}

const saveSeen = (s: Set<string>): void => {
  try { localStorage.setItem(LS_KEY, JSON.stringify([...s])) } catch { /* ignore */ }
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function NotificationsDropdown(): React.JSX.Element {
  const [open, setOpen]           = useState(false)
  const [items, setItems]         = useState<Notification[]>([])
  const [seen, setSeen]           = useState<Set<string>>(() => loadSeen())
  const [offline, setOffline]     = useState(false)
  const wrapRef                   = useRef<HTMLDivElement>(null)

  const unread = items.filter(n => !seen.has(n.id)).length

  // ── Click outside close ──
  useEffect(() => {
    if (!open) return
    const onDown = (e: globalThis.MouseEvent): void => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [open])

  // ── Fetch loop ──
  useEffect(() => {
    let alive = true
    const fetchOnce = async (): Promise<void> => {
      try {
        const r = await fetch(`${NOTIFY_BASE}?limit=50`, { cache: 'no-store' })
        if (!r.ok) throw new Error(String(r.status))
        const data = (await r.json()) as { notifications?: Notification[] }
        if (!alive) return
        setItems(data.notifications ?? [])
        setOffline(false)
      } catch {
        if (!alive) return
        // Fallback: demo seed (only first load)
        setItems(p => p.length === 0 ? SEED : p)
        setOffline(true)
      }
    }
    void fetchOnce()
    const iv = window.setInterval(() => { void fetchOnce() }, POLL_MS)
    return () => { alive = false; window.clearInterval(iv) }
  }, [])

  // ── Persist seen ──
  useEffect(() => { saveSeen(seen) }, [seen])

  const markRead = useCallback((id: string): void => {
    setSeen(s => {
      const n = new Set(s)
      n.add(id)
      return n
    })
  }, [])

  const markAllRead = useCallback((): void => {
    setSeen(new Set(items.map(n => n.id)))
  }, [items])

  // Sort: unread first, then recent
  const sorted = useMemo(() => {
    return [...items].sort((a, b) => {
      const aRead = seen.has(a.id) ? 1 : 0
      const bRead = seen.has(b.id) ? 1 : 0
      if (aRead !== bRead) return aRead - bRead
      return new Date(b.ts).getTime() - new Date(a.ts).getTime()
    })
  }, [items, seen])

  return (
    <div ref={wrapRef} style={{ position: 'relative', flexShrink: 0 }}>
      {/* Bell button */}
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        title={`${unread} notificación${unread !== 1 ? 'es' : ''} sin leer`}
        style={{
          position: 'relative',
          width: 34, height: 34, borderRadius: 9,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: open ? 'rgba(59,130,246,0.12)' : 'rgba(255,255,255,0.04)',
          border: `1px solid ${open ? 'rgba(59,130,246,0.4)' : 'rgba(255,255,255,0.08)'}`,
          cursor: 'pointer',
          color: open ? '#3B82F6' : 'rgba(255,255,255,0.55)',
          flexShrink: 0,
          transition: 'background .15s, border-color .15s, color .15s',
        }}
      >
        <Bell size={15} />
        {unread > 0 && (
          <span style={{
            position: 'absolute', top: -4, right: -4,
            minWidth: 16, height: 16, padding: '0 4px', borderRadius: 8,
            background: '#EF4444',
            color: '#FFFFFF',
            fontSize: 9, fontWeight: 700, fontFamily: 'monospace',
            display: 'grid', placeItems: 'center',
            boxShadow: '0 0 6px rgba(239,68,68,0.6)',
            animation: unread > 0 ? 'notif-pulse 1.6s ease-in-out infinite' : 'none',
          }}>
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>

      <style>{`@keyframes notif-pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.12)}}`}</style>

      {/* Dropdown */}
      {open && (
        <div style={{
          position: 'absolute', right: 0, top: 'calc(100% + 8px)',
          width: 380,
          maxHeight: 520,
          display: 'flex', flexDirection: 'column',
          background: 'rgba(8,10,18,0.98)',
          border: '1px solid rgba(255,255,255,0.14)',
          borderRadius: 14,
          overflow: 'hidden',
          zIndex: 300,
          boxShadow: '0 20px 60px rgba(0,0,0,.8)',
          backdropFilter: 'blur(20px)',
        }}>
          {/* Header */}
          <div style={{
            padding: '12px 16px',
            borderBottom: '1px solid rgba(255,255,255,0.07)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#F0F4FF' }}>
                Notificaciones
              </div>
              <div style={{
                fontSize: 10, color: 'rgba(160,180,220,0.5)', marginTop: 2,
                fontFamily: 'monospace', letterSpacing: '0.06em', textTransform: 'uppercase',
              }}>
                {unread} sin leer · {items.length} total {offline && ' · offline'}
              </div>
            </div>
            {unread > 0 && (
              <button type="button" onClick={markAllRead}
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 4,
                  padding: '5px 10px', borderRadius: 7,
                  background: 'transparent',
                  border: '1px solid rgba(255,255,255,0.1)',
                  color: 'rgba(200,210,240,0.7)',
                  fontSize: 11, fontWeight: 600,
                  cursor: 'pointer',
                }}>
                <Check size={11} /> Marcar todas
              </button>
            )}
          </div>

          {/* List */}
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {sorted.length === 0 ? (
              <div style={{
                padding: '36px 20px', textAlign: 'center',
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10,
              }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 22,
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  display: 'grid', placeItems: 'center',
                }}>
                  <Inbox size={20} color="rgba(160,180,220,0.4)" />
                </div>
                <div style={{ fontSize: 12, color: 'rgba(200,210,240,0.6)' }}>
                  Sin notificaciones nuevas
                </div>
              </div>
            ) : (
              sorted.map(n => {
                const cfg = KIND_CONFIG[n.kind]
                const Icon = cfg.icon
                const isRead = seen.has(n.id)
                return (
                  <a
                    key={n.id}
                    href={n.href ?? '#'}
                    onClick={e => {
                      if (!n.href) e.preventDefault()
                      markRead(n.id)
                    }}
                    style={{
                      display: 'flex', alignItems: 'flex-start', gap: 10,
                      padding: '12px 16px',
                      borderBottom: '1px solid rgba(255,255,255,0.05)',
                      background: isRead ? 'transparent' : 'rgba(59,130,246,0.04)',
                      cursor: 'pointer',
                      textDecoration: 'none',
                      transition: 'background .12s',
                    }}
                    onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.background = 'rgba(255,255,255,0.04)' }}
                    onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.background = isRead ? 'transparent' : 'rgba(59,130,246,0.04)' }}
                  >
                    {/* Icon */}
                    <div style={{
                      width: 30, height: 30, borderRadius: 8,
                      background: `${cfg.color}14`,
                      border: `1px solid ${cfg.color}33`,
                      display: 'grid', placeItems: 'center', flexShrink: 0,
                    }}>
                      <Icon size={13} style={{ color: cfg.color }} />
                    </div>

                    {/* Body */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{
                        display: 'flex', alignItems: 'center', gap: 7,
                        marginBottom: 2, flexWrap: 'wrap',
                      }}>
                        <span style={{
                          fontSize: 9, fontWeight: 700, fontFamily: 'monospace',
                          letterSpacing: '0.08em', textTransform: 'uppercase',
                          color: cfg.color,
                        }}>
                          {cfg.label}
                        </span>
                        {n.agent && (
                          <span style={{
                            fontSize: 9, fontFamily: 'monospace',
                            color: 'rgba(160,180,220,0.5)',
                            textTransform: 'uppercase', letterSpacing: '0.06em',
                          }}>
                            · {n.agent}
                          </span>
                        )}
                        <span style={{ marginLeft: 'auto', fontSize: 10, color: 'rgba(160,180,220,0.4)', fontFamily: 'monospace' }}>
                          {timeAgo(n.ts)}
                        </span>
                      </div>
                      <div style={{
                        fontSize: 13,
                        fontWeight: isRead ? 500 : 600,
                        color: isRead ? 'rgba(200,210,240,0.75)' : '#F0F4FF',
                        lineHeight: 1.35,
                      }}>
                        {n.title}
                      </div>
                      {n.body && (
                        <div style={{ fontSize: 11, color: 'rgba(160,180,220,0.55)', marginTop: 3, lineHeight: 1.45 }}>
                          {n.body}
                        </div>
                      )}
                    </div>

                    {!isRead && (
                      <span style={{
                        width: 6, height: 6, borderRadius: 3,
                        background: '#3B82F6', flexShrink: 0,
                        marginTop: 12,
                        boxShadow: '0 0 6px rgba(59,130,246,0.7)',
                      }} />
                    )}
                  </a>
                )
              })
            )}
          </div>

          {/* Footer */}
          <div style={{
            padding: '10px 16px',
            borderTop: '1px solid rgba(255,255,255,0.07)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            background: 'rgba(0,0,0,0.25)',
          }}>
            <span style={{
              fontSize: 10, fontFamily: 'monospace', color: 'rgba(160,180,220,0.4)',
              letterSpacing: '0.06em', textTransform: 'uppercase',
              display: 'inline-flex', alignItems: 'center', gap: 5,
            }}>
              {offline ? <BellOff size={11} /> : <Bell size={11} />}
              {offline ? 'modo local · backend offline' : 'live · polling 15s'}
            </span>
            <a href="#sec-collab" onClick={() => setOpen(false)}
              style={{
                fontSize: 11, fontWeight: 600, color: '#3B82F6',
                textDecoration: 'none',
                display: 'inline-flex', alignItems: 'center', gap: 4,
              }}>
              Ver todas <ChevronRight size={11} />
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
