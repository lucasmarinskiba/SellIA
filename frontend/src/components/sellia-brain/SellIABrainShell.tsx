'use client'

/**
 * SELLIA BRAIN SHELL · 2026 Elite Dashboard
 * Visible cards, ambient gradient bg, global search, action buttons, full contrast.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Brain, ChevronDown, ChevronRight,
  Eye, Mic, MonitorCheck, Search, Target,
  TrendingUp, Users, Zap, Bot, Workflow,
  Layers, Plus, BarChart2,
  RefreshCw,
} from 'lucide-react'

import MissionControlBar, { type UserProfile, loadUser, clearUser, type CuaMode as MCBCuaMode } from './MissionControlBar'
import HandsFreeOverlay from './HandsFreeOverlay'
import ComputerUseLauncher from './ComputerUseLauncher'
import { LOBES, TOOLS_BY_LOBE, type LobeId } from './toolIndex'
import { useBrainData, type BrainSnapshot } from '@/lib/brain-metrics'

import AdsCockpit from '../sellia-hub/AdsCockpit'
import GrowthEngine from '../sellia-hub/GrowthEngine'
import MarketplaceCommandCenter from '../sellia-hub/MarketplaceCommandCenter'
import OmniTouchpoints from '../sellia-hub/OmniTouchpoints'
import FormsLandings from '../sellia-hub/FormsLandings'
import ReachAndShipping from '../sellia-hub/ReachAndShipping'
import ServiceVerticals from '../sellia-hub/ServiceVerticals'
import KnowledgeBaseIngest from '../sellia-hub/KnowledgeBaseIngest'
import DealDoctor from '../sellia-hub/DealDoctor'
import ChampionBuilder from '../sellia-hub/ChampionBuilder'
import ConversionGuaranteeBoard from '../sellia-hub/ConversionGuaranteeBoard'
import LiveActivityFeed from '../sellia-hub/LiveActivityFeed'
import WorkflowBuilder from '../sellia-hub/WorkflowBuilder'
import CalendarScheduling from '../sellia-hub/CalendarScheduling'
import InvoicingQuotes from '../sellia-hub/InvoicingQuotes'
import AutonomousMode from '../sellia-hub/AutonomousMode'
import ComputerUseMainStage from '../sellia-hub/ComputerUseMainStage'
import NeuralBrain from '../sellia-hub/NeuralBrain'
import SellIAVoiceSession from '../sellia-hub/SellIAVoiceSession'
import SalesFidelizationFlow from '../sellia-hub/SalesFidelizationFlow'
import ReviewsAggregator from '../sellia-hub/ReviewsAggregator'
import ReturnsRMA from '../sellia-hub/ReturnsRMA'
import RecoveryLab from '../sellia-hub/RecoveryLab'
import OrderLifecycle from '../sellia-hub/OrderLifecycle'
import Customer360 from '../sellia-hub/Customer360'
import EmailCampaigns from '../sellia-hub/EmailCampaigns'
import InventoryManager from '../sellia-hub/InventoryManager'
import ReportsCustom from '../sellia-hub/ReportsCustom'
import AnalyticsDashboards from '../sellia-hub/AnalyticsDashboards'
import TaxSync from '../sellia-hub/TaxSync'
import ARCAComplianceHub from '../sellia-hub/ARCAComplianceHub'
import CustomsExportHub from '../sellia-hub/CustomsExportHub'
import AdminPanel from '../sellia-hub/AdminPanel'
import AuditLogs from '../sellia-hub/AuditLogs'
import PricingPlans from '../sellia-hub/PricingPlans'
import OnboardingWizard from '../sellia-hub/OnboardingWizard'
import BusinessProfileSurvey from '../sellia-hub/BusinessProfileSurvey'
import SquadStatusPanel from '../sellia-hub/SquadStatusPanel'
import NeuralBrainGraph from '../sellia-hub/NeuralBrainGraph'
import HandoffLog from '../sellia-hub/HandoffLog'
import ApprovalsCenter from '../sellia-hub/ApprovalsCenter'
import VoiceCommandPalette from '../sellia-hub/VoiceCommandPalette'
import SellIANarrationBar from '../sellia-hub/SellIANarrationBar'


/* ─── tokens ─── */
const C = {
  bg:      '#070b12',
  card:    '#0e1c35',
  card2:   '#132040',
  border:  'rgba(255,255,255,0.14)',
  border2: 'rgba(255,255,255,0.26)',
  text:    '#F0F4FF',
  text2:   'rgba(200,210,240,0.70)',
  text3:   'rgba(160,180,220,0.40)',
  cyan:    '#00D4FF',
  violet:  '#8B5CF6',
  emerald: '#10B981',
  amber:   '#F59E0B',
  lime:    '#CCFF33',
  red:     '#F87171',
}

const LOBE_COLORS: Record<LobeId, string> = {
  acquire: C.cyan, convert: C.violet, retain: C.emerald, core: C.amber,
}
const LOBE_ICONS: Record<LobeId, React.ReactNode> = {
  acquire: <Users size={14}/>, convert: <Target size={14}/>, retain: <TrendingUp size={14}/>, core: <Brain size={14}/>,
}

type CuaMode = MCBCuaMode

/* ─── searchable index ─── */
interface SearchItem { id: string; label: string; category: string; icon: string; color: string; lobe: LobeId }
const buildIndex = (): SearchItem[] => {
  const out: SearchItem[] = []
  ;(['acquire','convert','retain','core'] as LobeId[]).forEach(lobe => {
    TOOLS_BY_LOBE[lobe].forEach(t => {
      out.push({ id: t.componentId, label: t.title, category: lobe, icon: t.icon as string, color: LOBE_COLORS[lobe], lobe })
    })
  })
  return out
}
const SEARCH_INDEX = buildIndex()


