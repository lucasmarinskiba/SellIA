'use client'

/**
 * NEURAL BRAIN GRAPH
 *
 * Grafo interactivo con React Flow (@xyflow/react).
 * Agentes = nodos centrales (Ventas, PR, Ads, CS, CUA).
 * Skills = nodos periféricos (Búsqueda web, Email, CRM, etc).
 *
 * "Sinapsis": cuando agente A hace handoff → agente B, viaja un photon
 * luminoso por la edge correspondiente.
 *
 * Backend integration: emit handoff events via WebSocket; call addHandoff(from, to).
 */

import { useEffect, useMemo, useState } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  BackgroundVariant,
  type Node,
  type Edge,
  type NodeProps,
  type EdgeProps,
  Handle,
  Position,
  BaseEdge,
  getSmoothStepPath,
  ReactFlowProvider,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {
  Mail, Megaphone, Radio, Headphones, MonitorCheck,
  Search, Database, Brain, FileText, MessageSquare, Calendar,
} from 'lucide-react'

// ── Design tokens ──────────────────────────────────────────────────────────────
const T = {
  bgApp:    '#0B0F19',
  bgCard:   '#151B2B',
  border:   '#2A3441',
  textPrim: '#F3F4F6',
  textSub:  '#9CA3AF',
  emerald:  '#10B981',
  cyan:     '#06B6D4',
  amber:    '#F59E0B',
  violet:   '#8B5CF6',
  rose:     '#ef4444',
} as const

// ── Custom node types ─────────────────────────────────────────────────────────
interface AgentNodeData extends Record<string, unknown> {
  label:  string
  icon:   React.ElementType
  color:  string
  active: boolean
}

const AgentNode = ({ data }: NodeProps<Node<AgentNodeData>>): React.JSX.Element => {
  const Icon = data.icon
  return (
    <div style={{
      width: 110, height: 110, borderRadius: 22,
      background: `radial-gradient(circle at 50% 40%, ${data.color}22, ${T.bgCard} 75%)`,
      border: `1.5px solid ${data.color}${data.active ? 'cc' : '50'}`,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap: 6,
      boxShadow: data.active
        ? `0 0 30px -4px ${data.color}80, inset 0 0 16px ${data.color}25`
        : `0 0 12px -4px ${data.color}40`,
      position: 'relative',
    }}>
      <Handle type="source" position={Position.Top}    style={{ opacity: 0, pointerEvents: 'none' }} id="t" />
      <Handle type="source" position={Position.Right}  style={{ opacity: 0, pointerEvents: 'none' }} id="r" />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0, pointerEvents: 'none' }} id="b" />
      <Handle type="source" position={Position.Left}   style={{ opacity: 0, pointerEvents: 'none' }} id="l" />
      <Handle type="target" position={Position.Top}    style={{ opacity: 0, pointerEvents: 'none' }} id="tt" />
      <Handle type="target" position={Position.Right}  style={{ opacity: 0, pointerEvents: 'none' }} id="tr" />
      <Handle type="target" position={Position.Bottom} style={{ opacity: 0, pointerEvents: 'none' }} id="tb" />
      <Handle type="target" position={Position.Left}   style={{ opacity: 0, pointerEvents: 'none' }} id="tl" />

      <Icon size={26} style={{ color: data.color, filter: `drop-shadow(0 0 6px ${data.color}99)` }} />
      <div style={{ fontSize: 11, fontWeight: 700, color: T.textPrim, textAlign: 'center', fontFamily: "'Space Grotesk',sans-serif", lineHeight: 1.1 }}>
        {data.label}
      </div>
    </div>
  )
}

interface SkillNodeData extends Record<string, unknown> {
  label: string
  icon:  React.ElementType
  color: string
}

const SkillNode = ({ data }: NodeProps<Node<SkillNodeData>>): React.JSX.Element => {
  const Icon = data.icon
  return (
    <div style={{
      padding: '7px 11px', borderRadius: 14,
      background: T.bgCard,
      border: `1px solid ${data.color}45`,
      display: 'flex', alignItems: 'center', gap: 7,
      boxShadow: `0 0 10px -3px ${data.color}30`,
    }}>
      <Handle type="source" position={Position.Left}  style={{ opacity: 0, pointerEvents: 'none' }} />
      <Handle type="target" position={Position.Left}  style={{ opacity: 0, pointerEvents: 'none' }} id="tl" />
      <Handle type="source" position={Position.Right} style={{ opacity: 0, pointerEvents: 'none' }} id="r" />
      <Handle type="target" position={Position.Right} style={{ opacity: 0, pointerEvents: 'none' }} id="tr" />

      <Icon size={12} style={{ color: data.color }} />
      <span style={{ fontSize: 10, fontWeight: 600, color: T.textPrim, fontFamily: 'JetBrains Mono,monospace' }}>
        {data.label}
      </span>
    </div>
  )
}

