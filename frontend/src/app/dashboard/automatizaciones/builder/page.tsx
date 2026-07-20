'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Panel,
  Connection,
  Handle,
  Position,
  useReactFlow,
  ReactFlowProvider,
  type Node as FlowNode,
  type Edge as FlowEdge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft, Play, Mail, MessageSquare, Bot, Clock, Tag,
  Globe, GitBranch, Zap, Save, Trash2, Plus, MousePointer2,
  Loader2, Check, X
} from 'lucide-react'
import { cn } from '@/lib/utils'
import Button from '@/components/ui/Button'
import { automationsApi } from '@/lib/automations'
import { businessApi } from '@/lib/business'

/* ============================================================
   WORKFLOW VISUAL BUILDER — React Flow Canvas
   ============================================================ */

type NodeType = 'trigger' | 'action' | 'wait'

interface NodeData extends Record<string, any> {
  label: string
  type: string
  config: Record<string, any>
  icon?: any
  color?: string
}

const triggerTypes = [
  { type: 'new_lead', label: 'Nuevo Lead', icon: Plus, color: '#22C55E' },
  { type: 'new_message', label: 'Nuevo Mensaje', icon: MessageSquare, color: '#3B82F6' },
  { type: 'cart_abandoned', label: 'Carrito Abandonado', icon: Trash2, color: '#EF4444' },
  { type: 'appointment_missed', label: 'Cita No-Show', icon: Clock, color: '#F59E0B' },
  { type: 'tag_added', label: 'Tag Agregado', icon: Tag, color: '#8B5CF6' },
  { type: 'time_delay', label: 'Delay Programado', icon: Clock, color: '#64748B' },
]

const actionTypes = [
  { type: 'send_message', label: 'Enviar Mensaje', icon: MessageSquare, color: '#00D4AA' },
  { type: 'send_email', label: 'Enviar Email', icon: Mail, color: '#0EA5E9' },
  { type: 'ai_reply', label: 'Respuesta IA', icon: Bot, color: '#FF6B35' },
  { type: 'add_tag', label: 'Agregar Tag', icon: Tag, color: '#8B5CF6' },
  { type: 'wait', label: 'Esperar', icon: Clock, color: '#64748B' },
  { type: 'webhook', label: 'Webhook', icon: Globe, color: '#EC4899' },
  { type: 'move_stage', label: 'Mover Etapa', icon: GitBranch, color: '#F59E0B' },
]

function TriggerNode({ data, selected }: { data: NodeData; selected?: boolean }) {
  const Icon = data.icon || Zap
  return (
    <div className={cn(
      "relative px-4 py-3 rounded-xl border-2 min-w-[180px] transition-all",
      selected ? 'border-white/30 shadow-lg' : 'border-white/10'
    )} style={{ background: `${data.color}15` }}>
      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-white/50 !border-2" style={{ borderColor: data.color }} />
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${data.color}25` }}>
          <Icon className="w-4 h-4" style={{ color: data.color }} />
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-white/40">Trigger</p>
          <p className="text-sm font-medium text-white">{data.label}</p>
        </div>
      </div>
    </div>
  )
}

function ActionNode({ data, selected }: { data: NodeData; selected?: boolean }) {
  const Icon = data.icon || Play
  return (
    <div className={cn(
      "relative px-4 py-3 rounded-xl border-2 min-w-[180px] transition-all",
      selected ? 'border-white/30 shadow-lg' : 'border-white/10'
    )} style={{ background: `${data.color}10` }}>
      <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-white/50 !border-2" style={{ borderColor: data.color }} />
      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-white/50 !border-2" style={{ borderColor: data.color }} />
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${data.color}20` }}>
          <Icon className="w-4 h-4" style={{ color: data.color }} />
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-white/40">Acción</p>
          <p className="text-sm font-medium text-white">{data.label}</p>
        </div>
      </div>
      {data.config?.personality && (
        <p className="text-[10px] text-white/30 mt-1.5 ml-10.5">🤖 {data.config.personality}</p>
      )}
      {data.config?.delay && (
        <p className="text-[10px] text-white/30 mt-1.5 ml-10.5">⏱ {data.config.delay}</p>
      )}
    </div>
  )
}

