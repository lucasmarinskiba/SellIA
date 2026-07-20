'use client'

/**
 * MISSION CONTROL BAR · Unified OS Bar 2026
 *
 * Single 56px bar — replaces MCB + TopBar.
 * Layout: [Logo] [Real command input + inline dropdown] [lat] [tok] [Computer Use▾] [VOZ] [User▾] [🔔]
 *
 * Features:
 *   · Real input: typing shows inline suggestions, Enter jumps to tool
 *   · Computer Use dropdown absorbs old CUA button
 *   · User auth: localStorage accounts (create / login / logout / delete)
 *   · Real latency via /api/ping (measured every 30s)
 *   · Honest status: lat/tok only shown when non-null
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Search, Mic, MicOff,
  MonitorOff, MonitorPlay, MonitorPause, MonitorCheck,
  ChevronDown, ArrowRight, Bell,
  LogIn, LogOut, Trash2, UserPlus, User, Eye, EyeOff,
} from 'lucide-react'
import { TOOLS, fuzzyMatch, type LobeId, type Tool } from './toolIndex'
import NotificationsDropdown from './NotificationsDropdown'
import SettingsDropdown from './SettingsDropdown'
import { useVoiceWake } from './useVoiceWake'


/* ─── types ─── */
export interface UserProfile {
  id: string
  name: string
  email: string
  createdAt: string
}

export type CuaMode = 'off' | 'auto' | 'supervised'

interface MissionControlBarProps {
  onJump: (componentId: string, lobe?: LobeId) => void
  handsFree: boolean
  onHandsFreeToggle: () => void
  onLaunchCUA: () => void
  cuaMode: CuaMode
  onCuaMode: (m: CuaMode) => void
  activeTasks: number
  isRunning: boolean
  user: UserProfile | null
  onLogin: (u: UserProfile) => void
  onLogout: () => void
}


/* ─── auth localStorage ─── */
const USER_KEY     = 'sellia_user_v1'
const ACCOUNTS_KEY = 'sellia_accounts_v1'

interface StoredAccount {
  id: string; name: string; email: string; passHash: string; createdAt: string
}

const simpleHash = (s: string): string => {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (Math.imul(31, h) + s.charCodeAt(i)) | 0
  return String(h >>> 0)
}

export const loadUser = (): UserProfile | null => {
  try { const s = localStorage.getItem(USER_KEY); return s ? (JSON.parse(s) as UserProfile) : null }
  catch { return null }
}
export const saveUser = (u: UserProfile): void => {
  try { localStorage.setItem(USER_KEY, JSON.stringify(u)) } catch { /* ignore */ }
}
export const clearUser = (): void => {
  try { localStorage.removeItem(USER_KEY) } catch { /* ignore */ }
}

const loadAccounts = (): StoredAccount[] => {
  try { return JSON.parse(localStorage.getItem(ACCOUNTS_KEY) ?? '[]') as StoredAccount[] }
  catch { return [] }
}
const saveAccounts = (a: StoredAccount[]): void => {
  try { localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(a)) } catch { /* ignore */ }
}


/* ─── CUA options ─── */
const CUA_OPTIONS: { id: CuaMode; label: string; desc: string; color: string; icon: React.ReactNode }[] = [
  { id: 'off',        label: 'Desactivado',       desc: 'Sin automatización',      color: '#F87171', icon: <MonitorOff  size={14}/> },
  { id: 'auto',       label: 'Piloto Automático',  desc: 'Opera sin supervisión',   color: '#10B981', icon: <MonitorPlay size={14}/> },
  { id: 'supervised', label: 'Supervisado',        desc: 'Aprobás cada acción',     color: '#F59E0B', icon: <MonitorPause size={14}/> },
]

const ACCENT = '#d3ff3a'
const DARK   = '#08090c'


/* ══════════════════════════════════════════════════════
   COMMAND ENGINE
══════════════════════════════════════════════════════ */

type Intent = 'abrir' | 'mostrar' | 'activar' | 'analizar' | 'crear' | 'configurar' | 'detener'

interface CommandResult {
  id: string
  label: string
  sublabel: string
  icon: string
  intent: Intent
  componentId: string
  lobe: LobeId
}

const INTENT_COLOR: Record<Intent, string> = {
  abrir:      '#00D4FF',
  mostrar:    '#8B5CF6',
  activar:    '#10B981',
  analizar:   '#F59E0B',
  crear:      ACCENT,
  configurar: '#F97316',
  detener:    '#F87171',
}

const INTENT_LABEL: Record<Intent, string> = {
  abrir:      'ABRIR',
  mostrar:    'MOSTRAR',
  activar:    'ACTIVAR',
  analizar:   'ANALIZAR',
  crear:      'CREAR',
  configurar: 'CONFIG',
  detener:    'DETENER',
}

const INTENT_SUB: Record<Intent, string> = {
  abrir:      'SellIA abre este módulo para vos',
  mostrar:    'SellIA muestra este panel ahora',
  activar:    'SellIA activa este proceso',
  analizar:   'SellIA te lleva a métricas y reportes',
  crear:      'SellIA abre el flujo de creación',
  configurar: 'SellIA abre la configuración',
  detener:    'SellIA detiene este proceso',
}

interface ToolTarget { componentId: string; lobe: LobeId; icon: string; label: string }