// ── Synapse edge — luminous photon traveling along path ────────────────────────
interface SynapseEdgeData extends Record<string, unknown> {
  color:  string
  active: boolean
}

const SynapseEdge = (props: EdgeProps<Edge<SynapseEdgeData>>): React.JSX.Element => {
  const { id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data } = props
  const [edgePath] = getSmoothStepPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition, borderRadius: 16 })
  const color = data?.color ?? T.cyan
  const active = data?.active ?? false

  return (
    <>
      <BaseEdge id={id} path={edgePath} style={{ stroke: `${color}30`, strokeWidth: 1.2 }} />
      {active && (
        <>
          <path d={edgePath} fill="none" stroke={color} strokeWidth={2.2} opacity={0.7}
            style={{ filter: `drop-shadow(0 0 6px ${color})` }} />
          <circle r={4} fill={color} style={{ filter: `drop-shadow(0 0 10px ${color})` }}>
            <animateMotion dur="1.4s" repeatCount="indefinite" path={edgePath} />
          </circle>
        </>
      )}
    </>
  )
}

// ── Graph definition ──────────────────────────────────────────────────────────
const AGENTS: { id: string; label: string; icon: React.ElementType; color: string; pos: { x: number; y: number } }[] = [
  { id: 'sdr', label: 'SDR',     icon: Mail,          color: T.cyan,    pos: { x: 200, y: 80  } },
  { id: 'ads', label: 'Ads',     icon: Megaphone,     color: T.amber,   pos: { x: 480, y: 80  } },
  { id: 'pr',  label: 'PR',      icon: Radio,         color: T.violet,  pos: { x: 200, y: 320 } },
  { id: 'cs',  label: 'CS',      icon: Headphones,    color: T.emerald, pos: { x: 480, y: 320 } },
  { id: 'cua', label: 'CUA',     icon: MonitorCheck,  color: T.rose,    pos: { x: 340, y: 200 } },
]

const SKILLS: { id: string; label: string; icon: React.ElementType; color: string; pos: { x: number; y: number } }[] = [
  { id: 'sk_web',   label: 'Búsqueda Web', icon: Search,        color: T.cyan,    pos: { x: 20,  y: 30  } },
  { id: 'sk_mail',  label: 'Email',        icon: Mail,          color: T.cyan,    pos: { x: 20,  y: 130 } },
  { id: 'sk_crm',   label: 'CRM',          icon: Database,      color: T.emerald, pos: { x: 670, y: 30  } },
  { id: 'sk_kb',    label: 'Knowledge',    icon: Brain,         color: T.violet,  pos: { x: 670, y: 130 } },
  { id: 'sk_docs',  label: 'Docs / PDFs',  icon: FileText,      color: T.amber,   pos: { x: 670, y: 230 } },
  { id: 'sk_chat',  label: 'WhatsApp',     icon: MessageSquare, color: T.emerald, pos: { x: 670, y: 330 } },
  { id: 'sk_cal',   label: 'Calendar',     icon: Calendar,      color: T.violet,  pos: { x: 20,  y: 230 } },
  { id: 'sk_voice', label: 'Voice',        icon: MessageSquare, color: T.rose,    pos: { x: 20,  y: 330 } },
]

// ── Initial edges ─────────────────────────────────────────────────────────────
const baseEdges: Edge<SynapseEdgeData>[] = [
  // Skills → Agents
  { id: 'e_web_sdr',   source: 'sk_web',  target: 'sdr', type: 'synapse', data: { color: T.cyan,    active: false } },
  { id: 'e_mail_sdr',  source: 'sk_mail', target: 'sdr', type: 'synapse', data: { color: T.cyan,    active: false } },
  { id: 'e_crm_ads',   source: 'sk_crm',  target: 'ads', type: 'synapse', data: { color: T.amber,   active: false } },
  { id: 'e_kb_ads',    source: 'sk_kb',   target: 'ads', type: 'synapse', data: { color: T.amber,   active: false } },
  { id: 'e_docs_cs',   source: 'sk_docs', target: 'cs',  type: 'synapse', data: { color: T.emerald, active: false } },
  { id: 'e_chat_cs',   source: 'sk_chat', target: 'cs',  type: 'synapse', data: { color: T.emerald, active: false } },
  { id: 'e_cal_pr',    source: 'sk_cal',  target: 'pr',  type: 'synapse', data: { color: T.violet,  active: false } },
  { id: 'e_voice_cua', source: 'sk_voice', target: 'cua', type: 'synapse', data: { color: T.rose,   active: false } },

  // Agent ↔ Agent handoff edges (always present, photon shows when active)
  { id: 'h_pr_sdr',  source: 'pr',  target: 'sdr', type: 'synapse', data: { color: T.violet,  active: false } },
  { id: 'h_sdr_ads', source: 'sdr', target: 'ads', type: 'synapse', data: { color: T.cyan,    active: false } },
  { id: 'h_ads_cs',  source: 'ads', target: 'cs',  type: 'synapse', data: { color: T.amber,   active: false } },
  { id: 'h_cs_cua',  source: 'cs',  target: 'cua', type: 'synapse', data: { color: T.emerald, active: false } },
  { id: 'h_cua_sdr', source: 'cua', target: 'sdr', type: 'synapse', data: { color: T.rose,    active: false } },
]