function WaitNode({ data, selected }: { data: NodeData; selected?: boolean }) {
  return (
    <div className={cn(
      "relative px-4 py-3 rounded-xl border-2 min-w-[160px] transition-all",
      selected ? 'border-amber-400/40 shadow-lg' : 'border-white/10'
    )} style={{ background: 'rgba(245, 158, 11, 0.08)' }}>
      <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-amber-400/50 !border-2 !border-amber-400/50" />
      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-amber-400/50 !border-2 !border-amber-400/50" />
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-amber-400/15 flex items-center justify-center">
          <Clock className="w-4 h-4 text-amber-400" />
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-white/40">Esperar</p>
          <p className="text-sm font-medium text-white">{data.config?.delay || '5 min'}</p>
        </div>
      </div>
    </div>
  )
}

const nodeTypes = {
  trigger: TriggerNode,
  action: ActionNode,
  wait: WaitNode,
}

/* Convert delay string to config */
function parseDelay(delayStr: string): Record<string, number> {
  if (delayStr.includes('día')) return { days: parseInt(delayStr) || 1 }
  if (delayStr.includes('hora')) return { hours: parseInt(delayStr) || 1 }
  return { minutes: parseInt(delayStr) || 5 }
}

/* Convert nodes+edges to workflow actions */
function buildWorkflowActions(nodes: FlowNode<NodeData>[], edges: FlowEdge[]) {
  // Find trigger node (should be first)
  const triggerNode = nodes.find(n => n.type === 'trigger')
  if (!triggerNode) return { triggerType: 'new_message', actions: [] }

  // Build adjacency map
  const adjacency: Record<string, string[]> = {}
  edges.forEach(e => {
    if (!adjacency[e.source]) adjacency[e.source] = []
    adjacency[e.source].push(e.target)
  })

  // Traverse from trigger
  const actions: Record<string, any>[] = []
  const visited = new Set<string>()
  const queue = triggerNode.id ? [triggerNode.id] : []

  while (queue.length > 0) {
    const currentId = queue.shift()!
    if (visited.has(currentId)) continue
    visited.add(currentId)

    const node = nodes.find(n => n.id === currentId)
    if (!node || node.type === 'trigger') {
      // Add children to queue
      const children = adjacency[currentId] || []
      queue.push(...children)
      continue
    }

    const data = node.data
    const config = { ...data.config }

    if (node.type === 'wait' && config.delay) {
      const parsed = parseDelay(config.delay)
      Object.assign(config, parsed)
      delete config.delay
    }

    actions.push({
      type: data.type,
      config,
    })

    const children = adjacency[currentId] || []
    queue.push(...children)
  }

  return {
    triggerType: triggerNode.data.type,
    actions,
  }
}