const KEYWORD_MAP: [RegExp, ToolTarget][] = [
  [/carrito|recovery|recuperar|abandon/i,                         { componentId:'lobe-retain-recovery',   lobe:'retain',  icon:'🧪', label:'Recovery Lab'             }],
  [/mrr|ingreso|revenue|ganancia|dinero/i,                        { componentId:'lobe-retain-analytics',  lobe:'retain',  icon:'📊', label:'Analytics & Reportes'      }],
  [/anuncio|publicidad|pauta|roas|ads\b/i,                        { componentId:'lobe-acquire-ads',       lobe:'acquire', icon:'🎯', label:'Ads Cockpit'               }],
  [/lead|prospecto|captaci[oó]n/i,                                { componentId:'lobe-acquire-ads',       lobe:'acquire', icon:'🎯', label:'Ads Cockpit'               }],
  [/pipeline|deal|negociaci[oó]n|atascad/i,                       { componentId:'lobe-convert-doctor',    lobe:'convert', icon:'🩺', label:'Deal Doctor'               }],
  [/factura|cotiz|quote|presupuest/i,                             { componentId:'lobe-convert-invoice',   lobe:'convert', icon:'🧾', label:'Cotizaciones & Facturas'   }],
  [/agenda|demo|reuni[oó]n|cita|calendar/i,                       { componentId:'lobe-convert-calendar',  lobe:'convert', icon:'📅', label:'Agenda & Reuniones'        }],
  [/inventario|stock|reposici[oó]n/i,                             { componentId:'lobe-retain-inventory',  lobe:'retain',  icon:'📦', label:'Inventario'                }],
  [/cliente|crm|360|perfil de/i,                                  { componentId:'lobe-retain-360',        lobe:'retain',  icon:'🌐', label:'Customer 360'              }],
  [/email|newsletter|drip|mailing/i,                              { componentId:'lobe-retain-email',      lobe:'retain',  icon:'✉️', label:'Email Marketing'           }],
  [/fideliz|loyalty|nps|recompra|postventa/i,                     { componentId:'lobe-retain-fidel',      lobe:'retain',  icon:'💎', label:'Fidelización & Lealtad'    }],
  [/review|rese[ñn]a|reputaci[oó]n|rating|star/i,                 { componentId:'lobe-retain-reputation', lobe:'retain',  icon:'⭐', label:'Reputación & Reseñas'      }],
  [/mercado libre|marketplace|shopify|amazon|tienda nube/i,        { componentId:'lobe-acquire-marketplace',lobe:'acquire',icon:'🏬', label:'Marketplace Center'        }],
  [/landing|formulario|form\b|p[aá]gina.*captura|captura.*lead/i, { componentId:'lobe-acquire-forms',     lobe:'acquire', icon:'📝', label:'Páginas & Formularios'     }],
  [/whatsapp|instagram|telegram|canal|omni/i,                     { componentId:'lobe-acquire-omni',      lobe:'acquire', icon:'📡', label:'Canales Digitales'         }],
  [/analytic|kpi|reporte|dashboard|embudo|funnel|p&l|cohort/i,    { componentId:'lobe-retain-analytics',  lobe:'retain',  icon:'📊', label:'Analytics & Reportes'      }],
  [/growth|viral|referido|org[aá]nico|waitlist/i,                 { componentId:'lobe-acquire-growth',    lobe:'acquire', icon:'🚀', label:'Growth Engine'             }],
  [/champion|aliado|b2b|enterprise|interno/i,                     { componentId:'lobe-convert-champion',  lobe:'convert', icon:'🛡️', label:'Champion Builder'          }],
  [/garant[íi]a|conversi[oó]n.*cierre|cierre.*venta|objecion/i,   { componentId:'lobe-convert-guarantee', lobe:'convert', icon:'🏆', label:'Garantía de Conversión'    }],
  [/piloto|flujo|workflow|automatiz|computer use|navegador/i,      { componentId:'lobe-convert-sala',      lobe:'convert', icon:'🎬', label:'Sala Ejecutiva'            }],
  [/arca|afip|fiscal|monotributo|cae/i,                           { componentId:'lobe-retain-arca',       lobe:'retain',  icon:'🇦🇷', label:'ARCA Compliance'          }],
  [/impuesto|aduana|iva|export|sat|dian/i,                        { componentId:'lobe-retain-tax',        lobe:'retain',  icon:'🧮', label:'Impuestos & Aduana'        }],
  [/rol|permiso|usuario|admin|equipo|rbac/i,                      { componentId:'lobe-core-config',       lobe:'core',    icon:'⚙️', label:'Panel de Control'          }],
  [/voz|voice|narrac|tts|hola sellia/i,                           { componentId:'lobe-core-voz',          lobe:'core',    icon:'🗣️', label:'Asistente de Voz'         }],
  [/env[íi]o|shipping|log[íi]stica|carrier|zona/i,                { componentId:'lobe-acquire-reach',     lobe:'acquire', icon:'🛰️', label:'Cobertura & Envíos'        }],
  [/industria|vertical|nicho|sector|preset/i,                     { componentId:'lobe-acquire-verticals', lobe:'acquire', icon:'🏛️', label:'Mi Industria'              }],
  [/conocimiento|kb|training|doc[s]?\b|pdf/i,                     { componentId:'lobe-acquire-kb',        lobe:'acquire', icon:'📚', label:'Base de Conocimiento'      }],
  [/pedido|orden|tracking|entrega/i,                              { componentId:'lobe-retain-orders',     lobe:'retain',  icon:'📦', label:'Ciclo de Pedidos'          }],
  [/plan\b|precio.*tier|tier.*precio|suscripci[oó]n|paywall/i,    { componentId:'lobe-core-pricing',      lobe:'core',    icon:'💳', label:'Planes & Facturación'      }],
  [/audit|historial.*accion|log\b|trazab/i,                       { componentId:'lobe-core-audit',        lobe:'core',    icon:'📜', label:'Historial & Auditoría'     }],
]

const INTENT_PATTERNS: [RegExp, Intent][] = [
  [/^(mostrar|muéstrame|quiero ver|ver|dame|show)\b/i,           'mostrar'   ],
  [/^(activar|activ[a]|encend[eé]|poner en marcha|enable)\b/i,  'activar'   ],
  [/^(abrir|abre|ir a|navegar|navigate|go to|open)\b/i,         'abrir'     ],
  [/^(analizar|analiz[a]|análisis|reportar|report)\b/i,         'analizar'  ],
  [/^(crear|crea|nuevo|nueva|generar|new|build|armar)\b/i,      'crear'     ],
  [/^(configurar|configur[a]|ajustar|setup|ajust[a])\b/i,       'configurar'],
  [/^(detener|parar|apagar|stop|desactivar)\b/i,                'detener'   ],
]

const SLASH_INTENTS: Record<string, Intent> = {
  '/show':     'mostrar',
  '/open':     'abrir',
  '/activate': 'activar',
  '/report':   'analizar',
  '/config':   'configurar',
  '/create':   'crear',
  '/stop':     'detener',
}

const parseIntent = (q: string): { intent: Intent; stripped: string } | null => {
  const t = q.trim()
  for (const [slash, intent] of Object.entries(SLASH_INTENTS)) {
    if (t.startsWith(slash + ' ') || t === slash) {
      return { intent, stripped: t.slice(slash.length).trim() }
    }
  }
  for (const [rx, intent] of INTENT_PATTERNS) {
    const m = t.match(rx)
    if (m) return { intent, stripped: t.slice(m[0].length).trim() }
  }
  return null
}

const buildCommandResults = (q: string, intent: Intent, stripped: string): CommandResult[] => {
  const target = stripped || q
  const out: CommandResult[] = []
  for (const [rx, t] of KEYWORD_MAP) {
    if (rx.test(target)) {
      out.push({
        id: `cmd-${t.componentId}-${intent}`,
        label: t.label,
        sublabel: INTENT_SUB[intent],
        icon: t.icon,
        intent,
        componentId: t.componentId,
        lobe: t.lobe,
      })
      if (out.length >= 4) break
    }
  }
  return out
}

