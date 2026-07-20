'use client'

/**
 * SETTINGS PROVIDER
 *
 * Centraliza theme (light/dark) + idioma de toda la plataforma.
 * Persiste en localStorage. Aplica `data-theme` y `lang` a <html>.
 *
 * Idiomas soportados: es (Español · default) · en (English) · pt (Português) · fr (Français)
 *
 * Uso:
 *   const { lang, setLang, theme, setTheme, t } = useSettings()
 *   <h1>{t('dashboard.title')}</h1>
 */

import {
  createContext, useCallback, useContext, useEffect, useMemo, useState,
  type ReactNode,
} from 'react'
import { useTheme as useNextTheme } from 'next-themes'

// ── Types ──────────────────────────────────────────────────────────────────────
export type Theme = 'dark' | 'light'
export type Lang  = 'es' | 'en' | 'pt' | 'fr'

interface SettingsCtx {
  theme: Theme
  lang:  Lang
  setTheme: (t: Theme) => void
  setLang:  (l: Lang)  => void
  t:        (key: string, vars?: Record<string, string | number>) => string
}

const LS_THEME = 'sellia_theme_v1'
const LS_LANG  = 'sellia_lang_v1'

// ── Translations ──────────────────────────────────────────────────────────────
// Add keys here. Missing key falls back to ES → key.
type Dict = Record<string, string>