function BuilderCanvas() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const workflowId = searchParams?.get('id')
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const { screenToFlowPosition } = useReactFlow()

  const [nodes, setNodes, onNodesChange] = useNodesState<FlowNode<NodeData>>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<FlowEdge>([])
  const [selectedNode, setSelectedNode] = useState<FlowNode<NodeData> | null>(null)
  const [draggedType, setDraggedType] = useState<{ type: NodeType; item: any } | null>(null)

  // Save modal state
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [workflowName, setWorkflowName] = useState('')
  const [workflowDescription, setWorkflowDescription] = useState('')
  const [selectedBusinessId, setSelectedBusinessId] = useState('')
  const [businesses, setBusinesses] = useState<any[]>([])
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState(false)

  useEffect(() => {
    businessApi.list().then(data => {
      setBusinesses(data)
      if (data.length > 0) setSelectedBusinessId(data[0].id)
    }).catch(() => {})
  }, [])

  // Load existing workflow if editing
  useEffect(() => {
    if (!workflowId) return
    automationsApi.getWorkflows('').then(wfs => {
      const wf = wfs.find((w: any) => w.id === workflowId)
      if (wf && wf.visual_data) {
        setNodes(wf.visual_data.nodes || [])
        setEdges(wf.visual_data.edges || [])
        setWorkflowName(wf.name || '')
        setWorkflowDescription(wf.description || '')
        setSelectedBusinessId(wf.business_id || '')
      }
    }).catch(() => {})
  }, [workflowId, setNodes, setEdges])

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: 'rgba(255,255,255,0.2)' } }, eds)),
    [setEdges]
  )

  const onDragStart = (event: React.DragEvent, nodeType: NodeType, item: any) => {
    setDraggedType({ type: nodeType, item })
    event.dataTransfer.effectAllowed = 'move'
  }

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()
      if (!draggedType || !reactFlowWrapper.current) return

      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      })

      const { type, item } = draggedType
      const newNode: FlowNode<NodeData> = {
        id: `${type}_${Date.now()}`,
        type,
        position,
        data: {
          label: item.label,
          type: item.type,
          config: type === 'wait' ? { delay: '10 minutos' } : item.type === 'ai_reply' ? { personality: 'captador' } : {},
          icon: item.icon,
          color: item.color,
        },
      }

      setNodes((nds) => nds.concat(newNode))
      setDraggedType(null)
    },
    [draggedType, screenToFlowPosition, setNodes]
  )

  const onNodeClick = useCallback((_: React.MouseEvent, node: FlowNode<NodeData>) => {
    setSelectedNode(node)
  }, [])

  const updateNodeData = (nodeId: string, newData: Partial<NodeData>) => {
    setNodes((nds) =>
      nds.map((n) => {
        if (n.id === nodeId) {
          return { ...n, data: { ...n.data, ...newData } }
        }
        return n
      })
    )
    if (selectedNode?.id === nodeId) {
      setSelectedNode((prev) => prev ? { ...prev, data: { ...prev.data, ...newData } } : null)
    }
  }

  const deleteNode = (nodeId: string) => {
    setNodes((nds) => nds.filter((n) => n.id !== nodeId))
    setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId))
    if (selectedNode?.id === nodeId) setSelectedNode(null)
  }

  const exportWorkflow = async () => {
    const { triggerType, actions } = buildWorkflowActions(nodes, edges)

    if (!selectedBusinessId) {
      setSaveError('Seleccioná un negocio primero')
      setShowSaveModal(true)
      return
    }
    if (nodes.length === 0) {
      setSaveError('El workflow está vacío')
      return
    }
    setShowSaveModal(true)
  }

  const handleSave = async () => {
    if (!workflowName.trim()) {
      setSaveError('El nombre es obligatorio')
      return
    }
    if (!selectedBusinessId) {
      setSaveError('Seleccioná un negocio')
      return
    }

    const { triggerType, actions } = buildWorkflowActions(nodes, edges)

    setSaving(true)
    setSaveError(null)
    try {
      const payload = {
        business_id: selectedBusinessId,
        name: workflowName,
        description: workflowDescription || null,
        trigger_type: triggerType,
        trigger_config: {},
        actions,
        visual_data: { nodes, edges },
        status: 'active',
      }

      if (workflowId) {
        await automationsApi.updateWorkflow(workflowId, payload)
      } else {
        await automationsApi.createWorkflow(payload as any)
      }
      setSaveSuccess(true)
      setTimeout(() => {
        setShowSaveModal(false)
        router.push('/dashboard/automatizaciones')
      }, 1500)
    } catch (e: any) {
      setSaveError(e.response?.data?.detail || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex overflow-hidden bg-[#060812]">
      {/* Sidebar */}
      <div className="w-64 border-r border-white/[0.06] bg-[#070a14] flex flex-col shrink-0">
        <div className="p-4 border-b border-white/[0.06]">
          <Link href="/dashboard/automatizaciones" className="inline-flex items-center gap-2 text-sm text-white/40 hover:text-white transition-colors mb-3">
            <ArrowLeft className="w-4 h-4" />
            Volver
          </Link>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Zap className="w-4 h-4 text-brand-orange" />
            Workflow Builder
          </h2>
        </div>

        <div className="flex-1 overflow-y-auto no-scrollbar p-4 space-y-6">
          {/* Triggers */}
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-white/30 mb-3">Triggers</p>
            <div className="space-y-2">
              {triggerTypes.map((t) => (
                <div
                  key={t.type}
                  draggable
                  onDragStart={(e) => onDragStart(e, 'trigger', t)}
                  className="flex items-center gap-2.5 p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.06] hover:border-white/[0.12] cursor-grab active:cursor-grabbing transition-all"
                >
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0" style={{ background: `${t.color}20` }}>
                    <t.icon className="w-3.5 h-3.5" style={{ color: t.color }} />
                  </div>
                  <span className="text-xs text-white/70">{t.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-white/30 mb-3">Acciones</p>
            <div className="space-y-2">
              {actionTypes.map((t) => (
                <div
                  key={t.type}
                  draggable
                  onDragStart={(e) => onDragStart(e, t.type === 'wait' ? 'wait' : 'action', t)}
                  className="flex items-center gap-2.5 p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.06] hover:border-white/[0.12] cursor-grab active:cursor-grabbing transition-all"
                >
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0" style={{ background: `${t.color}15` }}>
                    <t.icon className="w-3.5 h-3.5" style={{ color: t.color }} />
                  </div>
                  <span className="text-xs text-white/70">{t.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-white/[0.06] space-y-2">
          <Button onClick={exportWorkflow} leftIcon={<Save className="w-4 h-4" />} className="w-full">
            {workflowId ? 'Actualizar Workflow' : 'Guardar Workflow'}
          </Button>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 relative" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onDragOver={onDragOver}
          onDrop={onDrop}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
          proOptions={{ hideAttribution: true }}
          defaultEdgeOptions={{ animated: true, style: { stroke: 'rgba(255,255,255,0.15)', strokeWidth: 2 } }}
        >
          <Background color="rgba(255,255,255,0.03)" gap={20} size={1} />
          <Controls className="!bg-[#0A0E1A] !border-white/[0.08] !shadow-xl" />
          <MiniMap
            className="!bg-[#0A0E1A] !border-white/[0.08]"
            nodeColor={(n: any) => n.data?.color || '#64748B'}
            maskColor="rgba(6, 8, 18, 0.8)"
          />
          <Panel position="top-center">
            <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#0A0E1A]/80 backdrop-blur border border-white/[0.08] text-xs text-white/40">
              <MousePointer2 className="w-3.5 h-3.5" />
              Arrastrá triggers y acciones al canvas · Conectá los nodos
            </div>
          </Panel>
        </ReactFlow>
      </div>

      {/* Properties Panel */}
      {selectedNode && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="w-72 border-l border-white/[0.06] bg-[#070a14] flex flex-col shrink-0"
        >
          <div className="p-4 border-b border-white/[0.06] flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Propiedades</h3>
            <button onClick={() => setSelectedNode(null)} className="p-1.5 rounded-lg hover:bg-white/5 text-white/30 hover:text-white/60 transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </button>
          </div>

          <div className="p-4 space-y-4">
            <div>
              <label className="text-[10px] font-semibold uppercase tracking-wider text-white/30 mb-1.5 block">Nombre</label>
              <input
                type="text"
                value={selectedNode.data?.label || ''}
                onChange={(e) => updateNodeData(selectedNode.id, { label: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
              />
            </div>

            {selectedNode.type === 'action' && selectedNode.data?.type === 'ai_reply' && (
              <div>
                <label className="text-[10px] font-semibold uppercase tracking-wider text-white/30 mb-1.5 block">Agente IA</label>
                <select
                  value={selectedNode.data?.config?.personality || 'captador'}
                  onChange={(e) => updateNodeData(selectedNode.id, { config: { ...selectedNode.data.config, personality: e.target.value } })}
                  className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                >
                  <option value="captador" className="bg-[#0A0E1A]">🎣 Captador</option>
                  <option value="cualificador" className="bg-[#0A0E1A]">🎯 Cualificador</option>
                  <option value="vendedor" className="bg-[#0A0E1A]">💰 Vendedor</option>
                  <option value="post-venta" className="bg-[#0A0E1A]">🤝 Post-Venta</option>
                  <option value="alex-hormozi" className="bg-[#0A0E1A]">🎯 Alex Hormozi</option>
                  <option value="jordan-belfort" className="bg-[#0A0E1A]">🐺 Jordan Belfort</option>
                </select>
              </div>
            )}

            {selectedNode.type === 'wait' && (
              <div>
                <label className="text-[10px] font-semibold uppercase tracking-wider text-white/30 mb-1.5 block">Delay</label>
                <select
                  value={selectedNode.data?.config?.delay || '10 minutos'}
                  onChange={(e) => updateNodeData(selectedNode.id, { config: { ...selectedNode.data.config, delay: e.target.value } })}
                  className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                >
                  <option value="5 minutos" className="bg-[#0A0E1A]">5 minutos</option>
                  <option value="10 minutos" className="bg-[#0A0E1A]">10 minutos</option>
                  <option value="30 minutos" className="bg-[#0A0E1A]">30 minutos</option>
                  <option value="1 hora" className="bg-[#0A0E1A]">1 hora</option>
                  <option value="6 horas" className="bg-[#0A0E1A]">6 horas</option>
                  <option value="1 día" className="bg-[#0A0E1A]">1 día</option>
                  <option value="3 días" className="bg-[#0A0E1A]">3 días</option>
                </select>
              </div>
            )}

            {selectedNode.type === 'action' && (selectedNode.data?.type === 'send_message' || selectedNode.data?.type === 'send_email') && (
              <div>
                <label className="text-[10px] font-semibold uppercase tracking-wider text-white/30 mb-1.5 block">Contenido / Template</label>
                <textarea
                  value={selectedNode.data?.config?.content || ''}
                  onChange={(e) => updateNodeData(selectedNode.id, { config: { ...selectedNode.data.config, content: e.target.value } })}
                  placeholder="Escribí el mensaje o nombre del template..."
                  rows={4}
                  className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20 resize-none"
                />
              </div>
            )}

            <div className="pt-4 border-t border-white/[0.06]">
              <button
                onClick={() => deleteNode(selectedNode.id)}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-all text-sm font-medium"
              >
                <Trash2 className="w-4 h-4" />
                Eliminar nodo
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Save Modal */}
      <AnimatePresence>
        {showSaveModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-md p-6 rounded-2xl bg-[#0A0E1A] border border-white/[0.08] shadow-2xl"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">
                  {workflowId ? 'Actualizar Workflow' : 'Guardar Workflow'}
                </h3>
                <button onClick={() => setShowSaveModal(false)} className="p-1.5 rounded-lg hover:bg-white/5 text-white/40 hover:text-white/60 transition-colors">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-white/40 mb-1.5 block">Negocio</label>
                  <select
                    value={selectedBusinessId}
                    onChange={(e) => setSelectedBusinessId(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  >
                    {businesses.map(b => (
                      <option key={b.id} value={b.id} className="bg-[#0A0E1A]">{b.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-medium text-white/40 mb-1.5 block">Nombre *</label>
                  <input
                    type="text"
                    value={workflowName}
                    onChange={(e) => setWorkflowName(e.target.value)}
                    placeholder="Ej: Recuperación de carrito"
                    className="w-full px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-white/40 mb-1.5 block">Descripción</label>
                  <textarea
                    value={workflowDescription}
                    onChange={(e) => setWorkflowDescription(e.target.value)}
                    placeholder="Describe qué hace este workflow..."
                    rows={3}
                    className="w-full px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20 resize-none"
                  />
                </div>

                {saveError && (
                  <div className="p-3 rounded-xl bg-red-500/10 text-red-400 text-xs border border-red-500/20">
                    {saveError}
                  </div>
                )}

                {saveSuccess && (
                  <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400 text-xs border border-emerald-500/20 flex items-center gap-2">
                    <Check className="w-4 h-4" />
                    Workflow guardado correctamente
                  </div>
                )}

                <div className="flex gap-2 pt-2">
                  <Button variant="secondary" onClick={() => setShowSaveModal(false)} className="flex-1">
                    Cancelar
                  </Button>
                  <Button onClick={handleSave} disabled={saving} leftIcon={saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} className="flex-1">
                    {saving ? 'Guardando...' : 'Guardar'}
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function WorkflowBuilderPage() {
  return (
    <ReactFlowProvider>
      <BuilderCanvas />
    </ReactFlowProvider>
  )
}