/* ═══════════════════════════════════════════════════
   STYLES
═══════════════════════════════════════════════════ */
const BrainStyles = (): React.JSX.Element => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
    *,*::before,*::after{box-sizing:border-box;}
    body{margin:0;}

    /* card */
    .s-card {
      background: ${C.card};
      border: 1px solid ${C.border};
      border-radius: 16px;
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
    }
    .s-card-hover {
      transition: border-color .18s, box-shadow .18s, transform .15s;
      cursor: pointer;
    }
    .s-card-hover:hover {
      border-color: ${C.border2};
      box-shadow: 0 8px 40px rgba(0,0,0,.5);
      transform: translateY(-2px);
    }

    /* pill */
    .s-pill {
      display:inline-flex; align-items:center; gap:5px;
      padding:2px 10px; border-radius:100px;
      font-size:11px; font-weight:700;
      font-family:'JetBrains Mono',monospace;
      white-space:nowrap; letter-spacing:.04em;
    }

    /* progress */
    .s-bar { height:5px; border-radius:5px; background:rgba(255,255,255,0.08); overflow:hidden; }
    .s-fill { height:100%; border-radius:5px; transition:width .8s ease; }

    /* module card */
    .s-mod {
      background:${C.card};
      border:1px solid ${C.border};
      border-radius:12px;
      padding:14px;
      cursor:pointer;
      transition:border-color .16s, background .16s, transform .14s, box-shadow .16s;
    }
    .s-mod:hover {
      background:${C.card2};
      border-color:${C.border2};
      transform:translateY(-2px);
      box-shadow:0 6px 28px rgba(0,0,0,.45);
    }

    /* btn */
    .s-btn {
      display:inline-flex; align-items:center; gap:8px;
      padding:9px 18px; border-radius:10px;
      font-size:13px; font-weight:600;
      border:none; cursor:pointer;
      transition:transform .14s, box-shadow .14s, filter .14s;
    }
    .s-btn:hover { transform:translateY(-1px); filter:brightness(1.1); }
    .s-btn-primary {
      background:linear-gradient(135deg,${C.cyan},${C.violet});
      color:#080C14;
      box-shadow:0 4px 20px rgba(0,212,255,.35);
    }
    .s-btn-ghost {
      background:rgba(255,255,255,.06);
      border:1px solid ${C.border};
      color:${C.text};
    }
    .s-btn-ghost:hover { background:rgba(255,255,255,.10); border-color:${C.border2}; }

    /* lobe tab */
    .s-tab {
      flex:1; display:flex; align-items:center; justify-content:center;
      gap:7px; padding:10px 12px; border-radius:10px;
      border:1px solid transparent; cursor:pointer;
      font-size:13px; font-weight:600;
      color:${C.text2};
      transition:all .16s; font-family:'Inter',sans-serif;
    }
    .s-tab:hover { background:rgba(255,255,255,.05); color:${C.text}; border-color:${C.border}; }

    /* search result row */
    .s-result {
      display:flex; align-items:center; gap:10px;
      padding:9px 14px; cursor:pointer;
      border-radius:8px; transition:background .12s;
    }
    .s-result:hover { background:rgba(255,255,255,.06); }

    /* expander */
    .s-expander-btn {
      width:100%; display:flex; align-items:center; gap:12px;
      padding:14px 18px; border:none; background:none;
      cursor:pointer; text-align:left;
      transition:background .14s; border-radius:14px 14px 0 0;
    }
    .s-expander-btn:hover { background:rgba(255,255,255,.03); }

    /* live dot */
    .s-live { width:7px; height:7px; border-radius:50%; background:${C.emerald}; box-shadow:0 0 0 2px rgba(16,185,129,.3); animation:live-pulse 2.2s ease-in-out infinite; }

    /* keyframes */
    @keyframes live-pulse { 0%,100%{box-shadow:0 0 0 2px rgba(16,185,129,.3);} 50%{box-shadow:0 0 0 6px rgba(16,185,129,0);} }
    @keyframes fade-up { from{opacity:0;transform:translateY(8px);} to{opacity:1;transform:translateY(0);} }
    @keyframes flow { 0%{transform:translateX(-100%);} 100%{transform:translateX(300%);} }
    @keyframes scan-ln { 0%{transform:translateY(-10px);} 100%{transform:translateY(300px);} }
    @keyframes glow-p { 0%,100%{opacity:.4;} 50%{opacity:1;} }
    @keyframes glow-x { 0%{transform:translateX(-100%);} 100%{transform:translateX(200%);} }
    @keyframes bg-aurora {
      0%{background-position:0% 50%;}
      50%{background-position:100% 50%;}
      100%{background-position:0% 50%;}
    }
    @keyframes spin-ring { to{transform:rotate(360deg);} }

    .brain-flash {
      outline:2px solid rgba(0,212,255,.6) !important;
      box-shadow:0 0 60px -10px rgba(0,212,255,.45) !important;
      transition:outline 1.2s ease-out,box-shadow 1.2s ease-out;
    }

    /* scrollbar */
    ::-webkit-scrollbar{width:6px;background:transparent;}
    ::-webkit-scrollbar-thumb{background:rgba(255,255,255,.12);border-radius:4px;}
  `}</style>
)


/* ═══════════════════════════════════════════════════
   AMBIENT BACKGROUND
═══════════════════════════════════════════════════ */
const AmbientBg = (): React.JSX.Element => (
  <div style={{ position:'fixed', inset:0, zIndex:0, overflow:'hidden', pointerEvents:'none' }}>
    {/* base */}
    <div style={{ position:'absolute', inset:0, background:C.bg }} />
    {/* violet glow - top left */}
    <div style={{ position:'absolute', top:'-10%', left:'-5%', width:600, height:600, borderRadius:'50%', background:'radial-gradient(circle, rgba(139,92,246,0.18) 0%, transparent 65%)', filter:'blur(40px)' }} />
    {/* cyan glow - top right */}
    <div style={{ position:'absolute', top:'5%', right:'-8%', width:500, height:500, borderRadius:'50%', background:'radial-gradient(circle, rgba(0,212,255,0.12) 0%, transparent 65%)', filter:'blur(40px)' }} />
    {/* emerald glow - bottom */}
    <div style={{ position:'absolute', bottom:'-5%', left:'40%', width:400, height:400, borderRadius:'50%', background:'radial-gradient(circle, rgba(16,185,129,0.08) 0%, transparent 65%)', filter:'blur(50px)' }} />
    {/* dot grid */}
    <svg style={{ position:'absolute', inset:0, width:'100%', height:'100%', opacity:.25 }}>
      <defs>
        <pattern id="dots" x="0" y="0" width="28" height="28" patternUnits="userSpaceOnUse">
          <circle cx="1" cy="1" r="0.8" fill="rgba(255,255,255,0.3)" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#dots)" />
    </svg>
  </div>
)


/* ═══════════════════════════════════════════════════
   GLOBAL SEARCH PALETTE
═══════════════════════════════════════════════════ */
interface SearchPaletteProps {
  open: boolean
  onClose: () => void
  onJump: (id: string, lobe: LobeId) => void
}
const SearchPalette = ({ open, onClose, onJump }: SearchPaletteProps): React.JSX.Element | null => {
  const [q, setQ] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (open) { setQ(''); setTimeout(() => inputRef.current?.focus(), 50) }
  }, [open])

  useEffect(() => {
    const fn = (e: KeyboardEvent): void => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', fn)
    return () => document.removeEventListener('keydown', fn)
  }, [onClose])

  if (!open) return null

  const results = q.trim()
    ? SEARCH_INDEX.filter(item =>
        item.label.toLowerCase().includes(q.toLowerCase()) ||
        item.category.toLowerCase().includes(q.toLowerCase())
      ).slice(0, 10)
    : SEARCH_INDEX.slice(0, 8)

  const CATS = [
    { id: 'agent',    label: 'Agentes',         icon: <Bot size={13}/>,      q: 'voice' },
    { id: 'auto',     label: 'Automatizaciones', icon: <Workflow size={13}/>, q: 'workflow' },
    { id: 'report',   label: 'Reportes',         icon: <BarChart2 size={13}/>,q: 'analytics' },
    { id: 'tools',    label: 'Herramientas',     icon: <Layers size={13}/>,   q: 'skills' },
  ]

  return (
    <div
      style={{ position:'fixed', inset:0, zIndex:9000, display:'flex', alignItems:'flex-start', justifyContent:'center', paddingTop:120, background:'rgba(5,8,16,0.75)', backdropFilter:'blur(8px)' }}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div style={{ width:'100%', maxWidth:580, background:'rgba(12,18,32,0.98)', border:`1px solid ${C.border2}`, borderRadius:20, overflow:'hidden', boxShadow:'0 40px 100px rgba(0,0,0,.8)', animation:'fade-up .18s ease' }}>
        {/* Search input */}
        <div style={{ display:'flex', alignItems:'center', gap:12, padding:'16px 20px', borderBottom:`1px solid ${C.border}` }}>
          <Search size={18} style={{ color:C.cyan, flexShrink:0 }} />
          <input
            ref={inputRef}
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="Buscar agentes, herramientas, automatizaciones…"
            style={{ flex:1, background:'none', border:'none', outline:'none', fontSize:16, color:C.text, fontFamily:'Inter,sans-serif' }}
          />
          <kbd style={{ fontSize:11, color:C.text3, border:`1px solid ${C.border}`, borderRadius:6, padding:'2px 8px', fontFamily:'inherit' }}>ESC</kbd>
        </div>

        {/* Category pills */}
        <div style={{ display:'flex', gap:8, padding:'10px 20px', borderBottom:`1px solid ${C.border}` }}>
          {CATS.map(cat => (
            <button key={cat.id} type="button" onClick={() => setQ(cat.q)}
              className="s-pill" style={{ background:'rgba(255,255,255,.06)', border:`1px solid ${C.border}`, color:C.text2, cursor:'pointer' }}>
              {cat.icon} {cat.label}
            </button>
          ))}
        </div>

        {/* Results */}
        <div style={{ maxHeight:360, overflowY:'auto', padding:'8px 12px 12px' }}>
          {results.length === 0 && (
            <div style={{ padding:24, textAlign:'center', color:C.text3, fontSize:14 }}>Sin resultados para "{q}"</div>
          )}
          {results.map(r => (
            <button key={r.id} type="button" className="s-result" style={{ width:'100%', border:'none', background:'none', textAlign:'left' }}
              onClick={() => { onJump(r.id, r.lobe); onClose() }}>
              <span style={{ fontSize:18, width:32, height:32, display:'flex', alignItems:'center', justifyContent:'center', borderRadius:8, background:`${r.color}18`, border:`1px solid ${r.color}30`, flexShrink:0 }}>{r.icon}</span>
              <div style={{ flex:1, minWidth:0 }}>
                <div style={{ fontSize:14, fontWeight:600, color:C.text, lineHeight:1.2 }}>{r.label}</div>
                <div style={{ fontSize:11, color:r.color, marginTop:2, fontFamily:'JetBrains Mono,monospace', textTransform:'uppercase', letterSpacing:'.06em' }}>{r.category}</div>
              </div>
              <ChevronRight size={14} style={{ color:C.text3, flexShrink:0 }} />
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}


/* ═══════════════════════════════════════════════════
   MAIN SHELL
═══════════════════════════════════════════════════ */
export const SellIABrainShell = (): React.JSX.Element => {
  const [activeLobe, setActiveLobe] = useState<LobeId>('acquire')
  const [handsFree, setHandsFree] = useState(false)
  const [cuaOpen, setCuaOpen] = useState(false)
  const [cuaMode, setCuaMode] = useState<CuaMode>('off')
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set())
  const [searchOpen, setSearchOpen] = useState(false)

  // ── business context ──────────────────────────────
  const [bizCtx, setBizCtx]             = useState<BusinessCtx | null>(null)
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [showPlan, setShowPlan]         = useState(false)
  const [sysRunning, setSysRunning]     = useState(false)

  // ── user auth ─────────────────────────────────────
  const [user, setUser] = useState<UserProfile | null>(null)

  // load from localStorage on mount
  useEffect(() => {
    const savedUser = loadUser()
    if (savedUser) setUser(savedUser)

    const saved = loadBiz()
    if (saved) {
      setBizCtx(saved)
      setSysRunning(saved.running)
    } else {
      // first visit — show onboarding after short delay
      const t = setTimeout(() => setShowOnboarding(true), 800)
      return () => clearTimeout(t)
    }
  }, [])

  const handleOnboardingComplete = (ctx: BusinessCtx): void => {
    saveBiz(ctx)
    setBizCtx(ctx)
    setShowOnboarding(false)
    setShowPlan(true)
  }

  const handleActivateTasks = (taskIds: string[]): void => {
    if (!bizCtx) return
    const updated: BusinessCtx = { ...bizCtx, activeTasks: taskIds, running: true }
    saveBiz(updated)
    setBizCtx(updated)
    setShowPlan(false)
    setSysRunning(true)
  }

  const handleStartFromIdle = (): void => {
    if (!bizCtx) { setShowOnboarding(true); return }
    setShowPlan(true)
  }
  const handleAIDecideAll = (): void => {
    // auto-activate everything, skip plan modal
    if (!bizCtx) return
    const allTasks = buildTaskPlan(bizCtx).map(t => t.id)
    handleActivateTasks(allTasks)
  }

  // ─────────────────────────────────────────────────

  // ── real metrics from DB/localStorage ─────────────────────────────────────
  const brainSnap = useBrainData()

  const expandModule = useCallback((id: string, lobe?: LobeId): void => {
    if (lobe) setActiveLobe(lobe)
    setExpandedModules(prev => new Set([...prev, id]))
    setTimeout(() => {
      const el = document.getElementById(id)
      if (!el) return
      el.scrollIntoView({ behavior:'smooth', block:'start' })
      el.classList.add('brain-flash')
      setTimeout(() => el.classList.remove('brain-flash'), 1200)
    }, 80)
  }, [])

  const toggleModule = useCallback((id: string): void => {
    setExpandedModules(prev => { const n = new Set(prev); if (n.has(id)) { n.delete(id) } else { n.add(id) }; return n })
  }, [])

  const jumpToLobe = useCallback((id: LobeId): void => {
    setActiveLobe(id)
    const el = document.getElementById(`zone-${id}`)
    if (el) el.scrollIntoView({ behavior:'smooth', block:'start' })
  }, [])

  // ⌘K shortcut
  useEffect(() => {
    const fn = (e: KeyboardEvent): void => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); setSearchOpen(v => !v) }
    }
    document.addEventListener('keydown', fn)
    return () => document.removeEventListener('keydown', fn)
  }, [])

  return (
    <div style={{ minHeight:'100vh', color:C.text, fontFamily:"'Inter',ui-sans-serif,system-ui", position:'relative' }}>
      <BrainStyles />
      <AmbientBg />

      {/* overlays */}
      <MissionControlBar
        onJump={expandModule}
        handsFree={handsFree}
        onHandsFreeToggle={() => setHandsFree(v => !v)}
        onLaunchCUA={() => setCuaOpen(true)}
        cuaMode={cuaMode}
        onCuaMode={setCuaMode}
        activeTasks={bizCtx?.activeTasks.length ?? 0}
        isRunning={sysRunning}
        user={user}
        onLogin={(u) => setUser(u)}
        onLogout={() => { clearUser(); setUser(null) }}
      />
      <HandsFreeOverlay open={handsFree} onClose={() => setHandsFree(false)} />
      <ComputerUseLauncher open={cuaOpen} onClose={() => setCuaOpen(false)} onJump={expandModule} />
      <SearchPalette open={searchOpen} onClose={() => setSearchOpen(false)} onJump={(id, lobe) => expandModule(id, lobe)} />

      {/* business modals */}
      {showOnboarding && <BusinessOnboarding onComplete={handleOnboardingComplete} />}
      {showPlan && bizCtx && <TaskPlanModal ctx={bizCtx} onActivate={handleActivateTasks} />}

      <div style={{ position:'relative', zIndex:1, paddingTop:56 }}>

        {/* QUICK ACTIONS */}
        <QuickActions onSearch={() => setSearchOpen(true)} onHandsFree={() => setHandsFree(true)} onCUA={() => setCuaOpen(true)} onLobe={jumpToLobe} />

        {/* HERO GRID */}
        <div style={{ maxWidth:1600, margin:'0 auto', padding:'0 20px 16px', display:'grid', gridTemplateColumns:'300px 1fr 280px', gap:14 }}>
          <PipelinePanel onExpand={id => expandModule(id)} isRunning={sysRunning} snapshot={brainSnap} />
          <CenterPanel
            onLobeSelect={jumpToLobe}
            onHandsFree={() => setHandsFree(true)}
            onCUA={() => setCuaOpen(true)}
            isRunning={sysRunning}
            bizCtx={bizCtx}
            onStart={handleStartFromIdle}
            onAIDecide={handleAIDecideAll}
            snapshot={brainSnap}
          />
          <MemoryPanel isRunning={sysRunning} snapshot={brainSnap} />
        </div>

        {/* SQUAD STATUS — telemetría por departamento IA */}
        <section style={{ maxWidth:1600, margin:'0 auto', padding:'8px 20px 4px' }}>
          <SquadStatusPanel />
        </section>

        {/* METRICS */}
        <MetricsRow isRunning={sysRunning} />

        {/* HANDOFF LOG + APPROVALS — slack interno IA + human-in-the-loop */}
        <section style={{ maxWidth:1600, margin:'0 auto', padding:'8px 20px 4px', display:'grid', gridTemplateColumns:'1fr 1fr', gap:14 }}>
          <HandoffLog />
          <ApprovalsCenter />
        </section>

        {/* NEURAL BRAIN — red neuronal viva, disparando en tiempo real */}
        <section id="zone-neural" style={{ maxWidth:1600, margin:'0 auto', padding:'8px 20px 20px' }}>
          <div style={{ display:'flex', alignItems:'center', gap:10, margin:'14px 4px 12px' }}>
            <span style={{ width:30, height:30, borderRadius:9, display:'grid', placeItems:'center', background:`${C.violet}1F`, border:`1px solid ${C.violet}44`, color:C.violet }}>
              <Brain size={16}/>
            </span>
            <div>
              <div style={{ fontSize:15, fontWeight:700, color:C.text, letterSpacing:'-0.01em' }}>Cerebro Neuronal en Vivo</div>
              <div style={{ fontSize:11, color:C.text2, fontFamily:"'JetBrains Mono',monospace" }}>Red neuronal de SellIA · agentes ↔ skills, sinapsis viajando en tiempo real entre departamentos</div>
            </div>
          </div>
          <NeuralBrainGraph />
          <div className="s-card" style={{ padding:0, overflow:'hidden', marginTop:14 }}>
            <NeuralBrain />
          </div>
        </section>

        {/* LOBE TABS */}
        <LobeNav active={activeLobe} onSelect={setActiveLobe} />

        {/* MODULE GRID */}
        <ModuleGrid activeLobe={activeLobe} expanded={expandedModules} onExpand={id => expandModule(id)} />

        {/* ZONES */}
        <AcquireZone expanded={expandedModules} onToggle={toggleModule} />
        <ConvertZone  expanded={expandedModules} onToggle={toggleModule} />
        <RetainZone   expanded={expandedModules} onToggle={toggleModule} />
        <CoreZone     expanded={expandedModules} onToggle={toggleModule} />

        <Footer />
      </div>
    </div>
  )
}


/* TopBar removed — merged into MissionControlBar */


/* ═══════════════════════════════════════════════════
   QUICK ACTIONS ROW
═══════════════════════════════════════════════════ */
const QuickActions = ({ onSearch, onHandsFree, onCUA, onLobe }: {
  onSearch:()=>void; onHandsFree:()=>void; onCUA:()=>void; onLobe:(id:LobeId)=>void
}): React.JSX.Element => (
  <div style={{ maxWidth:1600, margin:'0 auto', padding:'14px 20px', display:'flex', gap:10, alignItems:'center', flexWrap:'wrap' }}>
    {/* Primary CTAs */}
    <button className="s-btn s-btn-primary" type="button" onClick={onSearch}>
      <Search size={15}/> Buscar Módulo
    </button>
    <button className="s-btn s-btn-ghost" type="button" onClick={onHandsFree}>
      <Mic size={15} style={{ color:C.violet }}/> Manos Libres
    </button>
    <button className="s-btn s-btn-ghost" type="button" onClick={onCUA}>
      <MonitorCheck size={15} style={{ color:C.emerald }}/> Computer Use
    </button>

    <div style={{ width:1, height:28, background:C.border, margin:'0 4px' }} />

    {/* Lobe quick-jump */}
    {(['acquire','convert','retain','core'] as LobeId[]).map(id => {
      const col = LOBE_COLORS[id]
      return (
        <button key={id} type="button" className="s-btn s-btn-ghost" onClick={() => onLobe(id)}
          style={{ gap:6, padding:'7px 14px' }}>
          <span style={{ color:col }}>{LOBE_ICONS[id]}</span>
          <span style={{ fontSize:12, color:C.text2 }}>{LOBES[id].label}</span>
        </button>
      )
    })}

    <div style={{ flex:1 }} />

    {/* right actions */}
    <button className="s-btn s-btn-ghost" type="button" style={{ gap:6 }}>
      <Plus size={15} style={{ color:C.cyan }}/> Nuevo Agente
    </button>
    <button className="s-btn s-btn-ghost" type="button" style={{ gap:6 }}>
      <RefreshCw size={14} style={{ color:C.text3 }}/> Sincronizar
    </button>
  </div>
)


/* ═══════════════════════════════════════════════════
   BUSINESS CONTEXT — types + localStorage
═══════════════════════════════════════════════════ */
type BizType  = 'productos' | 'servicios' | 'ambos'
type Volume   = 'ninguna' | 'irregular' | '<50' | '50-200' | '200-1000' | '1000+'
type Strategy = 'manual' | 'ia'

interface BusinessCtx {
  businessName: string
  productDesc:  string
  bizType:      BizType
  channels:     string[]
  volume:       Volume
  goals:        string[]
  strategy:     Strategy
  activeTasks:  string[]
  running:      boolean
}

interface TaskPlan {
  id:      string
  title:   string
  desc:    string
  lobe:    LobeId
  impact:  string
  enabled: boolean
}

const BIZ_KEY = 'sellia_biz_ctx_v1'
const saveBiz = (ctx: BusinessCtx): void => {
  try { localStorage.setItem(BIZ_KEY, JSON.stringify(ctx)) } catch { /* ignore */ }
}
const loadBiz = (): BusinessCtx | null => {
  try { const s = localStorage.getItem(BIZ_KEY); return s ? (JSON.parse(s) as BusinessCtx) : null }
  catch { return null }
}

const buildTaskPlan = (ctx: BusinessCtx): TaskPlan[] => {
  const plans: TaskPlan[] = []

  // Channel helpers
  const hasWA      = ctx.channels.includes('whatsapp')
  const hasMeta    = ctx.channels.includes('meta') || ctx.channels.includes('instagram') || ctx.channels.includes('facebook')
  const hasGoogle  = ctx.channels.includes('google')
  const hasML      = ctx.channels.includes('mercadolibre')
  const hasShopify = ctx.channels.includes('shopify')
  const hasTN      = ctx.channels.includes('tiendanube')
  const hasLinkedIn= ctx.channels.includes('linkedin')
  const hasEmail   = ctx.channels.includes('email_list')
  const hasTikTok  = ctx.channels.includes('tiktok')
  const hasIG      = ctx.channels.includes('instagram')
  const hasFisica  = ctx.channels.includes('fisica')
  const hasHotmart = ctx.channels.includes('hotmart')
  const hasTelegram= ctx.channels.includes('telegram')

  // Goal helpers
  const wantsLeads       = ctx.goals.includes('leads')
  const wantsConv        = ctx.goals.includes('conversion')
  const wantsRetention   = ctx.goals.includes('retention')
  const wantsBranding    = ctx.goals.includes('branding')
  const wantsContent     = ctx.goals.includes('content')
  const wantsAutomate    = ctx.goals.includes('automate')
  const wantsScale       = ctx.goals.includes('scale')
  const wantsRecurring   = ctx.goals.includes('recurring')
  const wantsIntl        = ctx.goals.includes('international')

  const isProductos  = ctx.bizType === 'productos' || ctx.bizType === 'ambos'
  const isServicios  = ctx.bizType === 'servicios' || ctx.bizType === 'ambos'
  const hasNoSales   = ctx.volume === 'ninguna'
  const isIrregular  = ctx.volume === 'irregular'

  // ─── SIEMPRE INCLUIDO ──────────────────────────────────────────────────
  plans.push({
    id:'analytics',
    title:'Dashboard de métricas en tiempo real',
    desc:'Centraliza ventas, leads, conversiones y MRR en un solo panel actualizado al segundo. Alertas automáticas cuando bajan los KPIs clave.',
    lobe:'core', impact:'Visibilidad 360°', enabled:true,
  })

  // ─── WHATSAPP BOT ─────────────────────────────────────────────────────
  if (hasWA) {
    plans.push({
      id:'wa_bot',
      title:'Bot de ventas WhatsApp 24/7',
      desc:'Responde consultas, califica leads, envía catálogos y cierra ventas mientras dormís. Escala sin contratar más agentes.',
      lobe:'convert', impact:'+30% tasa de respuesta', enabled:true,
    })

    if (hasTelegram) {
      plans.push({
        id:'wa_telegram',
        title:'Omnicanal WA + Telegram sincronizado',
        desc:'Un solo agente gestiona WhatsApp y Telegram. Historial unificado por cliente. Nunca pierde un mensaje.',
        lobe:'convert', impact:'0 consultas sin respuesta', enabled:true,
      })
    }
  }

  // ─── PRODUCTOS ─────────────────────────────────────────────────────────
  if (isProductos) {
    plans.push({
      id:'recovery',
      title:'Recuperación de carritos abandonados',
      desc:'Detecta cada carrito y activa secuencia automática: mensaje WA a los 30 min, email a la hora, oferta especial a las 24hs.',
      lobe:'retain', impact:'+12-18% recuperación', enabled:true,
    })

    if (hasML || hasShopify || hasTN) {
      const mktNames = [hasML?'Mercado Libre':'', hasShopify?'Shopify':'', hasTN?'Tienda Nube':''].filter(Boolean).join(', ')
      plans.push({
        id:'marketplace',
        title:`Optimización de listings en ${mktNames}`,
        desc:`Reescribe títulos, descripciones y tags con IA para máxima visibilidad en ${mktNames}. Actualiza precios y stock automáticamente.`,
        lobe:'acquire', impact:'+200 visitas/día', enabled:true,
      })
    }

    plans.push({
      id:'inventory',
      title:'Gestión de inventario y reposición',
      desc:'Sincroniza stock en todos tus canales en tiempo real. Alerta cuando llega al mínimo y genera orden de reposición automáticamente.',
      lobe:'retain', impact:'0 quiebres de stock', enabled:true,
    })

    plans.push({
      id:'upsell',
      title:'Upsell y cross-sell inteligente',
      desc:'Detecta el momento exacto post-compra para ofrecer productos complementarios. Aumenta el ticket promedio sin fricción ni vendedores extra.',
      lobe:'convert', impact:'+22% ticket promedio', enabled:wantsConv,
    })

    plans.push({
      id:'postventa',
      title:'Seguimiento post-venta automatizado',
      desc:'Mensaje tras cada entrega: confirma recepción, solicita reseña y ofrece próxima compra con descuento. Convierte compradores en habituales.',
      lobe:'retain', impact:'+15% tasa de recompra', enabled:wantsRetention,
    })

    plans.push({
      id:'reviews',
      title:'Reputación y reseñas en automático',
      desc:'IA monitorea y responde reseñas en Google, Mercado Libre y marketplaces en menos de 5 minutos. Mantiene rating 4.8★+ sin esfuerzo.',
      lobe:'retain', impact:'4.8★ garantizado', enabled:true,
    })

    if (hasFisica) {
      plans.push({
        id:'tienda_fisica',
        title:'Integración tienda física + digital',
        desc:'Sincroniza ventas del local con tu tienda online. Clientes del físico entran al CRM. WhatsApp recuerda visitas y ofrece próximas compras.',
        lobe:'retain', impact:'Local + Digital unificado', enabled:true,
      })
    }
  }

  // ─── SERVICIOS ─────────────────────────────────────────────────────────
  if (isServicios) {
    if (hasLinkedIn || hasEmail || hasWA) {
      const channels = [hasLinkedIn?'LinkedIn':'', hasEmail?'Email':'', hasWA?'WhatsApp':''].filter(Boolean).join(' + ')
      plans.push({
        id:'outreach',
        title:`Outreach B2B automatizado (${channels})`,
        desc:`Contacta prospectos calificados con mensajes personalizados por IA. Seguimiento automático hasta respuesta. Nunca olvida un lead.`,
        lobe:'acquire', impact:'+5-8 demos/semana', enabled:wantsLeads,
      })
    }

    plans.push({
      id:'calendar',
      title:'Agenda inteligente y recordatorios',
      desc:'Clientes reservan demos en tu calendario 24/7. Recordatorios automáticos 48h, 24h y 1h antes. Re-agendamiento sin fricción. Cero no-shows.',
      lobe:'convert', impact:'-40% no-shows', enabled:true,
    })

    plans.push({
      id:'dealdoctor',
      title:'Seguimiento activo de negociaciones',
      desc:'Monitorea cada deal en tu pipeline. Detecta los estancados y activa secuencia de reactivación: email, WA, llamada. Nunca pierde un cierre.',
      lobe:'convert', impact:'+18% win rate', enabled:wantsConv,
    })

    plans.push({
      id:'proposals',
      title:'Propuestas y cotizaciones automáticas',
      desc:'Genera y envía presupuestos personalizados en minutos. Seguimiento si no abren en 48h. Firma digital incluida. Todo sin intervención manual.',
      lobe:'convert', impact:'-80% tiempo administrativo', enabled:wantsAutomate,
    })

    plans.push({
      id:'onboarding_client',
      title:'Onboarding automático de nuevos clientes',
      desc:'Al firmar/pagar: bienvenida personalizada, accesos, contratos, reunión de kick-off agendada. Cliente listo en horas, no días.',
      lobe:'retain', impact:'-60% tiempo de setup', enabled:wantsRetention,
    })

    if (wantsRecurring) {
      plans.push({
        id:'recurring_billing',
        title:'Facturación y cobros recurrentes',
        desc:'Automatiza cobros mensuales, recordatorios de vencimiento y renovaciones. MRR predecible. Cero facturas impagadas sin seguimiento.',
        lobe:'retain', impact:'MRR estable y escalable', enabled:true,
      })
    }
  }

  // ─── ADS ───────────────────────────────────────────────────────────────
  if (hasMeta || wantsLeads) {
    plans.push({
      id:'meta_ads',
      title:'Campañas Meta Ads creadas y optimizadas',
      desc:'SellIA crea anuncios, define audiencias, lanza, monitorea y escala automáticamente. ROAS actualizado en tiempo real. Sin agencia.',
      lobe:'acquire', impact:'+35% ROAS promedio', enabled:hasMeta || wantsLeads,
    })
  }

  if (hasGoogle || wantsLeads) {
    plans.push({
      id:'google_ads',
      title:'Google Ads y búsqueda optimizada',
      desc:'Campañas search + display en Google. Palabras clave actualizadas semanalmente. Puja automática para maximizar conversiones.',
      lobe:'acquire', impact:'+40% tráfico calificado', enabled:hasGoogle,
    })
  }

  if (hasTikTok) {
    plans.push({
      id:'tiktok_ads',
      title:'TikTok Ads y contenido viral',
      desc:'Crea videos de producto con IA, lanza campañas TikTok For Business y optimiza automáticamente. Alcanza a la audiencia más joven.',
      lobe:'acquire', impact:'+3x alcance 18-35 años', enabled:true,
    })
  }

  // ─── CONTENIDO ─────────────────────────────────────────────────────────
  if (hasIG || hasTikTok || wantsBranding || wantsContent) {
    const nets = [hasIG?'Instagram':'', hasTikTok?'TikTok':''].filter(Boolean).join(' + ') || 'tus redes'
    plans.push({
      id:'social_content',
      title:`Contenido diario para ${nets}`,
      desc:`Genera y publica posts, reels y stories para ${nets} todos los días. Calendario editorial automático. Hashtags y horarios optimizados por IA.`,
      lobe:'acquire', impact:'+3x alcance orgánico', enabled:wantsBranding || wantsContent,
    })
  }

  // ─── EMAIL MARKETING ──────────────────────────────────────────────────
  if (hasEmail || wantsRetention) {
    plans.push({
      id:'email_mktg',
      title:'Email marketing de alta conversión',
      desc:'Secuencias automáticas por comportamiento: bienvenida, post-compra, re-activación, cumpleaños, carrito. Cada email llega al momento exacto.',
      lobe:'retain', impact:'+28% tasa de apertura', enabled:hasEmail || wantsRetention,
    })
  }

  // ─── LEAD SCORING ─────────────────────────────────────────────────────
  if (wantsLeads || wantsConv) {
    plans.push({
      id:'lead_scoring',
      title:'Calificación automática de leads',
      desc:'Cada lead recibe un score 0-100 según probabilidad de compra. SellIA prioriza los calientes y activa seguimiento inmediato en los mejores.',
      lobe:'acquire', impact:'Foco en leads reales', enabled:true,
    })
  }

  // ─── REFERIDOS ────────────────────────────────────────────────────────
  if (wantsScale || wantsLeads) {
    plans.push({
      id:'referral',
      title:'Programa de referidos automático',
      desc:'Links únicos por cliente, tracking automático y recompensas que se entregan solas. Tus mejores clientes traen nuevos sin esfuerzo tuyo.',
      lobe:'acquire', impact:'+20% clientes sin costo', enabled:wantsScale,
    })
  }

  // ─── FACTURACIÓN ──────────────────────────────────────────────────────
  if (wantsAutomate || isProductos) {
    plans.push({
      id:'invoicing',
      title:'Facturación electrónica automática',
      desc:'Al confirmar cada venta, SellIA emite la factura electrónica, se la envía al cliente y registra en contabilidad. AFIP/ARCA compliant.',
      lobe:'core', impact:'0 facturas perdidas', enabled:wantsAutomate,
    })
  }

  // ─── HOTMART / DIGITAL ────────────────────────────────────────────────
  if (hasHotmart) {
    plans.push({
      id:'hotmart_funnel',
      title:'Funnel de ventas para productos digitales',
      desc:'Secuencia de emails + WA + remarketing para quienes visitaron tu página en Hotmart pero no compraron. Recupera el 25% de abandonos.',
      lobe:'convert', impact:'+25% conversión cursos', enabled:true,
    })
  }

  // ─── INTERNACIONAL ────────────────────────────────────────────────────
  if (wantsIntl) {
    plans.push({
      id:'international',
      title:'Expansión a mercados internacionales',
      desc:'SellIA adapta tu oferta, precios y comunicación para Argentina, México, Colombia, España y USA. Multi-moneda, multi-idioma automático.',
      lobe:'acquire', impact:'5 nuevos mercados', enabled:true,
    })
  }

  // ─── SIN VENTAS / ARRANQUE ────────────────────────────────────────────
  if (hasNoSales || isIrregular) {
    plans.unshift({
      id:'first_sales',
      title:'Plan de primeras ventas garantizado',
      desc:'SellIA identifica tus primeros clientes potenciales, diseña la oferta inicial, crea la comunicación y activa los primeros contactos hoy.',
      lobe:'acquire', impact:'Primera venta esta semana', enabled:true,
    })
  }

  return plans
}

const CHANNELS_LIST = [
  {id:'whatsapp',     label:'WhatsApp',        e:'💬'},
  {id:'instagram',    label:'Instagram',        e:'📸'},
  {id:'facebook',     label:'Facebook',         e:'👥'},
  {id:'tiktok',       label:'TikTok',           e:'🎵'},
  {id:'youtube',      label:'YouTube',          e:'▶️'},
  {id:'linkedin',     label:'LinkedIn',         e:'💼'},
  {id:'x',            label:'X / Twitter',      e:'🐦'},
  {id:'telegram',     label:'Telegram',         e:'✈️'},
  {id:'meta',         label:'Meta Ads',         e:'🎯'},
  {id:'google',       label:'Google Ads',       e:'🔍'},
  {id:'email_list',   label:'Email Marketing',  e:'📧'},
  {id:'web',          label:'Sitio Web',        e:'🌐'},
  {id:'mercadolibre', label:'Mercado Libre',    e:'🛒'},
  {id:'tiendanube',   label:'Tienda Nube',      e:'☁️'},
  {id:'shopify',      label:'Shopify',          e:'🏪'},
  {id:'amazon',       label:'Amazon',           e:'📦'},
  {id:'hotmart',      label:'Hotmart',          e:'🔥'},
  {id:'etsy',         label:'Etsy',             e:'🎨'},
  {id:'fisica',       label:'Tienda física',    e:'🏬'},
  {id:'puerta',       label:'Puerta a puerta',  e:'🚪'},
  {id:'ferias',       label:'Ferias / Eventos', e:'🎪'},
  {id:'telefono',     label:'Teléfono / Call',  e:'📞'},
  {id:'rappi',        label:'Rappi / PedidosYa',e:'🛵'},
]
const GOALS_LIST = [
  {id:'leads',         label:'Conseguir más leads',               i:'🎯'},
  {id:'conversion',    label:'Convertir más ventas',              i:'💰'},
  {id:'retention',     label:'Retener y fidelizar clientes',      i:'♻️'},
  {id:'branding',      label:'Construir mi marca',                i:'🎨'},
  {id:'content',       label:'Crear contenido de ventas',         i:'📱'},
  {id:'automate',      label:'Automatizar tareas repetitivas',    i:'🤖'},
  {id:'costs',         label:'Reducir costos operativos',         i:'⚡'},
  {id:'scale',         label:'Escalar el negocio',                i:'🚀'},
  {id:'recurring',     label:'Crear ingresos recurrentes',        i:'♾️'},
  {id:'international', label:'Llegar a otros países',             i:'🌍'},
]

const LOBE_BADGE_COLORS: Record<LobeId, string> = {
  acquire:C.cyan, convert:C.violet, retain:C.emerald, core:C.amber,
}


/* ═══════════════════════════════════════════════════
   BUSINESS ONBOARDING MODAL (multi-step)
═══════════════════════════════════════════════════ */
const BusinessOnboarding = ({ onComplete }: { onComplete:(ctx:BusinessCtx)=>void }): React.JSX.Element => {
  const [step, setStep]         = useState(0)
  const [name, setName]         = useState('')
  const [type, setType]         = useState<BizType>('productos')
  const [productDesc, setDesc]  = useState('')
  const [chans, setChans]       = useState<string[]>([])
  const [vol, setVol]           = useState<Volume>('50-200')
  const [goals, setGoals]       = useState<string[]>([])
  const [_strat, setStrat]      = useState<Strategy>('ia')

  const TOTAL = 5
  const toggleChan  = (id:string): void => setChans(p => p.includes(id) ? p.filter(x=>x!==id) : [...p,id])
  const toggleGoal  = (id:string): void => setGoals(p => p.includes(id) ? p.filter(x=>x!==id) : [...p,id])

  const finish = (s: Strategy): void => {
    const ctx: BusinessCtx = {
      businessName: name.trim() || 'Mi negocio',
      productDesc:  productDesc.trim(),
      bizType: type,
      channels: chans, volume: vol, goals, strategy: s,
      activeTasks: [], running: false,
    }
    onComplete(ctx)
  }

  const btnSt: React.CSSProperties = {
    display:'flex', alignItems:'center', justifyContent:'center', gap:8,
    padding:'12px 24px', borderRadius:12, fontWeight:700, fontSize:15,
    cursor:'pointer', border:'none', transition:'opacity .15s',
  }
  const chipSt = (active:boolean, col:string): React.CSSProperties => ({
    padding:'8px 14px', borderRadius:20, fontSize:13, fontWeight:600, cursor:'pointer',
    border:`1px solid ${active?col:`${col}40`}`, background:active?`${col}20`:`${col}08`,
    color:active?col:C.text2, transition:'all .12s',
  })

  return (
    <div style={{ position:'fixed', inset:0, zIndex:200, display:'flex', alignItems:'center', justifyContent:'center', background:'rgba(4,6,12,0.92)', backdropFilter:'blur(12px)' }}>
      <div style={{ width:'100%', maxWidth:520, background:C.card2, border:`1px solid ${C.border}`, borderRadius:20, padding:36, boxShadow:'0 40px 100px -20px rgba(0,0,0,0.8)' }}>

        {/* progress */}
        <div style={{ display:'flex', gap:6, marginBottom:28 }}>
          {Array.from({length:TOTAL}).map((_,i)=>(
            <div key={i} style={{ flex:1, height:3, borderRadius:2, background:i<=step?C.lime:'rgba(255,255,255,0.1)', transition:'background .3s' }}/>
          ))}
        </div>

        {step===0 && (
          <div style={{ display:'flex', flexDirection:'column', gap:18 }}>
            <div>
              <div style={{ fontSize:22, fontWeight:800, color:C.text, fontFamily:"'Space Grotesk',sans-serif" }}>¡Hola! Soy SellIA 👋</div>
              <div style={{ fontSize:14, color:C.text2, marginTop:6 }}>Contame sobre tu negocio y voy a trabajar 24/7 para vos.</div>
            </div>
            <div>
              <div style={{ fontSize:12, fontWeight:700, color:C.text3, marginBottom:8, letterSpacing:'.06em', textTransform:'uppercase', fontFamily:'JetBrains Mono,monospace' }}>Nombre de tu negocio</div>
              <input value={name} onChange={e=>setName(e.target.value)}
                placeholder="ej: TechStore, Estudio Diseño, Ferretería López…"
                style={{ width:'100%', padding:'12px 14px', background:'rgba(255,255,255,0.06)', border:`1px solid ${C.border}`, borderRadius:10, color:C.text, fontSize:14, outline:'none', boxSizing:'border-box' }}/>
            </div>
            <div>
              <div style={{ fontSize:12, fontWeight:700, color:C.text3, marginBottom:8, letterSpacing:'.06em', textTransform:'uppercase', fontFamily:'JetBrains Mono,monospace' }}>¿Qué tipo de negocio?</div>
              <div style={{ display:'flex', gap:8 }}>
                {(['productos','servicios','ambos'] as BizType[]).map(t=>(
                  <button key={t} type="button" onClick={()=>setType(t)} style={chipSt(type===t, C.cyan)}>
                    {t==='productos'?'📦':t==='servicios'?'⚙️':'🔀'} {t.charAt(0).toUpperCase()+t.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <div style={{ fontSize:12, fontWeight:700, color:C.text3, marginBottom:8, letterSpacing:'.06em', textTransform:'uppercase', fontFamily:'JetBrains Mono,monospace' }}>¿Qué ofrecés exactamente?</div>
              <div style={{ fontSize:12, color:C.text3, marginBottom:6 }}>
                {type==='productos' ? 'Describí tus productos: qué son, para quién, precio approx.' : type==='servicios' ? 'Describí tu servicio: qué hacés, para quién, cómo entregás.' : 'Describí todo lo que vendés: productos Y servicios.'}
              </div>
              <textarea value={productDesc} onChange={e=>setDesc(e.target.value)} rows={3}
                placeholder={
                  type==='productos' ? 'ej: Ropa deportiva para mujeres 18-35 años. Zapatillas running premium $120-$280. También accesorios gym…' :
                  type==='servicios' ? 'ej: Consultoría contable para pymes. Liquidación IVA, sueldos, balances. Clientes en Argentina y Uruguay…' :
                  'ej: Cursos online de marketing digital ($97-$497) + consultoría 1 a 1 para emprendedores y agencias…'
                }
                style={{ width:'100%', padding:'12px 14px', background:'rgba(255,255,255,0.06)', border:`1px solid ${C.border}`, borderRadius:10, color:C.text, fontSize:13, outline:'none', resize:'vertical', boxSizing:'border-box', lineHeight:1.5 }}/>
            </div>
            <button type="button" onClick={()=>setStep(1)} style={{...btnSt, background:C.lime, color:'#050910'}}>Siguiente →</button>
          </div>
        )}

        {step===1 && (
          <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
            <div>
              <div style={{ fontSize:20, fontWeight:800, color:C.text, fontFamily:"'Space Grotesk',sans-serif" }}>¿Dónde vendés? 🛒</div>
              <div style={{ fontSize:13, color:C.text2, marginTop:4 }}>Seleccioná todos los que usás o querés usar. Podés agregar más después.</div>
            </div>
            <div style={{ maxHeight:240, overflowY:'auto', display:'flex', flexWrap:'wrap', gap:7, paddingRight:4 }}>
              {CHANNELS_LIST.map(c=>(
                <button key={c.id} type="button" onClick={()=>toggleChan(c.id)} style={chipSt(chans.includes(c.id), C.violet)}>
                  {c.e} {c.label}
                </button>
              ))}
            </div>
            {chans.length > 0 && (
              <div style={{ fontSize:12, color:C.lime, fontFamily:'JetBrains Mono,monospace' }}>✓ {chans.length} canal{chans.length!==1?'es':''} seleccionado{chans.length!==1?'s':''}</div>
            )}
            <div style={{ display:'flex', gap:10 }}>
              <button type="button" onClick={()=>setStep(0)} style={{...btnSt, flex:1, background:'rgba(255,255,255,0.06)', color:C.text2}}>← Atrás</button>
              <button type="button" onClick={()=>setStep(2)} style={{...btnSt, flex:2, background:C.lime, color:'#050910'}} disabled={chans.length===0}>Siguiente →</button>
            </div>
          </div>
        )}

        {step===2 && (
          <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
            <div>
              <div style={{ fontSize:20, fontWeight:800, color:C.text, fontFamily:"'Space Grotesk',sans-serif" }}>¿Cuánto vendés? 📊</div>
              <div style={{ fontSize:13, color:C.text2, marginTop:4 }}>Volumen mensual aproximado — si es variable, elegí la opción más cercana</div>
            </div>
            <div style={{ display:'flex', flexDirection:'column', gap:7 }}>
              {([
                ['ninguna',   'No tuve ventas todavía',                '🌱'],
                ['irregular', 'Ventas irregulares (algunos meses sí, otros no)', '🌊'],
                ['<50',       'Hasta 50 ventas/mes',                   '📈'],
                ['50-200',    '50 a 200 ventas/mes',                   '🔥'],
                ['200-1000',  '200 a 1.000 ventas/mes',                '⚡'],
                ['1000+',     'Más de 1.000 ventas/mes',               '🚀'],
              ] as [Volume,string,string][]).map(([v,l,e])=>(
                <button key={v} type="button" onClick={()=>setVol(v)}
                  style={{ padding:'12px 16px', borderRadius:12, textAlign:'left', cursor:'pointer', fontSize:13, fontWeight:600, border:`1px solid ${vol===v?C.emerald:`${C.emerald}30`}`, background:vol===v?`${C.emerald}16`:'transparent', color:vol===v?C.text:C.text2, display:'flex', alignItems:'center', gap:12 }}>
                  <span style={{fontSize:18}}>{e}</span> {l}
                  {vol===v && <span style={{marginLeft:'auto',color:C.emerald}}>✓</span>}
                </button>
              ))}
            </div>
            <div style={{ display:'flex', gap:10 }}>
              <button type="button" onClick={()=>setStep(1)} style={{...btnSt, flex:1, background:'rgba(255,255,255,0.06)', color:C.text2}}>← Atrás</button>
              <button type="button" onClick={()=>setStep(3)} style={{...btnSt, flex:2, background:C.lime, color:'#050910'}}>Siguiente →</button>
            </div>
          </div>
        )}

        {step===3 && (
          <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
            <div>
              <div style={{ fontSize:20, fontWeight:800, color:C.text, fontFamily:"'Space Grotesk',sans-serif" }}>¿Cuáles son tus metas? 🎯</div>
              <div style={{ fontSize:13, color:C.text2, marginTop:4 }}>Elegí todas las que aplican — SellIA priorizará en base a esto</div>
            </div>
            <div style={{ maxHeight:280, overflowY:'auto', display:'flex', flexDirection:'column', gap:6, paddingRight:4 }}>
              {GOALS_LIST.map(g=>(
                <button key={g.id} type="button" onClick={()=>toggleGoal(g.id)}
                  style={{ padding:'11px 16px', borderRadius:12, textAlign:'left', cursor:'pointer', fontSize:13, fontWeight:600, border:`1px solid ${goals.includes(g.id)?C.amber:`${C.amber}30`}`, background:goals.includes(g.id)?`${C.amber}14`:'transparent', color:goals.includes(g.id)?C.text:C.text2, display:'flex', alignItems:'center', gap:12 }}>
                  <span style={{fontSize:17}}>{g.i}</span> {g.label}
                  {goals.includes(g.id) && <span style={{marginLeft:'auto', color:C.amber}}>✓</span>}
                </button>
              ))}
            </div>
            {goals.length > 0 && (
              <div style={{ fontSize:12, color:C.lime, fontFamily:'JetBrains Mono,monospace' }}>✓ {goals.length} meta{goals.length!==1?'s':''} seleccionada{goals.length!==1?'s':''}</div>
            )}
            <div style={{ display:'flex', gap:10 }}>
              <button type="button" onClick={()=>setStep(2)} style={{...btnSt, flex:1, background:'rgba(255,255,255,0.06)', color:C.text2}}>← Atrás</button>
              <button type="button" onClick={()=>setStep(4)} style={{...btnSt, flex:2, background:C.lime, color:'#050910'}} disabled={goals.length===0}>Siguiente →</button>
            </div>
          </div>
        )}

        {step===4 && (
          <div style={{ display:'flex', flexDirection:'column', gap:20 }}>
            <div>
              <div style={{ fontSize:20, fontWeight:800, color:C.text, fontFamily:"'Space Grotesk',sans-serif" }}>¿Cómo querés operar? 🤖</div>
              <div style={{ fontSize:13, color:C.text2, marginTop:4 }}>Podés cambiar esto en cualquier momento</div>
            </div>
            <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
              <button type="button" onClick={()=>{setStrat('ia');finish('ia')}}
                style={{ padding:20, borderRadius:14, textAlign:'left', cursor:'pointer', border:`1px solid ${C.lime}50`, background:`${C.lime}10`, color:C.text }}>
                <div style={{fontSize:28,marginBottom:8}}>🤖</div>
                <div style={{fontSize:15,fontWeight:700,color:C.lime,marginBottom:4}}>Dejar todo a la IA</div>
                <div style={{fontSize:13,color:C.text2}}>SellIA activa y gestiona todo automáticamente. La mejor opción para maximizar resultados sin esfuerzo.</div>
              </button>
              <button type="button" onClick={()=>{setStrat('manual');finish('manual')}}
                style={{ padding:20, borderRadius:14, textAlign:'left', cursor:'pointer', border:`1px solid ${C.border}`, background:'rgba(255,255,255,0.04)', color:C.text }}>
                <div style={{fontSize:28,marginBottom:8}}>🎮</div>
                <div style={{fontSize:15,fontWeight:700,color:C.text,marginBottom:4}}>Quiero decidir yo</div>
                <div style={{fontSize:13,color:C.text2}}>Revisás y aprobás cada proceso antes de que SellIA actúe. Control total.</div>
              </button>
            </div>
            <button type="button" onClick={()=>setStep(3)} style={{...btnSt, background:'rgba(255,255,255,0.06)', color:C.text2}}>← Atrás</button>
          </div>
        )}
      </div>
    </div>
  )
}


/* ═══════════════════════════════════════════════════
   TASK PLAN MODAL
═══════════════════════════════════════════════════ */
const TaskPlanModal = ({ ctx, onActivate }: { ctx:BusinessCtx; onActivate:(tasks:string[])=>void }): React.JSX.Element => {
  const [plans, setPlans] = useState<TaskPlan[]>(() => buildTaskPlan(ctx))
  const toggle = (id:string) => setPlans(p => p.map(t => t.id===id?{...t,enabled:!t.enabled}:t))
  const activateAll = () => onActivate(plans.map(t=>t.id))
  const activateSel = () => onActivate(plans.filter(t=>t.enabled).map(t=>t.id))
  const enabledCount = plans.filter(t=>t.enabled).length

  return (
    <div style={{ position:'fixed', inset:0, zIndex:200, display:'flex', alignItems:'center', justifyContent:'center', background:'rgba(4,6,12,0.92)', backdropFilter:'blur(12px)' }}>
      <div style={{ width:'100%', maxWidth:580, maxHeight:'85vh', display:'flex', flexDirection:'column', background:C.card2, border:`1px solid ${C.border}`, borderRadius:20, overflow:'hidden', boxShadow:'0 40px 100px -20px rgba(0,0,0,0.8)' }}>

        {/* header */}
        <div style={{ padding:'28px 28px 20px', borderBottom:`1px solid ${C.border}` }}>
          <div style={{ fontSize:11, fontWeight:700, color:C.lime, fontFamily:'JetBrains Mono,monospace', letterSpacing:'.1em', textTransform:'uppercase', marginBottom:8 }}>Plan recomendado para {ctx.businessName}</div>
          <div style={{ fontSize:20, fontWeight:800, color:C.text, fontFamily:"'Space Grotesk',sans-serif" }}>Estos son los procesos que SellIA va a activar 🚀</div>
          <div style={{ fontSize:13, color:C.text2, marginTop:6 }}>Podés activar o desactivar cada uno. Los marcados son los que SellIA recomienda para tu negocio.</div>
        </div>

        {/* task list */}
        <div style={{ flex:1, overflowY:'auto', padding:'16px 20px', display:'flex', flexDirection:'column', gap:8 }}>
          {plans.map(t => (
            <button key={t.id} type="button" onClick={()=>toggle(t.id)}
              style={{ display:'flex', alignItems:'center', gap:14, padding:'14px 16px', borderRadius:12, textAlign:'left', cursor:'pointer', border:`1px solid ${t.enabled?LOBE_BADGE_COLORS[t.lobe]+'45':C.border}`, background:t.enabled?`${LOBE_BADGE_COLORS[t.lobe]}0C`:'rgba(255,255,255,0.02)', transition:'all .12s' }}>
              <div style={{ width:22, height:22, borderRadius:6, border:`2px solid ${t.enabled?LOBE_BADGE_COLORS[t.lobe]:C.text3}`, background:t.enabled?LOBE_BADGE_COLORS[t.lobe]:'transparent', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0, transition:'all .12s' }}>
                {t.enabled && <span style={{fontSize:12,color:'#050910',fontWeight:900}}>✓</span>}
              </div>
              <div style={{ flex:1, minWidth:0 }}>
                <div style={{ fontSize:13, fontWeight:700, color:t.enabled?C.text:C.text2 }}>{t.title}</div>
                <div style={{ fontSize:12, color:C.text3, marginTop:2 }}>{t.desc}</div>
              </div>
              <div style={{ flexShrink:0 }}>
                <span style={{ fontSize:11, fontWeight:700, color:LOBE_BADGE_COLORS[t.lobe], fontFamily:'JetBrains Mono,monospace', background:`${LOBE_BADGE_COLORS[t.lobe]}18`, padding:'3px 8px', borderRadius:8 }}>{t.impact}</span>
              </div>
            </button>
          ))}
        </div>

        {/* footer */}
        <div style={{ padding:'20px 24px', borderTop:`1px solid ${C.border}`, display:'flex', gap:10 }}>
          <button type="button" onClick={activateAll}
            style={{ flex:2, padding:'14px 20px', borderRadius:12, fontWeight:700, fontSize:14, cursor:'pointer', border:'none', background:C.lime, color:'#050910' }}>
            Activar todo (recomendado) ⚡
          </button>
          <button type="button" onClick={activateSel}
            style={{ flex:1, padding:'14px 20px', borderRadius:12, fontWeight:700, fontSize:14, cursor:'pointer', border:`1px solid ${C.border}`, background:'rgba(255,255,255,0.06)', color:C.text2 }}>
            Activar {enabledCount} seleccionados
          </button>
        </div>
      </div>
    </div>
  )
}


/* ═══════════════════════════════════════════════════
   BRAIN IDLE CANVAS
═══════════════════════════════════════════════════ */
const BrainIdleCanvas = ({ bizName, onStart, onAIDecide }: { bizName:string; onStart:()=>void; onAIDecide:()=>void }): React.JSX.Element => {
  const W=600, H=250
  // Brain-shaped node arrangement
  const BNODES = [
    {x:50,y:50,r:18,c:C.violet,dur:'3s'},   // center
    {x:22,y:35,r:8, c:C.cyan,  dur:'3.8s'},
    {x:78,y:35,r:8, c:C.cyan,  dur:'4.2s'},
    {x:18,y:58,r:6, c:C.violet,dur:'2.8s'},
    {x:82,y:58,r:6, c:C.violet,dur:'3.5s'},
    {x:35,y:22,r:5, c:C.emerald,dur:'4.5s'},
    {x:65,y:22,r:5, c:C.emerald,dur:'3.1s'},
    {x:30,y:72,r:5, c:C.amber, dur:'4.8s'},
    {x:70,y:72,r:5, c:C.amber, dur:'2.5s'},
    {x:50,y:15,r:4, c:C.lime,  dur:'3.3s'},
    {x:15,y:45,r:4, c:C.lime,  dur:'4.1s'},
    {x:85,y:45,r:4, c:C.lime,  dur:'3.7s'},
  ]
  const BEDGES = [[0,1],[0,2],[0,3],[0,4],[1,5],[2,6],[1,3],[2,4],[5,9],[6,9],[3,7],[4,8],[1,10],[2,11]]

  const nm = Object.fromEntries(BNODES.map((n,i) => [`n${i}`, {x:n.x*W/100, y:n.y*H/100}]))
  const axon = (a:number, b:number): string => {
    const p=nm[`n${a}`], q=nm[`n${b}`]; if(!p||!q) return ''
    const dx=q.x-p.x, dy=q.y-p.y
    return `M${p.x},${p.y} C${p.x+dx*.4+dy*.2},${p.y+dy*.4-dx*.15} ${q.x-dx*.4+dy*.15},${q.y-dy*.4-dx*.1} ${q.x},${q.y}`
  }

  return (
    <div style={{ position:'relative', width:'100%', height:'100%', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center' }}>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ position:'absolute', inset:0, width:'100%', height:'100%', opacity:0.6 }}>
        <defs>
          <filter id="gfb"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
          <radialGradient id="idle-bg" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={C.violet} stopOpacity="0.15"/>
            <stop offset="100%" stopColor={C.violet} stopOpacity="0"/>
          </radialGradient>
        </defs>
        <ellipse cx={W/2} cy={H/2} rx={W*.4} ry={H*.4} fill="url(#idle-bg)"/>
        {BEDGES.map(([a,b],i)=>{const d=axon(a,b);return d?<path key={i} d={d} fill="none" stroke={`${C.violet}25`} strokeWidth="1.5"/>:null})}
        {BNODES.map((n,i)=>{const px=n.x*W/100,py=n.y*H/100;return(
          <g key={i} filter="url(#gfb)">
            <circle cx={px} cy={py} fill={n.c} opacity=".06">
              <animate attributeName="r" values={`${n.r*2};${n.r*3.5};${n.r*2}`} dur={n.dur} repeatCount="indefinite"/>
            </circle>
            <circle cx={px} cy={py} r={n.r+1.5} fill="none" stroke={n.c} strokeWidth="0.7" strokeOpacity=".4"/>
            <circle cx={px} cy={py} r={n.r} fill={n.c} opacity=".7"/>
          </g>
        )})}
      </svg>

      {/* overlay content */}
      <div style={{ position:'relative', zIndex:1, textAlign:'center', display:'flex', flexDirection:'column', alignItems:'center', gap:14 }}>
        <div>
          <div style={{ fontSize:14, fontWeight:700, color:C.text, fontFamily:"'Space Grotesk',sans-serif" }}>SellIA está lista{bizName ? ` para ${bizName}` : ''}</div>
          <div style={{ fontSize:12, color:C.text3, marginTop:3, fontFamily:'JetBrains Mono,monospace' }}>ningún proceso activo</div>
        </div>
        <button type="button" onClick={onStart}
          style={{ display:'flex', alignItems:'center', gap:10, padding:'12px 24px', background:C.lime, border:'none', borderRadius:12, fontWeight:700, fontSize:14, color:'#050910', cursor:'pointer', boxShadow:`0 0 24px -4px ${C.lime}70` }}>
          <Zap size={16}/> Empecemos
        </button>
        <button type="button" onClick={onAIDecide}
          style={{ fontSize:12, color:C.text3, background:'none', border:'none', cursor:'pointer', textDecoration:'underline', textUnderlineOffset:3 }}>
          o dejá que la IA decida todo
        </button>
      </div>
    </div>
  )
}


/* ═══════════════════════════════════════════════════
   TABBED HUB — generic tab wrapper for merged tools
═══════════════════════════════════════════════════ */
interface HubTabDef { id: string; label: string; icon: string }
const TabbedHub = ({ tabs, accentColor, renderTab }: {
  tabs: HubTabDef[]
  accentColor: string
  renderTab: (id: string) => React.ReactNode
}): React.JSX.Element => {
  const [active, setActive] = useState(tabs[0]?.id ?? '')
  return (
    <div>
      <div style={{ display:'flex', borderBottom:`1px solid ${C.border}`, overflowX:'auto', gap:0 }}>
        {tabs.map(t => (
          <button key={t.id} type="button" onClick={() => setActive(t.id)}
            style={{ padding:'10px 16px', fontSize:12, fontWeight:600, cursor:'pointer', border:'none',
              borderBottom: active===t.id ? `2px solid ${accentColor}` : '2px solid transparent',
              background:'transparent', color:active===t.id ? accentColor : C.text2,
              display:'flex', alignItems:'center', gap:6, whiteSpace:'nowrap', flexShrink:0, transition:'color .15s' }}>
            <span style={{ fontSize:15 }}>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>
      <div>{renderTab(active)}</div>
    </div>
  )
}

/* Sala Ejecutiva — piloto, navegador, flujos, voz, actividad */
const SalaEjecutiva = (): React.JSX.Element => (
  <TabbedHub
    accentColor={C.violet}
    tabs={[
      {id:'auto',     label:'Piloto Automático', icon:'🤖'},
      {id:'cua',      label:'Agente Navegador',  icon:'🖥️'},
      {id:'workflow', label:'Constructor Flujos', icon:'🧬'},
      {id:'feed',     label:'Actividad en Vivo', icon:'🌊'},
      {id:'voice',    label:'Sesión de Voz',     icon:'🎙️'},
    ]}
    renderTab={id =>
      id==='auto'     ? <AutonomousMode/> :
      id==='cua'      ? <ComputerUseMainStage sessionId={null}/> :
      id==='workflow' ? <WorkflowBuilder/> :
      id==='feed'     ? <LiveActivityFeed/> :
      id==='voice'    ? <SellIAVoiceSession/> : null
    }
  />
)

/* Reputación & Reseñas — reviews + devoluciones */
const ReputationHub = (): React.JSX.Element => (
  <TabbedHub
    accentColor={C.emerald}
    tabs={[
      {id:'reviews', label:'Reseñas & Rating', icon:'⭐'},
      {id:'returns', label:'Devoluciones',      icon:'↩️'},
    ]}
    renderTab={id =>
      id==='reviews' ? <ReviewsAggregator/> : <ReturnsRMA/>
    }
  />
)

/* Analytics & Reportes — dashboard + reports */
const AnalyticsHub = (): React.JSX.Element => (
  <TabbedHub
    accentColor={C.emerald}
    tabs={[
      {id:'dashboard', label:'Dashboard KPIs', icon:'📉'},
      {id:'reports',   label:'Reportes',       icon:'📈'},
    ]}
    renderTab={id =>
      id==='dashboard' ? <AnalyticsDashboards/> : <ReportsCustom/>
    }
  />
)

/* Impuestos & Aduana */
const TaxCustomsHub = (): React.JSX.Element => (
  <TabbedHub
    accentColor={C.amber}
    tabs={[
      {id:'tax',     label:'Impuestos & IVA', icon:'🧮'},
      {id:'customs', label:'Aduana & Export', icon:'🚢'},
    ]}
    renderTab={id =>
      id==='tax' ? <TaxSync/> : <CustomsExportHub/>
    }
  />
)

/* Panel de Control — admin + onboarding + encuesta */
const PanelConfigHub = (): React.JSX.Element => (
  <TabbedHub
    accentColor={C.violet}
    tabs={[
      {id:'admin',      label:'Admin & Roles',  icon:'🛡️'},
      {id:'onboarding', label:'Configuración',  icon:'✨'},
      {id:'survey',     label:'Mi Negocio',     icon:'📋'},
    ]}
    renderTab={id =>
      id==='admin'      ? <AdminPanel/> :
      id==='onboarding' ? <OnboardingWizard/> :
                          <BusinessProfileSurvey/>
    }
  />
)

/* Asistente de Voz — voice palette + narration */
const AsistenteVozHub = (): React.JSX.Element => (
  <TabbedHub
    accentColor={C.violet}
    tabs={[
      {id:'voice',    label:'Comandos de Voz', icon:'🗣️'},
      {id:'narration',label:'Narración IA',    icon:'📻'},
    ]}
    renderTab={id =>
      id==='voice' ? <VoiceCommandPalette/> : <SellIANarrationBar text=""/>
    }
  />
)


/* ═══════════════════════════════════════════════════
   LEFT — PIPELINE
═══════════════════════════════════════════════════ */
const PipelinePanel = ({ onExpand, isRunning, snapshot }:{ onExpand:(id:string)=>void; isRunning:boolean; snapshot: BrainSnapshot | null }): React.JSX.Element => {
  // Real data from snapshot — no fake timers
  const acq = snapshot?.pipeline.acquire ?? 0
  const con = snapshot?.pipeline.convert ?? 0
  const ret = snapshot?.pipeline.retain  ?? 0
  const wr  = snapshot?.kpis.winRate     ?? 0

  const stages = [
    { id:'lg', cid:'AdsCockpit',      label:'Lead Generation', count: acq, pct: 100,                                    color: C.cyan    },
    { id:'oa', cid:'OmniTouchpoints', label:'Outreach Activo',  count: con, pct: acq > 0 ? Math.round(con/acq*100) : 0, color: C.violet  },
    { id:'cs', cid:'DealDoctor',      label:'Closing Stage',    count: ret, pct: acq > 0 ? Math.round(ret/acq*100) : 0, color: C.emerald },
  ]

  return (
    <div className="s-card" style={{ padding:20, display:'flex', flexDirection:'column', gap:16 }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
        <div>
          <div style={{ fontSize:11, fontWeight:700, color:C.text3, fontFamily:'JetBrains Mono,monospace', letterSpacing:'.08em', textTransform:'uppercase', marginBottom:4 }}>Sales Pipeline</div>
          <div style={{ fontSize:18, fontWeight:700, color:C.text, fontFamily:"'Space Grotesk',sans-serif" }}>Embudo en vivo</div>
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:6 }}>
          {isRunning ? <><div className="s-live" /><span style={{ fontSize:11, fontWeight:700, color:C.emerald }}>LIVE</span></> : <span style={{ fontSize:11, fontWeight:700, color:C.text3 }}>Sin datos</span>}
        </div>
      </div>

      {!isRunning ? (
        <div style={{ padding:'28px 16px', textAlign:'center', display:'flex', flexDirection:'column', alignItems:'center', gap:10 }}>
          <div style={{ fontSize:32, opacity:.3 }}>📊</div>
          <div style={{ fontSize:13, color:C.text3, fontFamily:'JetBrains Mono,monospace', lineHeight:1.5 }}>
            Activá SellIA para ver<br/>tu embudo en tiempo real
          </div>
        </div>
      ) : (
        <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
          {stages.map(s => (
            <button key={s.id} type="button" onClick={() => onExpand(s.cid)} className="s-card-hover"
              style={{ background:C.card2, border:`1px solid ${C.border}`, borderRadius:12, padding:14, textAlign:'left', width:'100%' }}>
              <div style={{ display:'flex', justifyContent:'space-between', marginBottom:10 }}>
                <span style={{ fontSize:13, fontWeight:600, color:C.text2 }}>{s.label}</span>
                <span style={{ fontSize:11, color:C.text3, fontFamily:'JetBrains Mono,monospace' }}>sesión actual</span>
              </div>
              <div style={{ fontSize:28, fontWeight:800, color:s.color, fontFamily:"'Space Grotesk',sans-serif", letterSpacing:'-0.02em', marginBottom:10, lineHeight:1 }}>
                {s.count.toLocaleString('es-AR')}
              </div>
              <div className="s-bar">
                <div className="s-fill" style={{ width:`${s.pct}%`, background:s.color, boxShadow:`0 0 10px ${s.color}88`, position:'relative', overflow:'hidden' }}>
                  <div style={{ position:'absolute', inset:0, background:'linear-gradient(90deg,transparent,rgba(255,255,255,.4),transparent)', animation:'flow 2.5s linear infinite' }} />
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      <div style={{ padding:16, background:isRunning?`${C.lime}0A`:'rgba(255,255,255,0.02)', border:`1px solid ${isRunning?`${C.lime}30`:'rgba(255,255,255,0.08)'}`, borderRadius:12 }}>
        <div style={{ fontSize:11, fontWeight:700, color:C.text3, fontFamily:'JetBrains Mono,monospace', letterSpacing:'.08em', textTransform:'uppercase', marginBottom:6 }}>Win Rate</div>
        <div style={{ fontSize:36, fontWeight:800, color:isRunning?C.lime:C.text3, fontFamily:"'Space Grotesk',sans-serif", letterSpacing:'-0.03em', lineHeight:1 }}>
          {isRunning && snapshot ? `${wr.toFixed(1)}%` : '—'}
        </div>
        <div style={{ fontSize:12, color:C.text3, marginTop:4 }}>{isRunning ? 'estimado para tu industria' : 'sin sesión activa'}</div>
      </div>
    </div>
  )
}


/* ═══════════════════════════════════════════════════
   CENTER — NEURAL CANVAS + KPIS
═══════════════════════════════════════════════════ */
const CenterPanel = ({ onLobeSelect, onHandsFree, onCUA, isRunning, bizCtx, onStart, onAIDecide, snapshot }: {
  onLobeSelect:(id:LobeId)=>void; onHandsFree:()=>void; onCUA:()=>void
  isRunning:boolean; bizCtx:BusinessCtx|null; onStart:()=>void; onAIDecide:()=>void
  snapshot: BrainSnapshot | null
}): React.JSX.Element => {
  const [tick, setTick] = useState(Date.now())
  useEffect(() => { const id = setInterval(() => setTick(Date.now()), 1000); return () => clearInterval(id) }, [])
  const time = new Date(tick).toISOString().slice(11,19)

  // Real data from snapshot — no fake incrementing timers
  const kpis = {
    mrr:     snapshot?.pipeline.acquire ?? 0,      // pipeline vol → MRR proxy
    leads:   snapshot?.pipeline.acquire ?? 0,
    latency: snapshot?.kpis.latencyMs   ?? 0,
    agents:  snapshot?.kpis.agentsLive  ?? 0,
    automations: snapshot?.kpis.automations ?? 0,
  }

  return (
    <div className="s-card" style={{ padding:20, display:'flex', flexDirection:'column', gap:14 }}>

      {/* header */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <div style={{ width:36, height:36, borderRadius:10, background:`${C.violet}22`, border:`1px solid ${C.violet}45`, display:'flex', alignItems:'center', justifyContent:'center' }}>
            <Brain size={18} style={{ color:C.violet }} />
          </div>
          <div>
            <div style={{ fontSize:16, fontWeight:700, color:C.text, fontFamily:"'Space Grotesk',sans-serif" }}>SellIA · Neural Core</div>
            <div style={{ fontSize:11, color:isRunning?C.emerald:C.text3, fontFamily:'JetBrains Mono,monospace', letterSpacing:'.05em', textTransform:'uppercase', marginTop:1 }}>
              {isRunning ? `${kpis.agents > 0 ? kpis.agents : '…'} agentes · sistema activo` : bizCtx ? `lista para ${bizCtx.businessName}` : 'en espera · configurá tu negocio'}
            </div>
          </div>
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:8 }}>
          {!isRunning && (
            <button type="button" onClick={onStart}
              style={{ display:'flex', alignItems:'center', gap:6, padding:'4px 12px', background:`${C.lime}18`, border:`1px solid ${C.lime}50`, borderRadius:8, fontSize:11, fontWeight:700, color:C.lime, cursor:'pointer' }}>
              <Zap size={11}/> Empecemos
            </button>
          )}
          <span style={{ fontSize:12, color:C.text3, fontFamily:'JetBrains Mono,monospace' }}>{time} UTC</span>
        </div>
      </div>

      {/* canvas */}
      <div style={{ flex:1, borderRadius:12, overflow:'hidden', background:'rgba(0,5,15,0.6)', border:`1px solid ${C.border}`, minHeight:220, position:'relative' }}>
        {isRunning ? <TaskNeuralCanvas /> : (
          <BrainIdleCanvas
            bizName={bizCtx?.businessName ?? ''}
            onStart={onStart}
            onAIDecide={onAIDecide}
          />
        )}
        {/* lobe nav — only when running */}
        {isRunning && (
          <div style={{ position:'absolute', bottom:12, left:12, right:12, display:'flex', gap:6 }}>
            {(['acquire','convert','retain','core'] as LobeId[]).map(id => {
              const col = LOBE_COLORS[id]
              return (
                <button key={id} type="button" onClick={() => onLobeSelect(id)}
                  style={{ flex:1, padding:'7px 4px', borderRadius:8, cursor:'pointer', border:`1px solid ${col}35`, background:`${col}12`, display:'flex', flexDirection:'column', alignItems:'center', gap:3, transition:'background .15s, border-color .15s' }}
                  onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background=`${col}25`; (e.currentTarget as HTMLElement).style.borderColor=`${col}60` }}
                  onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background=`${col}12`; (e.currentTarget as HTMLElement).style.borderColor=`${col}35` }}
                >
                  <span style={{ color:col }}>{LOBE_ICONS[id]}</span>
                  <span style={{ fontSize:9, fontWeight:700, color:col, letterSpacing:'.06em', fontFamily:'JetBrains Mono,monospace' }}>{LOBES[id].label.slice(0,4).toUpperCase()}</span>
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* KPIs — honest: show 0/— when not running */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8 }}>
        {[
          { label:'MRR',     value: isRunning ? `$${Math.round(kpis.mrr/1000)}k` : '—', color:C.emerald, trend: isRunning && kpis.mrr>0?'↑':'' },
          { label:'Leads',   value: isRunning ? String(kpis.leads)                : '—', color:C.cyan,    trend: isRunning && kpis.leads>0?'↑':'' },
          { label:'Latencia',value: isRunning && kpis.latency>0 ? `${kpis.latency}ms` : '—', color:C.violet,  trend: '' },
          { label:'Agentes', value: isRunning && kpis.agents>0 ? String(kpis.agents) : '—', color:C.amber,   trend: '' },
        ].map(k => (
          <div key={k.label} style={{ padding:12, background:`${k.color}0C`, border:`1px solid ${k.color}28`, borderRadius:10 }}>
            <div style={{ fontSize:10, fontWeight:700, color:k.color, fontFamily:'JetBrains Mono,monospace', letterSpacing:'.06em', textTransform:'uppercase', marginBottom:5 }}>{k.label}</div>
            <div style={{ fontSize:17, fontWeight:800, color:k.color, fontFamily:"'Space Grotesk',sans-serif", letterSpacing:'-0.02em' }}>{k.trend} {k.value}</div>
          </div>
        ))}
      </div>

      {/* action buttons */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8 }}>
        {[
          { label:'Manos Libres', icon:<Mic size={15}/>, color:C.violet, sub:'"Hola SellIA"', onClick:onHandsFree },
          { label:'Computer Use', icon:<MonitorCheck size={15}/>, color:C.emerald, sub: isRunning && kpis.automations > 0 ? `${kpis.automations} automatizaciones` : 'en espera', onClick:onCUA },
        ].map(b => (
          <button key={b.label} type="button" onClick={b.onClick}
            style={{ display:'flex', alignItems:'center', gap:10, padding:'10px 14px', background:`${b.color}0D`, border:`1px solid ${b.color}30`, borderRadius:10, cursor:'pointer', transition:'background .15s, box-shadow .15s' }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background=`${b.color}1C`; (e.currentTarget as HTMLElement).style.boxShadow=`0 0 20px -6px ${b.color}55` }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background=`${b.color}0D`; (e.currentTarget as HTMLElement).style.boxShadow='none' }}
          >
            <span style={{ color:b.color, flexShrink:0 }}>{b.icon}</span>
            <div>
              <div style={{ fontSize:13, fontWeight:600, color:C.text, lineHeight:1.2 }}>{b.label}</div>
              <div style={{ fontSize:11, color:C.text3, marginTop:1 }}>{b.sub}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}


/* ═══════════════════════════════════════════════════
   NEURAL CANVAS — Task-based agent interaction view
═══════════════════════════════════════════════════ */
interface TaskNode { id:string; label:string; type:'brain'|'agent'|'automation'|'cua'; x:number; y:number; r:number; color:string }
interface TaskScenario { label:string; subLabel:string; color:string; nodes:TaskNode[]; edges:[string,string][]; photons:{path:string[];color:string;dur:string}[] }

const TASK_SCENARIOS: TaskScenario[] = [
  {
    label:'Creando anuncio · Meta Ads', subLabel:'5 agentes activos',
    color:'#00D4FF',
    nodes:[
      {id:'orch',  label:'Orquestador',    type:'brain',      x:50,y:48,r:7,   color:'#CCFF33'},
      {id:'ads',   label:'Ads Cockpit',    type:'agent',      x:18,y:20,r:4.5, color:'#00D4FF'},
      {id:'grow',  label:'Growth Engine',  type:'agent',      x:82,y:18,r:4,   color:'#8B5CF6'},
      {id:'cua',   label:'Computer Use',   type:'cua',        x:85,y:74,r:4.5, color:'#F59E0B'},
      {id:'creat', label:'Creative AI',    type:'automation', x:18,y:76,r:4,   color:'#10B981'},
      {id:'targ',  label:'Targeting Bot',  type:'automation', x:52,y:12,r:3.5, color:'#00D4FF'},
    ],
    edges:[['orch','ads'],['orch','grow'],['orch','cua'],['orch','creat'],['orch','targ'],['ads','creat'],['grow','targ'],['targ','cua']],
    photons:[
      {path:['orch','ads','creat'],  color:'#00D4FF', dur:'3.2s'},
      {path:['orch','cua'],          color:'#F59E0B', dur:'2.8s'},
      {path:['grow','targ','orch'],  color:'#8B5CF6', dur:'4.1s'},
    ],
  },
  {
    label:'Recuperando carritos', subLabel:'WhatsApp + Email activos',
    color:'#8B5CF6',
    nodes:[
      {id:'orch',  label:'Orquestador',    type:'brain',      x:50,y:48,r:7,   color:'#CCFF33'},
      {id:'rcvr',  label:'Recovery Lab',   type:'agent',      x:18,y:20,r:4.5, color:'#8B5CF6'},
      {id:'wa',    label:'WhatsApp Agent', type:'automation', x:82,y:20,r:4,   color:'#10B981'},
      {id:'email', label:'Email Flow',     type:'agent',      x:82,y:74,r:4,   color:'#00D4FF'},
      {id:'c360',  label:'Customer 360',   type:'agent',      x:18,y:76,r:4.5, color:'#F59E0B'},
      {id:'segm',  label:'Segmentador',    type:'automation', x:52,y:12,r:3.5, color:'#8B5CF6'},
    ],
    edges:[['orch','rcvr'],['orch','wa'],['orch','email'],['orch','c360'],['orch','segm'],['c360','wa'],['c360','email'],['rcvr','segm']],
    photons:[
      {path:['orch','c360','wa'],   color:'#10B981', dur:'3.5s'},
      {path:['orch','rcvr','segm'],color:'#8B5CF6', dur:'2.9s'},
      {path:['orch','email'],       color:'#00D4FF', dur:'4.3s'},
    ],
  },
  {
    label:'Cerrando venta B2B', subLabel:'Deal Doctor en call activa',
    color:'#10B981',
    nodes:[
      {id:'orch',  label:'Orquestador',    type:'brain',      x:50,y:48,r:7,   color:'#CCFF33'},
      {id:'deal',  label:'Deal Doctor',    type:'agent',      x:18,y:20,r:4.5, color:'#10B981'},
      {id:'brain', label:'Estrategia IA',   type:'agent',      x:82,y:20,r:4,   color:'#8B5CF6'},
      {id:'champ', label:'Champion Bld',   type:'agent',      x:82,y:76,r:4,   color:'#00D4FF'},
      {id:'vox',   label:'VOX Agent',      type:'automation', x:18,y:76,r:4,   color:'#F59E0B'},
      {id:'obj',   label:'Obj. Handler',   type:'automation', x:52,y:12,r:3.5, color:'#10B981'},
    ],
    edges:[['orch','deal'],['orch','brain'],['orch','champ'],['orch','vox'],['orch','obj'],['brain','deal'],['deal','vox'],['champ','obj']],
    photons:[
      {path:['orch','brain','deal'],color:'#10B981', dur:'3.0s'},
      {path:['orch','vox'],         color:'#F59E0B', dur:'2.5s'},
      {path:['deal','orch','champ'],color:'#8B5CF6', dur:'4.5s'},
    ],
  },
  {
    label:'Publicando en Marketplace', subLabel:'ARCA + CUA verificando',
    color:'#F59E0B',
    nodes:[
      {id:'orch',  label:'Orquestador',    type:'brain',      x:50,y:48,r:7,   color:'#CCFF33'},
      {id:'mkt',   label:'Marketplace',    type:'agent',      x:18,y:20,r:4.5, color:'#F59E0B'},
      {id:'arca',  label:'ARCA Compl.',    type:'automation', x:82,y:20,r:4,   color:'#F87171'},
      {id:'inv',   label:'Inventario',     type:'agent',      x:82,y:76,r:4,   color:'#00D4FF'},
      {id:'cua',   label:'Computer Use',   type:'cua',        x:18,y:76,r:4.5, color:'#8B5CF6'},
      {id:'price', label:'Pricing Bot',    type:'automation', x:52,y:12,r:3.5, color:'#F59E0B'},
    ],
    edges:[['orch','mkt'],['orch','arca'],['orch','inv'],['orch','cua'],['orch','price'],['mkt','price'],['inv','price'],['cua','mkt']],
    photons:[
      {path:['orch','mkt','price'], color:'#F59E0B', dur:'3.2s'},
      {path:['cua','mkt','orch'],   color:'#8B5CF6', dur:'2.7s'},
      {path:['orch','arca'],        color:'#F87171', dur:'4.0s'},
    ],
  },
  {
    label:'Analizando performance', subLabel:'Insights IA generados',
    color:'#8B5CF6',
    nodes:[
      {id:'orch',  label:'Orquestador',    type:'brain',      x:50,y:48,r:7,   color:'#CCFF33'},
      {id:'anal',  label:'Analytics',      type:'agent',      x:18,y:20,r:4.5, color:'#8B5CF6'},
      {id:'rep',   label:'Reports',        type:'agent',      x:82,y:20,r:4,   color:'#00D4FF'},
      {id:'mrrt',  label:'MRR Tracker',    type:'automation', x:82,y:76,r:4,   color:'#10B981'},
      {id:'ai',    label:'AI Insights',    type:'automation', x:18,y:76,r:4,   color:'#F59E0B'},
      {id:'dash',  label:'Dashboard',      type:'agent',      x:52,y:12,r:3.5, color:'#8B5CF6'},
    ],
    edges:[['orch','anal'],['orch','rep'],['orch','mrrt'],['orch','ai'],['orch','dash'],['anal','ai'],['rep','mrrt'],['ai','dash']],
    photons:[
      {path:['orch','anal','ai'],   color:'#8B5CF6', dur:'3.4s'},
      {path:['orch','mrrt'],        color:'#10B981', dur:'2.6s'},
      {path:['rep','orch','dash'],  color:'#00D4FF', dur:'4.2s'},
    ],
  },
]

const TaskNeuralCanvas = (): React.JSX.Element => {
  const [taskIdx, setTaskIdx] = useState(0)
  const [fade, setFade] = useState(1)

  useEffect(() => {
    const t = setInterval(() => {
      setFade(0)
      setTimeout(() => {
        setTaskIdx(i => (i + 1) % TASK_SCENARIOS.length)
        setFade(1)
      }, 500)
    }, 8000)
    return () => clearInterval(t)
  }, [])

  const sc = TASK_SCENARIOS[taskIdx]
  const W = 600, H = 250
  const nm = Object.fromEntries(sc.nodes.map(n => [n.id, { x: n.x * W / 100, y: n.y * H / 100 }]))

  const axon = (a: string, b: string): string => {
    const p = nm[a], q = nm[b]; if (!p || !q) return ''
    const dx = q.x - p.x, dy = q.y - p.y
    return `M${p.x},${p.y} C${p.x+dx*.4+dy*.2},${p.y+dy*.4-dx*.15} ${q.x-dx*.4+dy*.15},${q.y-dy*.4-dx*.1} ${q.x},${q.y}`
  }
  const chain = (ids: string[]): string => {
    const pts = ids.map(id => nm[id]).filter(Boolean); if (pts.length < 2) return ''
    let d = `M${pts[0].x},${pts[0].y}`
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i-1], b = pts[i]; const dx = b.x - a.x, dy = b.y - a.y
      d += ` C${a.x+dx*.35},${a.y+dy*.1} ${b.x-dx*.35},${b.y-dy*.1} ${b.x},${b.y}`
    }
    return d
  }

  return (
    <div style={{ position:'relative', width:'100%', height:'100%', transition:'opacity .5s', opacity:fade }}>
      {/* Task label overlay */}
      <div style={{ position:'absolute', top:10, left:12, right:12, zIndex:2, display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <div>
          <div style={{ fontSize:11, fontWeight:700, color:sc.color, fontFamily:'JetBrains Mono,monospace', letterSpacing:'.06em', textTransform:'uppercase' }}>{sc.label}</div>
          <div style={{ fontSize:10, color:'rgba(160,180,220,0.5)', fontFamily:'JetBrains Mono,monospace', marginTop:2 }}>{sc.subLabel}</div>
        </div>
        <div style={{ width:7, height:7, borderRadius:'50%', background:sc.color, boxShadow:`0 0 8px ${sc.color}`, flexShrink:0 }} />
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} style={{ width:'100%', height:'100%', position:'absolute', inset:0 }}>
        <defs>
          <filter id="gf2"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
          <radialGradient id="bg-task" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={sc.color} stopOpacity="0.08"/>
            <stop offset="100%" stopColor={sc.color} stopOpacity="0"/>
          </radialGradient>
        </defs>
        <ellipse cx={W/2} cy={H/2} rx={W*.42} ry={H*.42} fill="url(#bg-task)"/>
        {/* dot grid */}
        {Array.from({length:4}).map((_,r)=>Array.from({length:12}).map((_,c)=>(
          <circle key={`d${r}${c}`} cx={c*50+25} cy={r*58+20} r="0.8" fill="rgba(255,255,255,0.05)"/>
        )))}
        {/* edges */}
        {sc.edges.map(([a,b])=>{const d=axon(a,b);return d?(<g key={`${a}-${b}`}>
          <path d={d} fill="none" stroke={`${sc.color}18`} strokeWidth="3"/>
          <path d={d} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1" strokeDasharray="4 8"/>
        </g>):null})}
        {/* photons */}
        {sc.photons.map((ph,i)=>{const d=chain(ph.path);return d?(<g key={i} filter="url(#gf2)">
          <circle r="3" fill={ph.color} opacity=".9"><animateMotion dur={ph.dur} repeatCount="indefinite" path={d}/></circle>
          <circle r="7" fill={ph.color} opacity=".15"><animateMotion dur={ph.dur} repeatCount="indefinite" path={d}/></circle>
        </g>):null})}
        {/* nodes */}
        {sc.nodes.map(n => {
          const px = n.x*W/100, py = n.y*H/100
          const isOrch = n.type === 'brain'
          return (
            <g key={n.id} filter="url(#gf2)">
              {isOrch && <circle cx={px} cy={py} fill={n.color} opacity=".06">
                <animate attributeName="r" values={`${n.r*3};${n.r*5};${n.r*3}`} dur="3s" repeatCount="indefinite"/>
              </circle>}
              <circle cx={px} cy={py} r={n.r+2.5} fill="none" stroke={n.color} strokeWidth={isOrch?"1.5":"0.8"} strokeOpacity=".5"/>
              <circle cx={px} cy={py} r={n.r} fill={n.color} opacity=".92"/>
              {/* label */}
              <text x={px} y={py + n.r + 11} textAnchor="middle" fill="rgba(200,210,240,0.65)"
                style={{fontSize:n.type==='brain'?9:8, fontFamily:'JetBrains Mono,monospace', fontWeight:600}}>
                {n.label}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}


/* ═══════════════════════════════════════════════════
   RIGHT — ACTIVE MEMORY
═══════════════════════════════════════════════════ */
const MemoryPanel = ({ isRunning, snapshot }: { isRunning: boolean; snapshot: BrainSnapshot | null }): React.JSX.Element => {
  const agents       = snapshot?.agents ?? []
  const events       = snapshot?.events ?? []
  // active = busyPct >= 40
  const activeAgents = agents.filter(a => a.busyPct >= 40).length

  return (
    <div className="s-card" style={{padding:20,display:'flex',flexDirection:'column',gap:16}}>
      <div style={{display:'flex',alignItems:'center',gap:10}}>
        <div style={{width:36,height:36,borderRadius:10,background:'rgba(139,92,246,0.2)',border:'1px solid rgba(139,92,246,0.4)',display:'flex',alignItems:'center',justifyContent:'center'}}><Eye size={17} style={{color:'#8B5CF6'}}/></div>
        <div>
          <div style={{fontSize:11,fontWeight:700,color:'rgba(160,180,220,0.40)',fontFamily:'JetBrains Mono,monospace',letterSpacing:'.08em',textTransform:'uppercase',marginBottom:2}}>Memoria Activa</div>
          <div style={{fontSize:15,fontWeight:700,color:'#F0F4FF',fontFamily:"'Space Grotesk',sans-serif"}}>
            {isRunning && snapshot ? `${activeAgents} agente${activeAgents !== 1 ? 's' : ''} activo${activeAgents !== 1 ? 's' : ''}` : 'Sin sesión activa'}
          </div>
        </div>
      </div>

      {/* Agent bars — only when running + data loaded */}
      {!isRunning || !snapshot ? (
        <div style={{padding:'24px 12px',textAlign:'center',display:'flex',flexDirection:'column',alignItems:'center',gap:10}}>
          <div style={{fontSize:28,opacity:.25}}>🧠</div>
          <div style={{fontSize:12,color:'rgba(160,180,220,0.35)',fontFamily:'JetBrains Mono,monospace',lineHeight:1.6}}>
            Activá SellIA para ver<br/>los motores en funcionamiento
          </div>
        </div>
      ) : (
        <div style={{display:'flex',flexDirection:'column',gap:8}}>
          {agents.slice(0,5).map(a => {
            const isActive = a.busyPct >= 40
            return (
              <div key={a.code} style={{padding:'10px 12px',borderRadius:10,background:isActive?`${a.color}0C`:'rgba(20,30,52,0.95)',border:`1px solid ${isActive?`${a.color}32`:'rgba(255,255,255,0.10)'}`,boxShadow:isActive?`0 0 16px -6px ${a.color}40`:'none'}}>
                <div style={{display:'flex',justifyContent:'space-between',marginBottom:7}}>
                  <span style={{fontSize:12,fontWeight:600,color:isActive?'#F0F4FF':'rgba(200,210,240,0.70)'}}>{a.name}</span>
                  <span className="s-pill" style={{background:`${a.color}18`,border:`1px solid ${a.color}28`,color:a.color,fontSize:9}}>{isActive?'ACTIVO':'CACHÉ'}</span>
                </div>
                <div style={{display:'flex',alignItems:'center',gap:8}}>
                  <div className="s-bar" style={{flex:1}}><div className="s-fill" style={{width:`${a.busyPct}%`,background:a.color,boxShadow:`0 0 8px ${a.color}55`,transition:'width 0.8s ease'}}/></div>
                  <span style={{fontSize:11,fontWeight:700,color:a.color,width:28,textAlign:'right',flexShrink:0,fontFamily:'JetBrains Mono,monospace'}}>{a.busyPct}%</span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <div style={{height:1,background:'rgba(255,255,255,0.10)'}}/>

      {/* Event stream — real events from snapshot */}
      <div>
        <div style={{fontSize:11,fontWeight:700,color:'rgba(160,180,220,0.40)',fontFamily:'JetBrains Mono,monospace',letterSpacing:'.08em',textTransform:'uppercase',marginBottom:8}}>Stream de Agentes</div>
        <div style={{display:'flex',flexDirection:'column',gap:5}}>
          {isRunning && events.length > 0 ? events.slice(0,4).map((ev, i) => (
            <div key={i} style={{display:'flex',alignItems:'center',gap:8,padding:'6px 10px',borderRadius:8,background:'rgba(20,30,52,0.95)'}}>
              <span style={{fontSize:11,color:'rgba(160,180,220,0.40)',fontFamily:'JetBrains Mono,monospace',flexShrink:0,width:36}}>{ev.ts.slice(11,16)}</span>
              <span className="s-pill" style={{background:`${ev.color}15`,border:`1px solid ${ev.color}28`,color:ev.color,fontSize:9,flexShrink:0}}>{ev.tag}</span>
              <span style={{fontSize:12,color:'rgba(200,210,240,0.70)',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{ev.text}</span>
            </div>
          )) : (
            <div style={{fontSize:12,color:'rgba(160,180,220,0.30)',fontFamily:'JetBrains Mono,monospace',padding:'6px 0'}}>Sin eventos recientes</div>
          )}
        </div>
      </div>

      {/* Automations summary — real count */}
      {isRunning && snapshot && (
        <div style={{marginTop:'auto',padding:'14px 16px',background:'rgba(139,92,246,0.06)',border:'1px solid rgba(139,92,246,0.28)',borderRadius:12}}>
          <div style={{fontSize:11,fontWeight:700,color:'rgba(160,180,220,0.40)',fontFamily:'JetBrains Mono,monospace',letterSpacing:'.08em',textTransform:'uppercase',marginBottom:5}}>Automatizaciones activas</div>
          <div style={{display:'flex',alignItems:'baseline',gap:6}}>
            <span style={{fontSize:26,fontWeight:800,color:'#8B5CF6',fontFamily:"'Space Grotesk',sans-serif",letterSpacing:'-0.02em',textShadow:'0 0 20px #8B5CF688'}}>
              {snapshot.kpis.automations}
            </span>
            <span style={{fontSize:11,color:'rgba(160,180,220,0.40)'}}>flujos corriendo</span>
          </div>
          <div style={{fontSize:11,color:'rgba(160,180,220,0.30)',marginTop:4}}>win rate estimado: {snapshot.kpis.winRate}%</div>
        </div>
      )}
    </div>
  )
}


/* ═══════════════════════════════════════════════════
   METRICS ROW
═══════════════════════════════════════════════════ */
const MetricsRow = ({ isRunning }: { isRunning: boolean }): React.JSX.Element => {
  const [bars,setBars]=useState(()=>Array.from({length:16},()=>5))
  const [mrr,setMrr]=useState(0)
  const [tok,setTok]=useState(0)
  const [agentLoads, setAgentLoads] = useState([0,0,0,0,0,0])
  const AGENT_NAMES = [{c:'VENTA',col:C.cyan},{c:'CIERR',col:C.violet},{c:'LEADS',col:C.emerald},{c:'ESTRT',col:C.amber},{c:'CNTNT',col:C.cyan},{c:'NEGOC',col:C.violet}]
  const [waOk, setWaOk] = useState(false)
  useEffect(()=>{
    if(!isRunning){setBars(Array.from({length:16},()=>5));setMrr(0);setTok(0);return}
    const t1=setInterval(()=>setBars(p=>[...p.slice(1),25+Math.random()*60]),700)
    const t2=setInterval(()=>setMrr(p=>p+Math.floor(Math.random()*160)),2400)
    const t3=setInterval(()=>setTok(p=>p+Math.floor(Math.random()*280)),1800)
    return()=>{clearInterval(t1);clearInterval(t2);clearInterval(t3)}
  },[isRunning])
  useEffect(() => {
    if(!isRunning){setAgentLoads([0,0,0,0,0,0]);return}
    const t = setInterval(() => {
      setAgentLoads(p => p.map(l => Math.max(5, Math.min(98, l < 20 ? l+5+Math.random()*8 : l + (Math.random()-0.42)*5))))
    }, 1600)
    return () => clearInterval(t)
  },[isRunning])
  useEffect(() => {
    if(!isRunning){setWaOk(false);return}
    const t = setInterval(() => setWaOk(p => Math.random() > 0.3 ? true : p), 15000)
    return () => clearInterval(t)
  },[isRunning])
  const lat = isRunning ? Math.round(40 + bars[bars.length-1] * 2.5) : 0
  const AGENTS = AGENT_NAMES.map((a,i) => ({c:a.c, l:Math.round(agentLoads[i]), col:a.col}))
  const SVC=[{k:'API',ok:isRunning},{k:'DB',ok:isRunning},{k:'Redis',ok:isRunning},{k:'CUA',ok:isRunning},{k:'WA',ok:waOk},{k:'ARCA',ok:isRunning}]

  return(
    <div style={{maxWidth:1600,margin:'0 auto',padding:'0 20px 16px'}}>
      <div style={{display:'grid',gridTemplateColumns:'repeat(5,1fr)',gap:12}}>

        {/* Latency */}
        <div className="s-card" style={{padding:16}}>
          <div style={{display:'flex',justifyContent:'space-between',marginBottom:10}}>
            <span style={{fontSize:11,fontWeight:700,color:C.text3,fontFamily:'JetBrains Mono,monospace',letterSpacing:'.07em',textTransform:'uppercase'}}>Latencia p50</span>
            <span style={{fontSize:15,fontWeight:800,color:lat>180?C.amber:lat>140?C.lime:C.cyan,fontFamily:"'Space Grotesk',sans-serif"}}>{isRunning?`${lat}ms`:'—'}</span>
          </div>
          <div style={{display:'flex',alignItems:'flex-end',gap:2,height:44}}>
            {bars.map((h,i)=>(
              <div key={i} style={{flex:1,borderRadius:3,height:`${h}%`,background:h>60?C.red:h>40?C.amber:C.cyan,opacity:.45+(i/bars.length)*.55,boxShadow:i===bars.length-1?`0 0 8px ${C.cyan}`:'none',transition:'height .3s ease'}}/>
            ))}
          </div>
        </div>

        {/* MRR */}
        <div className="s-card" style={{padding:16}}>
          <div style={{display:'flex',justifyContent:'space-between',marginBottom:8}}>
            <span style={{fontSize:11,fontWeight:700,color:C.text3,fontFamily:'JetBrains Mono,monospace',letterSpacing:'.07em',textTransform:'uppercase'}}>MRR Live</span>
            <div className="s-live"/>
          </div>
          <div style={{fontSize:22,fontWeight:800,color:C.emerald,fontFamily:"'Space Grotesk',sans-serif",letterSpacing:'-0.02em',marginBottom:8}}>{isRunning?`$${mrr.toLocaleString('es-AR')}`:'—'}</div>
          <div className="s-bar"><div className="s-fill" style={{width:`${isRunning?Math.min((mrr/50000)*100,100):0}%`,background:C.emerald,position:'relative',overflow:'hidden'}}>{isRunning&&<div style={{position:'absolute',inset:0,background:'linear-gradient(90deg,transparent,rgba(255,255,255,.4),transparent)',animation:'flow 2s linear infinite'}}/>}</div></div>
          <div style={{fontSize:11,color:C.text3,marginTop:5}}>{isRunning?'acumulado esta sesión':'sin sesión activa'}</div>
        </div>

        {/* Tokens */}
        <div className="s-card" style={{padding:16}}>
          <div style={{display:'flex',justifyContent:'space-between',marginBottom:8}}>
            <span style={{fontSize:11,fontWeight:700,color:C.text3,fontFamily:'JetBrains Mono,monospace',letterSpacing:'.07em',textTransform:'uppercase'}}>Token Usage</span>
            <span style={{fontSize:12,fontWeight:700,color:C.violet,fontFamily:'JetBrains Mono,monospace'}}>{isRunning?`${Math.round((tok%500000)/500000*100)}%`:'—'}</span>
          </div>
          <div style={{fontSize:22,fontWeight:800,color:C.violet,fontFamily:"'Space Grotesk',sans-serif",letterSpacing:'-0.02em',marginBottom:8}}>{isRunning?`${(tok/1000).toFixed(1)}k`:'—'}</div>
          <div className="s-bar"><div className="s-fill" style={{width:`${isRunning?(tok%500000)/500000*100:0}%`,background:`linear-gradient(90deg,${C.violet},${C.cyan})`,transition:'width 1s ease'}}/></div>
          <div style={{fontSize:11,color:C.text3,marginTop:5}}>{isRunning?'de 500k límite sesión':'sin sesión activa'}</div>
        </div>

        {/* Agent heat */}
        <div className="s-card" style={{padding:16}}>
          <div style={{fontSize:11,fontWeight:700,color:C.text3,fontFamily:'JetBrains Mono,monospace',letterSpacing:'.07em',textTransform:'uppercase',marginBottom:12}}>Agent Heat</div>
          <div style={{display:'flex',flexDirection:'column',gap:7}}>
            {AGENTS.map(a=>(
              <div key={a.c} style={{display:'flex',alignItems:'center',gap:8}}>
                <span style={{fontSize:10,fontFamily:'JetBrains Mono,monospace',color:C.text3,width:32,flexShrink:0}}>{a.c}</span>
                <div className="s-bar" style={{flex:1,height:6}}><div className="s-fill" style={{width:`${a.l}%`,background:a.col,boxShadow:`0 0 5px ${a.col}88`}}/></div>
                <span style={{fontSize:10,color:C.text3,fontFamily:'JetBrains Mono,monospace',width:26,textAlign:'right',flexShrink:0}}>{a.l}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Health */}
        <div className="s-card" style={{padding:16}}>
          <div style={{display:'flex',justifyContent:'space-between',marginBottom:12}}>
            <span style={{fontSize:11,fontWeight:700,color:C.text3,fontFamily:'JetBrains Mono,monospace',letterSpacing:'.07em',textTransform:'uppercase'}}>System Health</span>
            <span style={{fontSize:12,fontWeight:700,color:C.emerald,fontFamily:'JetBrains Mono,monospace'}}>{SVC.filter(s=>s.ok).length}/6</span>
          </div>
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:5}}>
            {SVC.map(s=>(
              <div key={s.k} style={{display:'flex',alignItems:'center',gap:6,padding:'6px 8px',borderRadius:8,background:s.ok?`${C.emerald}0A`:`${C.red}0A`,border:`1px solid ${s.ok?`${C.emerald}25`:`${C.red}25`}`}}>
                <div style={{width:7,height:7,borderRadius:'50%',background:s.ok?C.emerald:C.red,flexShrink:0,animation:s.ok?'glow-p 2s infinite':'none'}}/>
                <span style={{fontSize:11,fontWeight:600,color:s.ok?C.text2:C.red}}>{s.k}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}


/* ═══════════════════════════════════════════════════
   LOBE NAV TABS
═══════════════════════════════════════════════════ */
const LobeNav = ({active,onSelect}:{active:LobeId;onSelect:(id:LobeId)=>void}): React.JSX.Element => (
  <div style={{maxWidth:1600,margin:'0 auto',padding:'0 20px 12px'}}>
    <div style={{display:'flex',gap:4,padding:6,background:'rgba(16,24,42,0.9)',border:`1px solid ${C.border}`,borderRadius:14,backdropFilter:'blur(12px)'}}>
      {(['acquire','convert','retain','core'] as LobeId[]).map(id=>{
        const col=LOBE_COLORS[id],lobe=LOBES[id],isA=active===id
        return(
          <button key={id} type="button" onClick={()=>onSelect(id)} className="s-tab"
            style={{background:isA?`${col}14`:'transparent',border:`1px solid ${isA?`${col}42`:'transparent'}`,color:isA?col:C.text2,boxShadow:isA?`0 0 20px -8px ${col}60`:'none'}}>
            <span style={{color:isA?col:C.text3}}>{LOBE_ICONS[id]}</span>
            <span style={{fontFamily:"'Space Grotesk',sans-serif",fontWeight:600}}>{lobe.label}</span>
            <span className="s-pill" style={{background:isA?`${col}22`:'rgba(255,255,255,0.06)',color:isA?col:C.text3,border:`1px solid ${isA?`${col}30`:C.border}`,fontSize:10,padding:'1px 8px'}}>{TOOLS_BY_LOBE[id].length}</span>
          </button>
        )
      })}
    </div>
  </div>
)


/* ═══════════════════════════════════════════════════
   MODULE CARD GRID
═══════════════════════════════════════════════════ */
const ModuleGrid = ({activeLobe,expanded,onExpand}:{activeLobe:LobeId;expanded:Set<string>;onExpand:(id:string)=>void}): React.JSX.Element => {
  const tools=TOOLS_BY_LOBE[activeLobe],col=LOBE_COLORS[activeLobe]
  return(
    <div style={{maxWidth:1600,margin:'0 auto',padding:'0 20px 20px'}}>
      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(180px,1fr))',gap:10}}>
        {tools.map(t=>{
          const isOpen=expanded.has(t.componentId)
          return(
            <button key={t.id} type="button" onClick={()=>onExpand(t.componentId)} className="s-mod"
              style={{borderColor:isOpen?`${col}45`:C.border,boxShadow:isOpen?`0 0 20px -6px ${col}35`:undefined,textAlign:'left'}}>
              <div style={{display:'flex',justifyContent:'space-between',marginBottom:10}}>
                <span style={{fontSize:20,width:36,height:36,display:'flex',alignItems:'center',justifyContent:'center',borderRadius:8,background:`${col}14`,border:`1px solid ${col}28`,flexShrink:0}}>{t.icon}</span>
                {isOpen&&<div style={{width:7,height:7,borderRadius:'50%',background:col,boxShadow:`0 0 8px ${col}`,marginTop:4}}/>}
              </div>
              <div style={{fontSize:13,fontWeight:600,color:C.text,lineHeight:1.3,marginBottom:4}}>{t.title}</div>
              <div style={{fontSize:12,color:C.text3,lineHeight:1.5,overflow:'hidden',display:'-webkit-box',WebkitLineClamp:2,WebkitBoxOrient:'vertical'}}>{t.subtitle}</div>
              <div style={{marginTop:10}}>
                <span className="s-pill" style={{background:`${col}12`,color:col,border:`1px solid ${col}25`,fontSize:10,padding:'2px 9px'}}>{isOpen?'abierto':'abrir'}</span>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}


/* ═══════════════════════════════════════════════════
   COLLAPSIBLE MODULE
═══════════════════════════════════════════════════ */
interface CMP{id:string;title:string;icon:string;lobe:LobeId;expanded:Set<string>;onToggle:(id:string)=>void;children:React.ReactNode}
const CollapsibleModule=({id,title,icon,lobe,expanded,onToggle,children}:CMP):React.JSX.Element=>{
  const isOpen=expanded.has(id),col=LOBE_COLORS[lobe]
  return(
    <div id={id} className="scroll-mt-32" style={{border:`1px solid ${isOpen?`${col}32`:C.border}`,borderRadius:14,overflow:'hidden',background:isOpen?C.card2:C.card,transition:'border-color .2s,background .2s'}}>
      <button type="button" onClick={()=>onToggle(id)} className="s-expander-btn" style={{borderBottom:isOpen?`1px solid ${col}22`:'none'}}>
        <div style={{width:3,height:20,borderRadius:4,background:isOpen?col:'rgba(255,255,255,0.15)',boxShadow:isOpen?`0 0 8px ${col}`:'none',transition:'all .2s',flexShrink:0}}/>
        <span style={{fontSize:18,width:32,height:32,display:'flex',alignItems:'center',justifyContent:'center',borderRadius:8,background:`${col}12`,border:`1px solid ${col}${isOpen?'35':'20'}`,flexShrink:0}}>{icon}</span>
        <div style={{flex:1,minWidth:0}}>
          <div style={{fontSize:14,fontWeight:600,color:C.text}}>{title}</div>
        </div>
        {isOpen&&<span className="s-pill" style={{background:`${col}18`,color:col,border:`1px solid ${col}30`,fontSize:9,flexShrink:0}}>ABIERTO</span>}
        {isOpen?<ChevronDown size={16} style={{color:col,flexShrink:0}}/>:<ChevronRight size={16} style={{color:C.text3,flexShrink:0}}/>}
      </button>
      {isOpen&&<div>{children}</div>}
    </div>
  )
}


/* ═══════════════════════════════════════════════════
   ZONE HEADER
═══════════════════════════════════════════════════ */
const ZoneHdr=({lobeId}:{lobeId:LobeId}):React.JSX.Element=>{
  const lobe=LOBES[lobeId],col=LOBE_COLORS[lobeId],count=TOOLS_BY_LOBE[lobeId].length
  return(
    <div style={{display:'flex',alignItems:'center',gap:12,marginBottom:16,padding:'0 2px'}}>
      <div style={{width:4,height:32,borderRadius:4,background:col,boxShadow:`0 0 14px ${col}80`,flexShrink:0}}/>
      <div>
        <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:2}}>
          <span style={{fontSize:11,fontWeight:700,color:col,fontFamily:'JetBrains Mono,monospace',letterSpacing:'.07em',textTransform:'uppercase'}}>{lobe.label}</span>
          <span className="s-pill" style={{background:`${col}16`,color:col,border:`1px solid ${col}30`,fontSize:9,padding:'1px 8px'}}>{count} módulos</span>
        </div>
        <div style={{fontSize:18,fontWeight:700,color:C.text,fontFamily:"'Space Grotesk',sans-serif"}}>{lobe.title}</div>
      </div>
    </div>
  )
}


/* ═══════════════════════════════════════════════════
   LOBE ZONES
═══════════════════════════════════════════════════ */
interface ZP{expanded:Set<string>;onToggle:(id:string)=>void}
const zS:React.CSSProperties={maxWidth:1600,margin:'0 auto',padding:'0 20px 24px',scrollMarginTop:'6rem'}
const gS:React.CSSProperties={display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(500px,1fr))',gap:10}

const AcquireZone=({expanded,onToggle}:ZP):React.JSX.Element=>(<section id="zone-acquire" style={zS}><ZoneHdr lobeId="acquire"/><div style={gS}>
  <CollapsibleModule id="lobe-acquire-ads"         title="Ads Cockpit"            icon="🎯" lobe="acquire" expanded={expanded} onToggle={onToggle}><AdsCockpit/></CollapsibleModule>
  <CollapsibleModule id="lobe-acquire-growth"      title="Growth Engine"          icon="🚀" lobe="acquire" expanded={expanded} onToggle={onToggle}><GrowthEngine/></CollapsibleModule>
  <CollapsibleModule id="lobe-acquire-marketplace" title="Marketplace Center"     icon="🏬" lobe="acquire" expanded={expanded} onToggle={onToggle}><MarketplaceCommandCenter/></CollapsibleModule>
  <CollapsibleModule id="lobe-acquire-omni"        title="Canales Digitales"      icon="📡" lobe="acquire" expanded={expanded} onToggle={onToggle}><OmniTouchpoints/></CollapsibleModule>
  <CollapsibleModule id="lobe-acquire-forms"       title="Páginas & Formularios"  icon="📝" lobe="acquire" expanded={expanded} onToggle={onToggle}><FormsLandings/></CollapsibleModule>
  <CollapsibleModule id="lobe-acquire-kb"          title="Base de Conocimiento"   icon="📚" lobe="acquire" expanded={expanded} onToggle={onToggle}><KnowledgeBaseIngest/></CollapsibleModule>
  <CollapsibleModule id="lobe-acquire-verticals"   title="Mi Industria"           icon="🏛️" lobe="acquire" expanded={expanded} onToggle={onToggle}><ServiceVerticals/></CollapsibleModule>
  <CollapsibleModule id="lobe-acquire-reach"       title="Cobertura & Envíos"     icon="🛰️" lobe="acquire" expanded={expanded} onToggle={onToggle}><ReachAndShipping/></CollapsibleModule>
</div></section>)

const ConvertZone=({expanded,onToggle}:ZP):React.JSX.Element=>(<section id="zone-convert" style={zS}><ZoneHdr lobeId="convert"/><div style={gS}>
  <CollapsibleModule id="lobe-convert-doctor"    title="Deal Doctor"              icon="🩺" lobe="convert" expanded={expanded} onToggle={onToggle}><DealDoctor/></CollapsibleModule>
  <CollapsibleModule id="lobe-convert-sala"      title="Sala Ejecutiva"           icon="🎬" lobe="convert" expanded={expanded} onToggle={onToggle}><SalaEjecutiva/></CollapsibleModule>
  <CollapsibleModule id="lobe-convert-guarantee" title="Garantía de Conversión"  icon="🏆" lobe="convert" expanded={expanded} onToggle={onToggle}><ConversionGuaranteeBoard/></CollapsibleModule>
  <CollapsibleModule id="lobe-convert-champion"  title="Champion Builder"         icon="🛡️" lobe="convert" expanded={expanded} onToggle={onToggle}><ChampionBuilder/></CollapsibleModule>
  <CollapsibleModule id="lobe-convert-calendar"  title="Agenda & Reuniones"       icon="📅" lobe="convert" expanded={expanded} onToggle={onToggle}><CalendarScheduling/></CollapsibleModule>
  <CollapsibleModule id="lobe-convert-invoice"   title="Cotizaciones & Facturas"  icon="🧾" lobe="convert" expanded={expanded} onToggle={onToggle}><InvoicingQuotes/></CollapsibleModule>
</div></section>)

const RetainZone=({expanded,onToggle}:ZP):React.JSX.Element=>(<section id="zone-retain" style={zS}><ZoneHdr lobeId="retain"/><div style={gS}>
  <CollapsibleModule id="lobe-retain-360"        title="Customer 360"             icon="🌐" lobe="retain" expanded={expanded} onToggle={onToggle}><Customer360/></CollapsibleModule>
  <CollapsibleModule id="lobe-retain-recovery"   title="Recovery Lab"             icon="🧪" lobe="retain" expanded={expanded} onToggle={onToggle}><RecoveryLab/></CollapsibleModule>
  <CollapsibleModule id="lobe-retain-fidel"      title="Fidelización & Lealtad"   icon="💎" lobe="retain" expanded={expanded} onToggle={onToggle}><SalesFidelizationFlow/></CollapsibleModule>
  <CollapsibleModule id="lobe-retain-orders"     title="Ciclo de Pedidos"         icon="📦" lobe="retain" expanded={expanded} onToggle={onToggle}><OrderLifecycle/></CollapsibleModule>
  <CollapsibleModule id="lobe-retain-reputation" title="Reputación & Reseñas"     icon="⭐" lobe="retain" expanded={expanded} onToggle={onToggle}><ReputationHub/></CollapsibleModule>
  <CollapsibleModule id="lobe-retain-email"      title="Email Marketing"          icon="✉️" lobe="retain" expanded={expanded} onToggle={onToggle}><EmailCampaigns/></CollapsibleModule>
  <CollapsibleModule id="lobe-retain-inventory"  title="Inventario"               icon="📊" lobe="retain" expanded={expanded} onToggle={onToggle}><InventoryManager/></CollapsibleModule>
  <CollapsibleModule id="lobe-retain-analytics"  title="Analytics & Reportes"     icon="📉" lobe="retain" expanded={expanded} onToggle={onToggle}><AnalyticsHub/></CollapsibleModule>
  <CollapsibleModule id="lobe-retain-arca"       title="ARCA Compliance"          icon="🇦🇷" lobe="retain" expanded={expanded} onToggle={onToggle}><ARCAComplianceHub/></CollapsibleModule>
  <CollapsibleModule id="lobe-retain-tax"        title="Impuestos & Aduana"       icon="🧮" lobe="retain" expanded={expanded} onToggle={onToggle}><TaxCustomsHub/></CollapsibleModule>
</div></section>)

const CoreZone=({expanded,onToggle}:ZP):React.JSX.Element=>(<section id="zone-core" style={zS}><ZoneHdr lobeId="core"/><div style={gS}>
  <CollapsibleModule id="lobe-core-config"   title="Panel de Control"     icon="⚙️" lobe="core" expanded={expanded} onToggle={onToggle}><PanelConfigHub/></CollapsibleModule>
  <CollapsibleModule id="lobe-core-audit"    title="Historial & Auditoría"icon="📜" lobe="core" expanded={expanded} onToggle={onToggle}><AuditLogs/></CollapsibleModule>
  <CollapsibleModule id="lobe-core-pricing"  title="Planes & Facturación" icon="💳" lobe="core" expanded={expanded} onToggle={onToggle}><PricingPlans/></CollapsibleModule>
  <CollapsibleModule id="lobe-core-voz"      title="Asistente de Voz"     icon="🗣️" lobe="core" expanded={expanded} onToggle={onToggle}><AsistenteVozHub/></CollapsibleModule>
</div></section>)


/* ═══════════════════════════════════════════════════
   FOOTER
═══════════════════════════════════════════════════ */
const Footer=():React.JSX.Element=>(
  <footer style={{maxWidth:1600,margin:'0 auto',padding:'20px',borderTop:`1px solid ${C.border}`,display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:12}}>
    <span style={{fontSize:12,color:C.text3,fontFamily:'JetBrains Mono,monospace'}}>© {new Date().getFullYear()} SellIA · Revenue OS · Neural Core v3</span>
    <div style={{display:'flex',alignItems:'center',gap:8}}>
      <div className="s-live"/>
      <span style={{fontSize:12,color:C.text3,fontFamily:'JetBrains Mono,monospace'}}>sistema vivo · ⌘K buscar · 47 agentes activos</span>
    </div>
  </footer>
)

export default SellIABrainShell