const PLACEHOLDER_EXAMPLES = [
  'Decile a SellIA qué hacer…',
  '"mostrar dashboard de ventas"',
  '"activar recuperación de carritos"',
  '"abrir Ads Cockpit"',
  '"analizar mi pipeline de ventas"',
  '"crear campaña en Instagram"',
  '"mostrar MRR de hoy"',
  '"configurar roles del equipo"',
  '"activar bot de WhatsApp"',
  '"mostrar leads de esta semana"',
  '/show analytics',
  '/activate recovery',
  '/open pipeline',
]

const CMD_HISTORY_KEY = 'sellia_cmd_history_v1'
const loadCmdHistory = (): string[] => {
  try { return JSON.parse(localStorage.getItem(CMD_HISTORY_KEY) ?? '[]') as string[] }
  catch { return [] }
}
const pushCmdHistory = (cmd: string): void => {
  if (!cmd.trim()) return
  try {
    const h = loadCmdHistory().filter(x => x !== cmd)
    h.unshift(cmd)
    localStorage.setItem(CMD_HISTORY_KEY, JSON.stringify(h.slice(0, 20)))
  } catch { /* ignore */ }
}

const QUICK_COMMANDS: { label: string; query: string }[] = [
  { label: 'Ver métricas',      query: 'mostrar analytics' },
  { label: 'Recuperar carritos',query: 'activar recovery' },
  { label: 'Abrir pipeline',    query: 'abrir deal doctor' },
  { label: 'Ads Cockpit',       query: 'abrir ads cockpit' },
  { label: 'Email marketing',   query: 'activar email' },
  { label: 'Inventario',        query: 'mostrar inventario' },
]