const TRANSLATIONS: Record<Lang, Dict> = {
  es: {
    // Nav tabs
    'nav.dashboard':   'Dashboard',
    'nav.squads':      'Escuadrones',
    'nav.pipeline':    'Pipeline de Ventas',
    'nav.audit':       'Agent Audit Log',
    'nav.handoff':     'Handoff · Slack IA',
    'nav.approvals':   'Aprobaciones',
    'nav.neural':      'Cerebro Neuronal',
    // Mission bar
    'mb.search':       'Buscar herramienta…',
    'mb.computer_use': 'Computer Use',
    'mb.voice':        'VOZ',
    'mb.voice.listening':   'ESCUCHANDO',
    'mb.voice.requesting':  'PERMISO…',
    'mb.voice.denied':      'MIC OFF',
    'mb.voice.unsupported': 'N/A',
    'mb.login':        'Entrar',
    'mb.create_acct':  'Crear cuenta gratis',
    'mb.logout':       'Cerrar sesión',
    'mb.delete_acct':  'Eliminar cuenta',
    // Notifications
    'notif.title':     'Notificaciones',
    'notif.empty':     'Sin notificaciones nuevas',
    'notif.mark_all':  'Marcar todas',
    'notif.view_all':  'Ver todas',
    'notif.unread':    'sin leer',
    // Settings
    'set.title':       'Configuración',
    'set.theme':       'Tema',
    'set.theme.dark':  'Modo oscuro',
    'set.theme.light': 'Modo claro',
    'set.lang':        'Idioma',
    'set.lang.es':     'Español',
    'set.lang.en':     'Inglés',
    'set.lang.pt':     'Portugués',
    'set.lang.fr':     'Francés',
    // Squads
    'squad.title':     'Escuadrones SellIA',
    'squad.executing': 'EJECUTANDO',
    'squad.idle':      'EN REPOSO',
    'squad.paused':    'PAUSADO',
    'squad.attention': 'ATENCIÓN',
    // Approvals
    'apr.title':       'Centro de Aprobaciones',
    'apr.subtitle':    'Human-in-the-Loop',
    'apr.all':         'Todas',
    'apr.critical':    'Crítico',
    'apr.high':        'Alto',
    'apr.medium':      'Medio',
    'apr.low':         'Bajo',
    'apr.approve':     'Aprobar',
    'apr.reject':      'Rechazar',
    'apr.expand_all':  'Expandir todo',
    'apr.collapse_all': 'Colapsar todo',
    'apr.empty':       'Sin decisiones pendientes',
    // Neural
    'neural.title':    'Cerebro Neuronal en Vivo',
    'neural.active':   'SINAPSIS ACTIVAS',
    'neural.idle':     'EN REPOSO',
    'neural.offline':  'Cerebro offline · reintentando…',
  },
  en: {
    'nav.dashboard':   'Dashboard',
    'nav.squads':      'Squads',
    'nav.pipeline':    'Sales Pipeline',
    'nav.audit':       'Agent Audit Log',
    'nav.handoff':     'Handoff · AI Slack',
    'nav.approvals':   'Approvals',
    'nav.neural':      'Neural Brain',
    'mb.search':       'Search tool…',
    'mb.computer_use': 'Computer Use',
    'mb.voice':        'VOICE',
    'mb.voice.listening':   'LISTENING',
    'mb.voice.requesting':  'PERMISSION…',
    'mb.voice.denied':      'MIC OFF',
    'mb.voice.unsupported': 'N/A',
    'mb.login':        'Sign in',
    'mb.create_acct':  'Create free account',
    'mb.logout':       'Sign out',
    'mb.delete_acct':  'Delete account',
    'notif.title':     'Notifications',
    'notif.empty':     'No new notifications',
    'notif.mark_all':  'Mark all',
    'notif.view_all':  'View all',
    'notif.unread':    'unread',
    'set.title':       'Settings',
    'set.theme':       'Theme',
    'set.theme.dark':  'Dark mode',
    'set.theme.light': 'Light mode',
    'set.lang':        'Language',
    'set.lang.es':     'Spanish',
    'set.lang.en':     'English',
    'set.lang.pt':     'Portuguese',
    'set.lang.fr':     'French',
    'squad.title':     'SellIA Squads',
    'squad.executing': 'EXECUTING',
    'squad.idle':      'IDLE',
    'squad.paused':    'PAUSED',
    'squad.attention': 'ATTENTION',
    'apr.title':       'Approvals Center',
    'apr.subtitle':    'Human-in-the-Loop',
    'apr.all':         'All',
    'apr.critical':    'Critical',
    'apr.high':        'High',
    'apr.medium':      'Medium',
    'apr.low':         'Low',
    'apr.approve':     'Approve',
    'apr.reject':      'Reject',
    'apr.expand_all':  'Expand all',
    'apr.collapse_all': 'Collapse all',
    'apr.empty':       'No pending decisions',
    'neural.title':    'Live Neural Brain',
    'neural.active':   'ACTIVE SYNAPSES',
    'neural.idle':     'IDLE',
    'neural.offline':  'Brain offline · retrying…',
  },
  pt: {
    'nav.dashboard':   'Painel',
    'nav.squads':      'Esquadrões',
    'nav.pipeline':    'Pipeline de Vendas',
    'nav.audit':       'Agent Audit Log',
    'nav.handoff':     'Handoff · Slack IA',
    'nav.approvals':   'Aprovações',
    'nav.neural':      'Cérebro Neural',
    'mb.search':       'Buscar ferramenta…',
    'mb.computer_use': 'Computer Use',
    'mb.voice':        'VOZ',
    'mb.voice.listening':   'OUVINDO',
    'mb.voice.requesting':  'PERMISSÃO…',
    'mb.voice.denied':      'MIC OFF',
    'mb.voice.unsupported': 'N/D',
    'mb.login':        'Entrar',
    'mb.create_acct':  'Criar conta grátis',
    'mb.logout':       'Sair',
    'mb.delete_acct':  'Excluir conta',
    'notif.title':     'Notificações',
    'notif.empty':     'Sem notificações novas',
    'notif.mark_all':  'Marcar todas',
    'notif.view_all':  'Ver todas',
    'notif.unread':    'não lidas',
    'set.title':       'Configurações',
    'set.theme':       'Tema',
    'set.theme.dark':  'Modo escuro',
    'set.theme.light': 'Modo claro',
    'set.lang':        'Idioma',
    'set.lang.es':     'Espanhol',
    'set.lang.en':     'Inglês',
    'set.lang.pt':     'Português',
    'set.lang.fr':     'Francês',
    'squad.title':     'Esquadrões SellIA',
    'squad.executing': 'EXECUTANDO',
    'squad.idle':      'EM REPOUSO',
    'squad.paused':    'PAUSADO',
    'squad.attention': 'ATENÇÃO',
    'apr.title':       'Central de Aprovações',
    'apr.subtitle':    'Human-in-the-Loop',
    'apr.all':         'Todas',
    'apr.critical':    'Crítico',
    'apr.high':        'Alto',
    'apr.medium':      'Médio',
    'apr.low':         'Baixo',
    'apr.approve':     'Aprovar',
    'apr.reject':      'Rejeitar',
    'apr.expand_all':  'Expandir tudo',
    'apr.collapse_all': 'Recolher tudo',
    'apr.empty':       'Sem decisões pendentes',
    'neural.title':    'Cérebro Neural Ao Vivo',
    'neural.active':   'SINAPSES ATIVAS',
    'neural.idle':     'EM REPOUSO',
    'neural.offline':  'Cérebro offline · tentando…',
  },
  fr: {
    'nav.dashboard':   'Tableau de bord',
    'nav.squads':      'Escouades',
    'nav.pipeline':    'Pipeline des ventes',
    'nav.audit':       'Agent Audit Log',
    'nav.handoff':     'Handoff · Slack IA',
    'nav.approvals':   'Approbations',
    'nav.neural':      'Cerveau Neuronal',
    'mb.search':       'Chercher outil…',
    'mb.computer_use': 'Computer Use',
    'mb.voice':        'VOIX',
    'mb.voice.listening':   'À L\'ÉCOUTE',
    'mb.voice.requesting':  'PERMISSION…',
    'mb.voice.denied':      'MIC OFF',
    'mb.voice.unsupported': 'N/D',
    'mb.login':        'Connexion',
    'mb.create_acct':  'Créer un compte gratuit',
    'mb.logout':       'Déconnexion',
    'mb.delete_acct':  'Supprimer le compte',
    'notif.title':     'Notifications',
    'notif.empty':     'Aucune notification',
    'notif.mark_all':  'Tout marquer',
    'notif.view_all':  'Voir toutes',
    'notif.unread':    'non lues',
    'set.title':       'Paramètres',
    'set.theme':       'Thème',
    'set.theme.dark':  'Mode sombre',
    'set.theme.light': 'Mode clair',
    'set.lang':        'Langue',
    'set.lang.es':     'Espagnol',
    'set.lang.en':     'Anglais',
    'set.lang.pt':     'Portugais',
    'set.lang.fr':     'Français',
    'squad.title':     'Escouades SellIA',
    'squad.executing': 'EN EXÉCUTION',
    'squad.idle':      'AU REPOS',
    'squad.paused':    'EN PAUSE',
    'squad.attention': 'ATTENTION',
    'apr.title':       'Centre d\'Approbations',
    'apr.subtitle':    'Human-in-the-Loop',
    'apr.all':         'Toutes',
    'apr.critical':    'Critique',
    'apr.high':        'Haute',
    'apr.medium':      'Moyenne',
    'apr.low':         'Basse',
    'apr.approve':     'Approuver',
    'apr.reject':      'Rejeter',
    'apr.expand_all':  'Tout déplier',
    'apr.collapse_all': 'Tout replier',
    'apr.empty':       'Aucune décision en attente',
    'neural.title':    'Cerveau Neuronal en Direct',
    'neural.active':   'SYNAPSES ACTIVES',
    'neural.idle':     'AU REPOS',
    'neural.offline':  'Cerveau hors ligne · nouvel essai…',
  },
}