// Demo handoff sequence — rotates through agent pairs
const DEMO_SEQ = ['h_pr_sdr', 'h_sdr_ads', 'h_ads_cs', 'h_cs_cua', 'h_cua_sdr'] as const

// ── Main component ────────────────────────────────────────────────────────────
const nodeTypes = { agent: AgentNode, skill: SkillNode }
const edgeTypes = { synapse: SynapseEdge }

const NeuralBrainGraphInner = (): React.JSX.Element => {
  const [activeEdges, setActiveEdges] = useState<Set<string>>(new Set())
  const [activeAgents, setActiveAgents] = useState<Set<string>>(new Set(['sdr', 'ads']))

  // Build nodes
  const nodes: Node[] = useMemo(() => [
    ...AGENTS.map(a => ({
      id: a.id,
      type: 'agent',
      position: a.pos,
      data: { label: a.label, icon: a.icon, color: a.color, active: activeAgents.has(a.id) },
    })),
    ...SKILLS.map(s => ({
      id: s.id,
      type: 'skill',
      position: s.pos,
      data: { label: s.label, icon: s.icon, color: s.color },
    })),
  ], [activeAgents])

  // Build edges with active state
  const edges: Edge[] = useMemo(() =>
    baseEdges.map(e => ({
      ...e,
      data: { ...e.data!, active: activeEdges.has(e.id) },
    }))
  , [activeEdges])

  // Demo handoff simulation — replace with WebSocket subscription
  useEffect(() => {
    let step = 0
    const id = setInterval(() => {
      const edgeId = DEMO_SEQ[step % DEMO_SEQ.length]
      step++

      // Activate edge + source/target agents
      const edge = baseEdges.find(e => e.id === edgeId)
      if (!edge) return

      setActiveEdges(p => new Set(p).add(edgeId))
      setActiveAgents(p => new Set(p).add(edge.source).add(edge.target))

      // Deactivate after photon transit (~2s)
      setTimeout(() => {
        setActiveEdges(p => {
          const next = new Set(p)
          next.delete(edgeId)
          return next
        })
      }, 2200)
    }, 2800)
    return () => clearInterval(id)
  }, [])

  // ── Public API: trigger a handoff from backend ─────────────────────────────
  // const triggerHandoff = useCallback((edgeId: string, durMs = 2200) => {
  //   setActiveEdges(p => new Set(p).add(edgeId))
  //   setTimeout(() => setActiveEdges(p => { const n = new Set(p); n.delete(edgeId); return n }), durMs)
  // }, [])

  return (
    <div style={{
      width: '100%',
      height: 460,
      background: T.bgApp,
      border: `1px solid ${T.border}`,
      borderRadius: 14,
      overflow: 'hidden',
      position: 'relative',
    }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        proOptions={{ hideAttribution: true }}
        minZoom={0.5}
        maxZoom={1.5}
      >
        <Background variant={BackgroundVariant.Dots} gap={18} size={1} color={`${T.border}99`} />
        <Controls position="bottom-right" showInteractive={false}
          style={{ background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 8 }} />
      </ReactFlow>

      {/* Legend overlay */}
      <div style={{ position: 'absolute', top: 10, left: 10, padding: '6px 10px', background: `${T.bgCard}cc`, border: `1px solid ${T.border}`, borderRadius: 8, backdropFilter: 'blur(8px)' }}>
        <div style={{ fontSize: 10, color: T.textSub, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.05em', textTransform: 'uppercase' }}>
          Cerebro Neuronal · {activeEdges.size} sinapsis activas
        </div>
      </div>
    </div>
  )
}

// Provider wrapper required by React Flow
export default function NeuralBrainGraph(): React.JSX.Element {
  return (
    <ReactFlowProvider>
      <NeuralBrainGraphInner />
    </ReactFlowProvider>
  )
}