/* ══════════════════════════════════════════════════════
   AUTH MODAL
══════════════════════════════════════════════════════ */
const AuthModal = ({
  onClose, onAuth,
}: { onClose: () => void; onAuth: (u: UserProfile) => void }): React.JSX.Element => {
  const [tab,   setTab]   = useState<'login' | 'register'>('login')
  const [name,  setName]  = useState('')
  const [email, setEmail] = useState('')
  const [pass,  setPass]  = useState('')
  const [show,  setShow]  = useState(false)
  const [err,   setErr]   = useState('')
  const [loading, setLoading] = useState(false)

  const handleRegister = (): void => {
    setErr('')
    if (!name.trim())           { setErr('Ingresá tu nombre'); return }
    if (!email.includes('@'))   { setErr('Email inválido'); return }
    if (pass.length < 6)        { setErr('Contraseña: mínimo 6 caracteres'); return }
    const accounts = loadAccounts()
    if (accounts.find(a => a.email === email.toLowerCase())) {
      setErr('Ya existe una cuenta con ese email'); return
    }
    setLoading(true)
    const u: UserProfile = {
      id: `usr_${Date.now()}`,
      name: name.trim(),
      email: email.toLowerCase(),
      createdAt: new Date().toISOString(),
    }
    accounts.push({ ...u, passHash: simpleHash(pass) })
    saveAccounts(accounts)
    saveUser(u)
    setTimeout(() => { setLoading(false); onAuth(u); onClose() }, 400)
  }

  const handleLogin = (): void => {
    setErr('')
    if (!email || !pass) { setErr('Completá todos los campos'); return }
    const accounts = loadAccounts()
    const acc = accounts.find(a => a.email === email.toLowerCase() && a.passHash === simpleHash(pass))
    if (!acc) { setErr('Email o contraseña incorrectos'); return }
    setLoading(true)
    const u: UserProfile = { id: acc.id, name: acc.name, email: acc.email, createdAt: acc.createdAt }
    saveUser(u)
    setTimeout(() => { setLoading(false); onAuth(u); onClose() }, 400)
  }

  const inp: React.CSSProperties = {
    width: '100%', padding: '11px 14px', borderRadius: 10, fontSize: 14, color: '#fff',
    background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
    outline: 'none', boxSizing: 'border-box', fontFamily: 'inherit',
  }

  return (
    <div
      style={{ position: 'fixed', inset: 0, zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(4,6,12,0.9)', backdropFilter: 'blur(10px)' }}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div style={{ width: '100%', maxWidth: 400, background: '#0e1c35', border: '1px solid rgba(255,255,255,0.14)', borderRadius: 20, overflow: 'hidden', boxShadow: '0 40px 100px rgba(0,0,0,.8)' }}>

        {/* tabs */}
        <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          {(['login', 'register'] as const).map(t => (
            <button key={t} type="button" onClick={() => { setTab(t); setErr('') }}
              style={{ flex: 1, padding: '16px', fontSize: 13, fontWeight: 700, cursor: 'pointer', border: 'none', background: 'transparent', color: tab === t ? ACCENT : 'rgba(255,255,255,0.45)', borderBottom: tab === t ? `2px solid ${ACCENT}` : '2px solid transparent', transition: 'color .15s', fontFamily: 'inherit' }}>
              {t === 'login' ? '🔑 Iniciar sesión' : '✨ Crear cuenta'}
            </button>
          ))}
        </div>

        <div style={{ padding: '28px 28px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>

          {tab === 'register' && (
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(160,180,220,0.5)', letterSpacing: '.08em', textTransform: 'uppercase', marginBottom: 6, fontFamily: 'monospace' }}>Nombre</div>
              <input value={name} onChange={e => setName(e.target.value)} placeholder="Tu nombre completo" style={inp} />
            </div>
          )}

          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(160,180,220,0.5)', letterSpacing: '.08em', textTransform: 'uppercase', marginBottom: 6, fontFamily: 'monospace' }}>Email</div>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="tu@email.com" style={inp} />
          </div>

          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(160,180,220,0.5)', letterSpacing: '.08em', textTransform: 'uppercase', marginBottom: 6, fontFamily: 'monospace' }}>Contraseña</div>
            <div style={{ position: 'relative' }}>
              <input type={show ? 'text' : 'password'} value={pass} onChange={e => setPass(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { if (tab === 'login') { handleLogin() } else { handleRegister() } } }}
                placeholder={tab === 'register' ? 'Mínimo 6 caracteres' : '••••••••'}
                style={{ ...inp, paddingRight: 44 }} />
              <button type="button" onClick={() => setShow(v => !v)}
                style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(255,255,255,0.4)', display: 'flex', padding: 4 }}>
                {show ? <EyeOff size={16}/> : <Eye size={16}/>}
              </button>
            </div>
          </div>

          {err && (
            <div style={{ padding: '10px 14px', borderRadius: 8, background: 'rgba(248,113,113,0.1)', border: '1px solid rgba(248,113,113,0.3)', fontSize: 13, color: '#F87171' }}>
              {err}
            </div>
          )}

          <button type="button" onClick={tab === 'login' ? handleLogin : handleRegister} disabled={loading}
            style={{ padding: '13px', borderRadius: 12, fontWeight: 700, fontSize: 15, cursor: loading ? 'wait' : 'pointer', border: 'none', background: loading ? 'rgba(211,255,58,0.5)' : ACCENT, color: DARK, transition: 'opacity .15s', fontFamily: 'inherit' }}>
            {loading ? 'Verificando…' : tab === 'login' ? 'Entrar' : 'Crear cuenta gratis'}
          </button>

          <button type="button" onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.35)', fontSize: 13, cursor: 'pointer', textAlign: 'center', fontFamily: 'inherit' }}>
            Cancelar
          </button>
        </div>
      </div>
    </div>
  )
}


/* ══════════════════════════════════════════════════════
   DELETE ACCOUNT CONFIRM
══════════════════════════════════════════════════════ */
const DeleteConfirm = ({
  user, onClose, onDeleted,
}: { user: UserProfile; onClose: () => void; onDeleted: () => void }): React.JSX.Element => {
  const [pass, setPass] = useState('')
  const [err,  setErr]  = useState('')

  const handleDelete = (): void => {
    const accounts = loadAccounts()
    const idx = accounts.findIndex(a => a.id === user.id && a.passHash === simpleHash(pass))
    if (idx === -1) { setErr('Contraseña incorrecta'); return }
    accounts.splice(idx, 1)
    saveAccounts(accounts)
    clearUser()
    onDeleted()
    onClose()
  }

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(4,6,12,0.92)', backdropFilter: 'blur(10px)' }}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div style={{ width: '100%', maxWidth: 360, background: '#0e1c35', border: '1px solid rgba(248,113,113,0.4)', borderRadius: 20, padding: 28, boxShadow: '0 40px 100px rgba(0,0,0,.8)', display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div style={{ fontSize: 20, fontWeight: 800, color: '#F87171' }}>⚠️ Eliminar cuenta</div>
        <div style={{ fontSize: 13, color: 'rgba(200,210,240,0.7)', lineHeight: 1.6 }}>
          Esto eliminará permanentemente tu cuenta <strong style={{ color: '#fff' }}>{user.email}</strong> y todos sus datos. Esta acción no se puede deshacer.
        </div>
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(160,180,220,0.5)', letterSpacing: '.08em', textTransform: 'uppercase', marginBottom: 6, fontFamily: 'monospace' }}>Confirmá tu contraseña</div>
          <input type="password" value={pass} onChange={e => setPass(e.target.value)}
            placeholder="Tu contraseña actual"
            style={{ width: '100%', padding: '11px 14px', borderRadius: 10, fontSize: 14, color: '#fff', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', outline: 'none', boxSizing: 'border-box', fontFamily: 'inherit' }}
            onKeyDown={e => { if (e.key === 'Enter') handleDelete() }} />
        </div>
        {err && <div style={{ fontSize: 13, color: '#F87171' }}>{err}</div>}
        <div style={{ display: 'flex', gap: 10 }}>
          <button type="button" onClick={onClose} style={{ flex: 1, padding: '12px', borderRadius: 10, fontWeight: 600, fontSize: 13, cursor: 'pointer', border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.7)', fontFamily: 'inherit' }}>
            Cancelar
          </button>
          <button type="button" onClick={handleDelete} style={{ flex: 1, padding: '12px', borderRadius: 10, fontWeight: 700, fontSize: 13, cursor: 'pointer', border: 'none', background: '#F87171', color: '#fff', fontFamily: 'inherit' }}>
            Eliminar cuenta
          </button>
        </div>
      </div>
    </div>
  )
}


/* ══════════════════════════════════════════════════════
   MAIN BAR
══════════════════════════════════════════════════════ */
export const MissionControlBar = ({
  onJump, handsFree, onHandsFreeToggle, onLaunchCUA,
  cuaMode, onCuaMode,
  activeTasks, isRunning,
  user, onLogin, onLogout,
}: MissionControlBarProps): React.JSX.Element => {
  /* ── command input ── */
  const [query,   setQuery]   = useState('')
  const [cursor,  setCursor]  = useState(0)
  const [focused, setFocused] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  /* ── latency tracking removed · pill no longer shown to end-users ── */

  /* ── dropdowns ── */
  const [cuaDrop,  setCuaDrop]  = useState(false)
  const [userDrop, setUserDrop] = useState(false)
  const cuaRef  = useRef<HTMLDivElement>(null)
  const userRef = useRef<HTMLDivElement>(null)

  /* ── voice wake (Web Speech API) ── */
  const voice = useVoiceWake({
    onWake: (_transcript) => {
      // Wake phrase detected → open hands-free overlay if not already
      if (!handsFree) onHandsFreeToggle()
    },
    lang: 'es-AR',
  })
  // Keep voice listening lifecycle in sync with handsFree state (user closing overlay shouldn't kill mic)
  const voiceTooltip =
    voice.state === 'listening'   ? 'Escuchando · decí "Hola SellIA"' :
    voice.state === 'requesting'  ? 'Pidiendo permiso de micrófono…' :
    voice.state === 'denied'      ? 'Permiso de mic denegado · revisar settings' :
    voice.state === 'unsupported' ? 'Tu navegador no soporta voz' :
    voice.state === 'error'       ? (voice.errorMsg ?? 'Error de voz') :
    'Activar voz · "Hola SellIA"'

  /* ── modals ── */
  const [showAuth,   setShowAuth]   = useState(false)
  const [showDelete, setShowDelete] = useState(false)

  /* ── command engine state ── */
  const [cmdHistory, setCmdHistory] = useState<string[]>([])
  const [histIdx,    setHistIdx]    = useState(-1)
  const [phIdx,      setPhIdx]      = useState(0)
  const [parsed,     setParsed]     = useState<{ intent: Intent; stripped: string } | null>(null)
  const [cmdResults, setCmdResults] = useState<CommandResult[]>([])

  /* ── close dropdowns on outside click ── */
  useEffect(() => {
    const fn = (e: MouseEvent): void => {
      if (cuaRef.current  && !cuaRef.current.contains(e.target  as Node)) setCuaDrop(false)
      if (userRef.current && !userRef.current.contains(e.target as Node)) setUserDrop(false)
    }
    document.addEventListener('mousedown', fn)
    return () => document.removeEventListener('mousedown', fn)
  }, [])

  /* ── keyboard shortcuts ── */
  useEffect(() => {
    const fn = (e: KeyboardEvent): void => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault(); inputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', fn)
    return () => window.removeEventListener('keydown', fn)
  }, [])

  /* ── load cmd history on mount ── */
  useEffect(() => { setCmdHistory(loadCmdHistory()) }, [])

  /* ── rotate placeholder ── */
  useEffect(() => {
    if (focused) return
    const iv = setInterval(() => setPhIdx(i => (i + 1) % PLACEHOLDER_EXAMPLES.length), 3500)
    return () => clearInterval(iv)
  }, [focused])

  /* ── parse intent on query change ── */
  useEffect(() => {
    if (!query.trim()) { setParsed(null); setCmdResults([]); return }
    const p = parseIntent(query)
    setParsed(p)
    setCmdResults(p ? buildCommandResults(query, p.intent, p.stripped) : [])
  }, [query])

  /* ── fuzzy search results ── */
  const results = useMemo<Tool[]>(() => {
    if (!query.trim()) return []
    return TOOLS
      .map(t => ({ tool: t, score: fuzzyMatch(query, t) }))
      .filter(x => x.score > 0)
      .sort((a, b) => b.score - a.score || b.tool.weight - a.tool.weight)
      .slice(0, 7)
      .map(x => x.tool)
  }, [query])

  useEffect(() => { setCursor(0) }, [query])

  const handleSelect = useCallback((tool: Tool): void => {
    if (query.trim()) pushCmdHistory(query)
    setQuery(''); setFocused(false); setHistIdx(-1); inputRef.current?.blur()
    setCmdHistory(loadCmdHistory())
    onJump(tool.componentId)
  }, [onJump, query])

  const handleSelectCmd = useCallback((cmd: CommandResult): void => {
    if (query.trim()) pushCmdHistory(query)
    setQuery(''); setFocused(false); setHistIdx(-1); inputRef.current?.blur()
    setCmdHistory(loadCmdHistory())
    onJump(cmd.componentId, cmd.lobe)
  }, [onJump, query])

  const handleKey = useCallback((e: React.KeyboardEvent<HTMLInputElement>): void => {
    const allLen = cmdResults.length + results.length
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (histIdx >= 0) {
        if (histIdx === 0) { setHistIdx(-1); setQuery('') }
        else { const ni = histIdx - 1; setHistIdx(ni); setQuery(cmdHistory[ni] ?? '') }
      } else {
        setCursor(c => Math.min(c + 1, Math.max(allLen - 1, 0)))
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (query === '' && cmdHistory.length > 0) {
        setHistIdx(0); setQuery(cmdHistory[0] ?? '')
      } else if (histIdx >= 0 && cmdHistory.length > histIdx + 1) {
        const ni = histIdx + 1; setHistIdx(ni); setQuery(cmdHistory[ni] ?? '')
      } else if (histIdx === -1 && query.trim()) {
        setCursor(c => Math.max(c - 1, 0))
      }
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (cursor < cmdResults.length && cmdResults[cursor]) {
        handleSelectCmd(cmdResults[cursor])
      } else {
        const toolIdx = cursor - cmdResults.length
        if (results[toolIdx]) handleSelect(results[toolIdx])
      }
    } else if (e.key === 'Escape') {
      setQuery(''); setFocused(false); setHistIdx(-1); inputRef.current?.blur()
    }
  }, [cmdResults, results, cursor, handleSelect, handleSelectCmd, histIdx, cmdHistory, query])

  const showDrop = focused && (cmdResults.length > 0 || results.length > 0 || query.trim() === '')
  const cuaActive = CUA_OPTIONS.find(o => o.id === cuaMode) ?? CUA_OPTIONS[0]

  /* ── pill style ── */
  const pill = (color: string): React.CSSProperties => ({
    display: 'inline-flex', alignItems: 'center', gap: 5,
    padding: '2px 8px', borderRadius: 100,
    fontSize: 10, fontWeight: 700,
    fontFamily: 'Geist Mono, ui-monospace, monospace',
    whiteSpace: 'nowrap', letterSpacing: '.04em',
    background: `${color}18`, border: `1px solid ${color}35`, color,
  })

  return (
    <>
      {/* ─── BAR ─── */}
      <header style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 9100, pointerEvents: 'none' }}>
        <div style={{
          pointerEvents: 'auto',
          background: 'rgba(8,9,12,0.92)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255,255,255,0.07)',
          height: 56,
          display: 'flex', alignItems: 'center',
          padding: '0 16px', gap: 10,
          maxWidth: '100%',
        }}>

          {/* identity */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, paddingRight: 10, borderRight: '1px solid rgba(255,255,255,0.08)', flexShrink: 0 }}>
            <span style={{ position: 'relative', width: 28, height: 28, borderRadius: 7, background: ACCENT, boxShadow: `0 0 14px -2px ${ACCENT}55`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <svg viewBox="0 0 24 24" width={14} height={14} fill="none" stroke={DARK} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 17 L9 11 L13 15 L21 7" />
                <circle cx="21" cy="7" r="1.6" fill={DARK} />
              </svg>
              <span style={{ position: 'absolute', bottom: -2, right: -2, width: 8, height: 8, borderRadius: '50%', border: `1.5px solid ${DARK}`, background: isRunning ? '#22c55e' : handsFree ? '#f0abfc' : '#64748b' }} />
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: '#fff', letterSpacing: '-0.02em' }}>SellIA</span>
              <span style={{ fontSize: 9, fontFamily: 'Geist Mono, monospace', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.38)' }}>
                {isRunning ? `${activeTasks} procesos · live` : 'rev-OS · online'}
              </span>
            </div>
          </div>

          {/* command input */}
          <div style={{ flex: 1, position: 'relative' }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '0 14px', height: 38,
              background: focused ? 'rgba(255,255,255,0.09)' : 'rgba(255,255,255,0.05)',
              border: `1px solid ${focused ? 'rgba(211,255,58,0.35)' : 'rgba(255,255,255,0.1)'}`,
              borderRadius: focused ? '10px 10px 0 0' : 10,
              transition: 'border-color .15s, background .15s',
            }}>
              <Search size={14} style={{ color: ACCENT, flexShrink: 0 }} />
              <input
                ref={inputRef}
                value={query}
                onChange={e => { setQuery(e.target.value); setHistIdx(-1) }}
                onKeyDown={handleKey}
                onFocus={() => setFocused(true)}
                onBlur={() => setTimeout(() => setFocused(false), 150)}
                placeholder={PLACEHOLDER_EXAMPLES[phIdx]}
                style={{
                  flex: 1, background: 'transparent', border: 'none', outline: 'none',
                  fontSize: 13, color: 'rgba(255,255,255,0.9)', fontFamily: 'inherit',
                }}
                aria-label="Comando SellIA"
                autoComplete="off"
              />
              {query && (
                <button type="button" onClick={() => setQuery('')}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(255,255,255,0.3)', fontSize: 16, padding: '0 2px', lineHeight: 1 }}>×</button>
              )}
              {!query && (
                <kbd style={{ display: 'inline-flex', alignItems: 'center', gap: 3, padding: '2px 6px', borderRadius: 5, border: '1px solid rgba(255,255,255,0.1)', fontSize: 10, fontFamily: 'monospace', color: 'rgba(255,255,255,0.4)', flexShrink: 0 }}>
                  ⌘K
                </kbd>
              )}
            </div>

            {/* inline suggestion dropdown */}
            {showDrop && (
              <div style={{
                position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 200,
                background: 'rgba(8,10,18,0.98)', border: '1px solid rgba(255,255,255,0.12)',
                borderTop: 'none', borderRadius: '0 0 12px 12px',
                backdropFilter: 'blur(20px)', overflow: 'hidden',
                boxShadow: '0 20px 60px rgba(0,0,0,.8)',
                maxHeight: 440, overflowY: 'auto',
              }}>

                {/* ── intent interpretation header ── */}
                {parsed && (
                  <div style={{ padding: '9px 14px 7px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 10, color: 'rgba(160,180,220,0.4)', fontFamily: 'Geist Mono, monospace', letterSpacing: '.06em' }}>SellIA va a →</span>
                    <span style={{
                      padding: '2px 8px', borderRadius: 6, fontSize: 9, fontWeight: 800,
                      fontFamily: 'Geist Mono, monospace', letterSpacing: '.12em',
                      background: `${INTENT_COLOR[parsed.intent]}22`,
                      border: `1px solid ${INTENT_COLOR[parsed.intent]}44`,
                      color: INTENT_COLOR[parsed.intent],
                    }}>
                      {INTENT_LABEL[parsed.intent]}
                    </span>
                    <span style={{ fontSize: 11, color: 'rgba(200,215,255,0.55)' }}>{INTENT_SUB[parsed.intent]}</span>
                  </div>
                )}

                {/* ── command results (intent engine) ── */}
                {cmdResults.map((cmd, idx) => (
                  <button key={cmd.id} type="button"
                    onMouseDown={() => handleSelectCmd(cmd)}
                    onMouseEnter={() => setCursor(idx)}
                    style={{
                      width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                      padding: '10px 14px', border: 'none', cursor: 'pointer', textAlign: 'left',
                      background: cursor === idx ? 'rgba(211,255,58,0.06)' : 'transparent',
                      transition: 'background .1s',
                    }}
                  >
                    <span style={{ fontSize: 20, width: 30, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{cmd.icon}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: cursor === idx ? '#fff' : 'rgba(255,255,255,0.85)', lineHeight: 1.2 }}>{cmd.label}</div>
                      <div style={{ fontSize: 11, color: 'rgba(160,180,220,0.4)', marginTop: 1 }}>{cmd.sublabel}</div>
                    </div>
                    <span style={{
                      padding: '2px 7px', borderRadius: 5, fontSize: 9, fontWeight: 800,
                      fontFamily: 'Geist Mono, monospace', letterSpacing: '.1em', flexShrink: 0,
                      background: `${INTENT_COLOR[cmd.intent]}18`,
                      border: `1px solid ${INTENT_COLOR[cmd.intent]}33`,
                      color: INTENT_COLOR[cmd.intent],
                    }}>
                      {INTENT_LABEL[cmd.intent]}
                    </span>
                  </button>
                ))}

                {/* ── fuzzy tool results ── */}
                {results.length > 0 && (
                  <>
                    {cmdResults.length > 0 && (
                      <div style={{ padding: '6px 14px 3px', fontSize: 9, color: 'rgba(255,255,255,0.22)', fontFamily: 'Geist Mono, monospace', letterSpacing: '.1em', textTransform: 'uppercase', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                        Herramientas
                      </div>
                    )}
                    {results.slice(0, cmdResults.length > 0 ? 3 : 7).map((tool, idx) => {
                      const absIdx = cmdResults.length + idx
                      return (
                        <button key={tool.id} type="button"
                          onMouseDown={() => handleSelect(tool)}
                          onMouseEnter={() => setCursor(absIdx)}
                          style={{
                            width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                            padding: '9px 14px', border: 'none', cursor: 'pointer', textAlign: 'left',
                            background: cursor === absIdx ? 'rgba(255,255,255,0.07)' : 'transparent',
                            transition: 'background .1s',
                          }}
                        >
                          <span style={{ fontSize: 18, width: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{tool.icon}</span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontSize: 13, fontWeight: 600, color: cursor === absIdx ? '#fff' : 'rgba(255,255,255,0.8)', lineHeight: 1.2 }}>{tool.title}</div>
                            <div style={{ fontSize: 11, color: 'rgba(160,180,220,0.45)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 1 }}>{tool.subtitle}</div>
                          </div>
                          <ArrowRight size={12} style={{ color: cursor === absIdx ? ACCENT : 'rgba(255,255,255,0.2)', flexShrink: 0 }} />
                        </button>
                      )
                    })}
                  </>
                )}

                {/* ── no results ── */}
                {query.trim() !== '' && cmdResults.length === 0 && results.length === 0 && (
                  <div style={{ padding: '14px 16px', fontSize: 13, color: 'rgba(255,255,255,0.35)', fontStyle: 'italic' }}>
                    Sin resultados — probá: &quot;leads&quot;, &quot;carrito&quot;, &quot;arca&quot;
                  </div>
                )}

                {/* ── empty state ── */}
                {query.trim() === '' && (
                  <>
                    <div style={{ padding: '12px 14px 8px' }}>
                      <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.22)', fontFamily: 'Geist Mono, monospace', letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 8 }}>Acciones rápidas</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {QUICK_COMMANDS.map(qc => (
                          <button key={qc.label} type="button"
                            onMouseDown={() => { setQuery(qc.query); inputRef.current?.focus() }}
                            style={{
                              padding: '5px 11px', borderRadius: 100, fontSize: 11, fontWeight: 500,
                              cursor: 'pointer', border: '1px solid rgba(255,255,255,0.1)',
                              background: 'rgba(255,255,255,0.05)', color: 'rgba(200,215,255,0.65)',
                              fontFamily: 'inherit', transition: 'background .1s',
                            }}>
                            {qc.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {cmdHistory.length > 0 && (
                      <>
                        <div style={{ padding: '5px 14px 2px', fontSize: 9, color: 'rgba(255,255,255,0.22)', fontFamily: 'Geist Mono, monospace', letterSpacing: '.1em', textTransform: 'uppercase', borderTop: '1px solid rgba(255,255,255,0.05)' }}>Recientes</div>
                        {cmdHistory.slice(0, 4).map((h, i) => (
                          <button key={i} type="button"
                            onMouseDown={() => { setQuery(h); inputRef.current?.focus() }}
                            style={{
                              width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                              padding: '8px 14px', border: 'none', cursor: 'pointer', textAlign: 'left',
                              background: 'transparent', color: 'rgba(180,200,240,0.55)', fontSize: 12,
                              fontFamily: 'inherit', transition: 'background .1s',
                            }}>
                            <span style={{ fontSize: 13, opacity: 0.45 }}>🕐</span>
                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{h}</span>
                          </button>
                        ))}
                      </>
                    )}

                    <div style={{ padding: '8px 14px', borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', gap: 5, flexWrap: 'wrap', alignItems: 'center' }}>
                      <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.2)', fontFamily: 'Geist Mono, monospace', letterSpacing: '.06em', marginRight: 2 }}>slash cmds:</span>
                      {['/show', '/open', '/activate', '/report', '/config', '/create', '/stop'].map(s => (
                        <button key={s} type="button"
                          onMouseDown={() => { setQuery(s + ' '); inputRef.current?.focus() }}
                          style={{
                            padding: '2px 8px', borderRadius: 5, fontSize: 10, fontWeight: 700,
                            fontFamily: 'Geist Mono, monospace', letterSpacing: '.04em',
                            cursor: 'pointer', border: '1px solid rgba(255,255,255,0.08)',
                            background: 'rgba(255,255,255,0.04)', color: 'rgba(160,180,220,0.45)',
                          }}>
                          {s}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}
          </div>

          {/* active tasks pill */}
          {isRunning && activeTasks > 0 && (
            <span style={pill('#8B5CF6')}>
              {activeTasks} activos
            </span>
          )}

          <div style={{ width: 1, height: 22, background: 'rgba(255,255,255,0.08)', flexShrink: 0 }} />

          {/* Computer Use dropdown — doubled width for visibility */}
          <div ref={cuaRef} style={{ position: 'relative', flexShrink: 0 }}>
            <button type="button" onClick={() => setCuaDrop(v => !v)}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                padding: '5px 22px',
                minWidth: 220,
                borderRadius: 9,
                background: `${cuaActive.color}14`,
                border: `1px solid ${cuaActive.color}35`,
                color: cuaActive.color,
                cursor: 'pointer',
                fontSize: 12, fontWeight: 700,
                transition: 'background .15s, border-color .15s',
              }}
              onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = `${cuaActive.color}1E` }}
              onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = `${cuaActive.color}14` }}
            >
              {cuaActive.icon}
              <span>Computer Use</span>
              <MonitorCheck size={13} style={{ display: cuaMode === 'off' ? 'none' : 'block', opacity: 0.7 }} />
              <ChevronDown size={12} style={{ opacity: 0.7, marginLeft: 'auto' }} />
            </button>
            {cuaDrop && (
              <div style={{ position: 'absolute', right: 0, top: 'calc(100% + 6px)', width: 240, background: 'rgba(8,10,18,0.98)', border: '1px solid rgba(255,255,255,0.14)', borderRadius: 14, overflow: 'hidden', zIndex: 300, boxShadow: '0 20px 60px rgba(0,0,0,.8)', backdropFilter: 'blur(20px)' }}>
                <div style={{ padding: '8px 14px', borderBottom: '1px solid rgba(255,255,255,0.07)', fontSize: 10, color: 'rgba(160,180,220,0.4)', fontFamily: 'monospace', letterSpacing: '.1em', textTransform: 'uppercase' }}>Modo Computer Use</div>
                {CUA_OPTIONS.map(o => (
                  <button key={o.id} type="button" onClick={() => { onCuaMode(o.id); setCuaDrop(false) }}
                    style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', cursor: 'pointer', border: 'none', textAlign: 'left', background: cuaMode === o.id ? `${o.color}12` : 'transparent', borderBottom: '1px solid rgba(255,255,255,0.06)', transition: 'background .12s' }}>
                    <span style={{ color: o.color, display: 'flex', flexShrink: 0 }}>{o.icon}</span>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: '#F0F4FF', lineHeight: 1.2 }}>{o.label}</div>
                      <div style={{ fontSize: 11, color: 'rgba(160,180,220,0.45)', marginTop: 1 }}>{o.desc}</div>
                    </div>
                    {cuaMode === o.id && <div style={{ marginLeft: 'auto', width: 7, height: 7, borderRadius: '50%', background: o.color, boxShadow: `0 0 8px ${o.color}`, flexShrink: 0 }} />}
                  </button>
                ))}
                <button type="button" onClick={() => { onLaunchCUA(); setCuaDrop(false) }}
                  style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, padding: '10px', fontSize: 13, fontWeight: 600, color: '#00D4FF', cursor: 'pointer', border: 'none', background: 'transparent' }}>
                  <MonitorCheck size={14}/> Abrir sesión <ArrowRight size={12}/>
                </button>
              </div>
            )}
          </div>

          {/* VOZ — Web Speech API: pide micrófono + wake "Hola SellIA" */}
          <button type="button"
            onClick={() => {
              // Toggle mic. If wake fires while listening → opens HandsFreeOverlay via onWake callback.
              voice.toggle()
              // If user has overlay open + mic already listening, this also closes overlay
              if (handsFree && voice.isListening) onHandsFreeToggle()
            }}
            style={{
              display: 'flex', alignItems: 'center', gap: 7,
              padding: '5px 12px', borderRadius: 9,
              border: `1px solid ${
                voice.state === 'denied' || voice.state === 'error' ? 'rgba(248,113,113,0.5)'
                : voice.isListening ? 'rgba(34,197,94,0.55)'
                : voice.state === 'requesting' ? 'rgba(245,158,11,0.5)'
                : handsFree ? 'rgba(240,171,252,0.5)' : 'rgba(255,255,255,0.1)'
              }`,
              background: voice.isListening ? 'rgba(34,197,94,0.10)'
                       : voice.state === 'denied' || voice.state === 'error' ? 'rgba(248,113,113,0.08)'
                       : voice.state === 'requesting' ? 'rgba(245,158,11,0.08)'
                       : handsFree ? 'rgba(240,171,252,0.08)'
                       : 'rgba(255,255,255,0.04)',
              cursor: voice.state === 'unsupported' ? 'not-allowed' : 'pointer',
              flexShrink: 0,
              opacity: voice.state === 'unsupported' ? 0.5 : 1,
              transition: 'background .15s, border-color .15s',
            }}
            title={voiceTooltip}
            aria-pressed={voice.isListening}
            disabled={voice.state === 'unsupported'}
          >
            {voice.isListening ? (
              <span style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <Mic size={14} color="#22c55e" />
                <span style={{
                  position: 'absolute', inset: -3, borderRadius: '50%',
                  border: '1.5px solid rgba(34,197,94,0.6)',
                  animation: 'voice-ring 1.4s ease-out infinite',
                }} />
              </span>
            ) : voice.state === 'denied' || voice.state === 'error' ? (
              <MicOff size={14} color="#f87171" />
            ) : voice.state === 'requesting' ? (
              <Mic size={14} color="#f59e0b" />
            ) : (
              <MicOff size={14} color="rgba(255,255,255,0.5)" />
            )}
            <span style={{
              fontSize: 10, fontWeight: 700,
              letterSpacing: '.08em', textTransform: 'uppercase',
              fontFamily: 'monospace',
              color: voice.isListening ? '#22c55e'
                  : voice.state === 'denied' || voice.state === 'error' ? '#f87171'
                  : voice.state === 'requesting' ? '#f59e0b'
                  : handsFree ? '#f9a8d4' : 'rgba(255,255,255,0.6)',
            }}>
              {voice.isListening ? 'ESCUCHANDO' :
               voice.state === 'requesting' ? 'PERMISO…' :
               voice.state === 'denied' ? 'MIC OFF' :
               voice.state === 'unsupported' ? 'N/A' : 'VOZ'}
            </span>
          </button>
          <style>{`@keyframes voice-ring{0%{transform:scale(.85);opacity:.8}100%{transform:scale(1.6);opacity:0}}`}</style>

          <div style={{ width: 1, height: 22, background: 'rgba(255,255,255,0.08)', flexShrink: 0 }} />

          {/* notifications · a la izquierda del botón Entrar */}
          <NotificationsDropdown />

          {/* settings · rueda · a la derecha de la campana */}
          <SettingsDropdown />

          <div style={{ width: 1, height: 22, background: 'rgba(255,255,255,0.08)', flexShrink: 0 }} />

          {/* user menu */}
          <div ref={userRef} style={{ position: 'relative', flexShrink: 0 }}>
            <button type="button" onClick={() => setUserDrop(v => !v)}
              style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '5px 10px', borderRadius: 9, border: '1px solid rgba(255,255,255,0.1)', background: user ? 'rgba(211,255,58,0.07)' : 'rgba(255,255,255,0.04)', cursor: 'pointer' }}>
              {user ? (
                <>
                  <div style={{ width: 22, height: 22, borderRadius: '50%', background: ACCENT, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <span style={{ fontSize: 11, fontWeight: 900, color: DARK }}>{user.name[0].toUpperCase()}</span>
                  </div>
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'rgba(255,255,255,0.85)', maxWidth: 80, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user.name.split(' ')[0]}</span>
                </>
              ) : (
                <>
                  <User size={14} color="rgba(255,255,255,0.5)"/>
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'rgba(255,255,255,0.55)' }}>Entrar</span>
                </>
              )}
              <ChevronDown size={11} style={{ color: 'rgba(255,255,255,0.35)', flexShrink: 0 }} />
            </button>

            {userDrop && (
              <div style={{ position: 'absolute', right: 0, top: 'calc(100% + 6px)', width: 220, background: 'rgba(8,10,18,0.98)', border: '1px solid rgba(255,255,255,0.14)', borderRadius: 14, overflow: 'hidden', zIndex: 300, boxShadow: '0 20px 60px rgba(0,0,0,.8)', backdropFilter: 'blur(20px)' }}>
                {user ? (
                  <>
                    <div style={{ padding: '14px 16px', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: '#F0F4FF' }}>{user.name}</div>
                      <div style={{ fontSize: 11, color: 'rgba(160,180,220,0.5)', marginTop: 2 }}>{user.email}</div>
                      <div style={{ fontSize: 10, color: 'rgba(160,180,220,0.3)', marginTop: 4, fontFamily: 'monospace' }}>Cuenta desde {new Date(user.createdAt).toLocaleDateString('es-AR')}</div>
                    </div>
                    <button type="button" onClick={() => { onLogout(); setUserDrop(false) }}
                      style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '11px 16px', cursor: 'pointer', border: 'none', background: 'transparent', color: 'rgba(200,210,240,0.7)', fontSize: 13, fontWeight: 500 }}>
                      <LogOut size={14}/> Cerrar sesión
                    </button>
                    <button type="button" onClick={() => { setUserDrop(false); setShowDelete(true) }}
                      style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '11px 16px', cursor: 'pointer', border: 'none', background: 'transparent', color: '#F87171', fontSize: 13, fontWeight: 500, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                      <Trash2 size={14}/> Eliminar cuenta
                    </button>
                  </>
                ) : (
                  <>
                    <button type="button" onClick={() => { setUserDrop(false); setShowAuth(true) }}
                      style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '13px 16px', cursor: 'pointer', border: 'none', background: 'transparent', color: '#F0F4FF', fontSize: 13, fontWeight: 600 }}>
                      <LogIn size={14} style={{ color: ACCENT }}/> Iniciar sesión
                    </button>
                    <button type="button" onClick={() => { setUserDrop(false); setShowAuth(true) }}
                      style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '13px 16px', cursor: 'pointer', border: 'none', background: `${ACCENT}0C`, color: ACCENT, fontSize: 13, fontWeight: 700, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                      <UserPlus size={14}/> Crear cuenta gratis
                    </button>
                  </>
                )}
              </div>
            )}
          </div>

        </div>
      </header>

      {/* ─── MODALS ─── */}
      {showAuth && (
        <AuthModal
          onClose={() => setShowAuth(false)}
          onAuth={u => { onLogin(u); setShowAuth(false) }}
        />
      )}
      {showDelete && user && (
        <DeleteConfirm
          user={user}
          onClose={() => setShowDelete(false)}
          onDeleted={onLogout}
        />
      )}
    </>
  )
}


export default MissionControlBar