// ── Context ────────────────────────────────────────────────────────────────────
const Ctx = createContext<SettingsCtx | null>(null)

const isLang = (v: string): v is Lang => v === 'es' || v === 'en' || v === 'pt' || v === 'fr'

export const SettingsProvider = ({ children }: { children: ReactNode }): React.JSX.Element => {
  // Use next-themes as source of truth for theme (avoids fight with global ThemeProvider)
  const { resolvedTheme, setTheme: setNextTheme } = useNextTheme()
  const theme: Theme = resolvedTheme === 'light' ? 'light' : 'dark'

  const [lang, setLangState] = useState<Lang>('es')

  // Load lang from localStorage on mount
  useEffect(() => {
    try {
      const lStored = localStorage.getItem(LS_LANG)
      if (lStored && isLang(lStored)) setLangState(lStored)
    } catch { /* noop */ }
  }, [])

  // Force data-theme attr too (for our CSS selectors that target it)
  useEffect(() => {
    if (typeof document === 'undefined') return
    document.documentElement.dataset.theme = theme
  }, [theme])

  // Apply lang to <html> + trigger DOM translation
  useEffect(() => {
    if (typeof document === 'undefined') return
    document.documentElement.lang = lang
    // Dynamic import to keep DOM translator out of SSR bundle
    void import('./domTranslator').then(({ translateDocument }) => {
      void translateDocument(lang)
    })
  }, [lang])

  const setTheme = useCallback((t: Theme): void => {
    setNextTheme(t)
    try { localStorage.setItem(LS_THEME, t) } catch { /* noop */ }
  }, [setNextTheme])

  const setLang = useCallback((l: Lang): void => {
    setLangState(l)
    try { localStorage.setItem(LS_LANG, l) } catch { /* noop */ }
  }, [])

  const t = useCallback((key: string, vars?: Record<string, string | number>): string => {
    const dict = TRANSLATIONS[lang]
    const fallback = TRANSLATIONS.es
    let str = dict[key] ?? fallback[key] ?? key
    if (vars) {
      for (const [k, v] of Object.entries(vars)) {
        str = str.replace(`{${k}}`, String(v))
      }
    }
    return str
  }, [lang])

  const value = useMemo<SettingsCtx>(() => ({ theme, lang, setTheme, setLang, t }), [theme, lang, setTheme, setLang, t])

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export const useSettings = (): SettingsCtx => {
  const v = useContext(Ctx)
  if (!v) {
    // Graceful fallback if used outside provider
    return {
      theme: 'dark',
      lang:  'es',
      setTheme: () => { /* noop */ },
      setLang:  () => { /* noop */ },
      t: (k) => TRANSLATIONS.es[k] ?? k,
    }
  }
  return v
}

export const LANG_META: Record<Lang, { label: string; flag: string }> = {
  es: { label: 'Español',    flag: '🇪🇸' },
  en: { label: 'English',    flag: '🇬🇧' },
  pt: { label: 'Português',  flag: '🇧🇷' },
  fr: { label: 'Français',   flag: '🇫🇷' },
}
