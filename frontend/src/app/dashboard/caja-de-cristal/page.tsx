'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { MonitorPlay, Loader2, Plus, ArrowLeft, History, LayoutGrid, BookOpen, FileText, Keyboard } from 'lucide-react'

import { ComputerUseClient } from '@/lib/computer-use'
import { computerUseApi } from '@/lib/api/computer-use'
import { useComputerUseKeyboardShortcuts } from '@/hooks/useComputerUseKeyboardShortcuts'
import ComputerUseViewer from '@/components/computer-use/ComputerUseViewer'
import ComputerUseControls from '@/components/computer-use/ComputerUseControls'
import ComputerUseLog from '@/components/computer-use/ComputerUseLog'
import ComputerUseChat from '@/components/computer-use/ComputerUseChat'
import ComputerUseStatus from '@/components/computer-use/ComputerUseStatus'
import ComputerUseScreenshotHistory from '@/components/computer-use/ComputerUseScreenshotHistory'
import ComputerUseExportButton from '@/components/computer-use/ComputerUseExportButton'
import ComputerUseTemplatesPanel from '@/components/computer-use/ComputerUseTemplatesPanel'
import ComputerUseBatchPanel from '@/components/computer-use/ComputerUseBatchPanel'
import ComputerUseActiveGrid from '@/components/computer-use/ComputerUseActiveGrid'
import ComputerUseReplay from '@/components/computer-use/ComputerUseReplay'
import ComputerUseAnnotationsOverlay from '@/components/computer-use/ComputerUseAnnotationsOverlay'
import ComputerUseElementHighlight from '@/components/computer-use/ComputerUseElementHighlight'
import ComputerUseScreenshotGallery from '@/components/computer-use/ComputerUseScreenshotGallery'
import ComputerUseVoiceCommands from '@/components/computer-use/ComputerUseVoiceCommands'

interface LogEntry {
  step: number
  action_type: string
  params: Record<string, any>
  reason: string
  execution_result?: string
}

interface ChatMessage {
  role: 'user' | 'agent' | 'system'
  content: string
}

interface Annotation {
  id: string
  step_number: number
  content: string
  x_coordinate?: number
  y_coordinate?: number
  color: string
}

export default function CajaDeCristalPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const sessionIdFromUrl = searchParams?.get('session') ?? null

  const [sessionId, setSessionId] = useState<string | null>(sessionIdFromUrl)
  const [task, setTask] = useState('')
  const [startUrl, setStartUrl] = useState('')
  const [browserType, setBrowserType] = useState('chromium')
  const [isCreating, setIsCreating] = useState(false)
  const [activeTab, setActiveTab] = useState<'new' | 'active' | 'templates' | 'batch'>('new')
  const [showShortcuts, setShowShortcuts] = useState(false)

  // Live state
  const [screenshot, setScreenshot] = useState<string | null>(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [currentUrl, setCurrentUrl] = useState('')
  const [status, setStatus] = useState('idle')
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [lastAction, setLastAction] = useState<LogEntry | null>(null)
  const [result, setResult] = useState('')
  const [historySteps, setHistorySteps] = useState<any[]>([])
  const [annotations, setAnnotations] = useState<Annotation[]>([])
  const [showReplay, setShowReplay] = useState(false)
  const [replayData, setReplayData] = useState<any>(null)
  const [showGallery, setShowGallery] = useState(false)
  const [highlightCoords, setHighlightCoords] = useState<{x: number, y: number} | null>(null)

  const clientRef = useRef<ComputerUseClient | null>(null)

  useEffect(() => {
    if (sessionIdFromUrl) {
      setSessionId(sessionIdFromUrl)
      connectToSession(sessionIdFromUrl)
    }
  }, [sessionIdFromUrl])

  useComputerUseKeyboardShortcuts({
    onPause: () => clientRef.current?.pause(),
    onResume: () => clientRef.current?.resume(),
    onStop: () => clientRef.current?.stop(),
    onToggleHistory: () => {},
    onToggleChat: () => {},
  }, !!sessionId)

  const connectToSession = useCallback((sid: string) => {
    const client = new ComputerUseClient(sid)
    clientRef.current = client

    client.onConnect = () => setStatus('connecting')

    client.onScreenshot = (imageBase64, step, url) => {
      setScreenshot(imageBase64)
      setCurrentStep(step)
      setCurrentUrl(url)
      setHistorySteps(prev => [...prev, { step, image: imageBase64, url }])
    }

    client.onAction = (msg) => {
      const entry: LogEntry = {
        step: msg.data.step,
        action_type: msg.data.action_type,
        params: msg.data.params,
        reason: msg.data.reason,
      }
      setLogs((prev) => [...prev, entry])
      setLastAction(entry)
      // Highlight element if click action
      if (msg.data.action_type === 'click' && msg.data.params?.x && msg.data.params?.y) {
        setHighlightCoords({ x: msg.data.params.x, y: msg.data.params.y })
        setTimeout(() => setHighlightCoords(null), 2000)
      }
    }

    client.onStatus = (newStatus, message, step) => {
      setStatus(newStatus)
      setCurrentStep(step)
      if (message) {
        setChatMessages((prev) => [...prev, { role: 'system', content: message }])
      }
    }

    client.onChat = (role, content) => {
      setChatMessages((prev) => [...prev, { role: role as any, content }])
    }

    client.onError = (message) => {
      setChatMessages((prev) => [...prev, { role: 'system', content: `Error: ${message}` }])
    }

    client.onCompleted = (res) => {
      setResult(res)
      setStatus('completed')
      setChatMessages((prev) => [...prev, { role: 'system', content: `✅ ${res}` }])
    }

    client.onDisconnect = () => {
      if (status !== 'completed' && status !== 'failed' && status !== 'stopped') {
        setStatus('disconnected')
      }
    }

    client.connect()
  }, [status])

  const handleCreateSession = async () => {
    if (!task.trim()) return
    setIsCreating(true)
    try {
      const session = await computerUseApi.createSession({
        task_description: task.trim(),
        start_url: startUrl.trim() || undefined,
        browser_type: browserType,
      })
      setSessionId(session.id)
      await computerUseApi.startSession(session.id)
      connectToSession(session.id)
      router.push(`/dashboard/caja-de-cristal?session=${session.id}`)
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        { role: 'system', content: `Error: ${err?.response?.data?.detail || err.message}` },
      ])
    } finally {
      setIsCreating(false)
    }
  }

  const handlePause = () => clientRef.current?.pause()
  const handleResume = () => clientRef.current?.resume()
  const handleStop = () => clientRef.current?.stop()
  const handleSendMessage = (msg: string) => clientRef.current?.sendMessage(msg)

  const handleBack = () => {
    clientRef.current?.disconnect()
    setSessionId(null)
    setScreenshot(null)
    setCurrentStep(0)
    setCurrentUrl('')
    setStatus('idle')
    setLogs([])
    setChatMessages([])
    setLastAction(null)
    setResult('')
    setTask('')
    setStartUrl('')
    setHistorySteps([])
    setAnnotations([])
    setReplayData(null)
    router.push('/dashboard/caja-de-cristal')
  }

  const loadReplay = async (sid: string) => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token')
      const res = await fetch(`/api/v1/computer-use/sessions/${sid}/replay`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const data = await res.json()
        setReplayData(data)
        setShowReplay(true)
      }
    } catch (e) {
      console.error(e)
    }
  }

  const loadAnnotations = async (sid: string) => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token')
      const res = await fetch(`/api/v1/computer-use/sessions/${sid}/annotations`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const data = await res.json()
        setAnnotations(data)
      }
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    if (sessionId) {
      loadAnnotations(sessionId)
    }
  }, [sessionId])

  const handleSelectHistoryStep = (stepNumber: number) => {
    const stepLog = logs.find((l) => l.step === stepNumber)
    if (stepLog) setLastAction(stepLog)
  }

  // ========== CREATION VIEW ==========
  if (!sessionId) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center">
              <MonitorPlay className="w-5 h-5 text-brand-orange" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Caja de Cristal</h1>
              <p className="text-sm text-white/40">Supervisá en tiempo real cómo el agente IA opera el navegador</p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 mb-6 bg-white/5 rounded-lg p-1 w-fit">
          {[
            { id: 'new', label: 'Nueva sesión', icon: Plus },
            { id: 'active', label: 'Activas', icon: LayoutGrid },
            { id: 'templates', label: 'Plantillas', icon: BookOpen },
            { id: 'batch', label: 'Batch', icon: FileText },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.id ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white/60'
              }`}
            >
              <tab.icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === 'new' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-[#0A0E1A] rounded-2xl border border-white/[0.08] p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Nueva automatización</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-white/50 mb-1.5">¿Qué querés que haga el agente?</label>
                  <textarea
                    value={task}
                    onChange={(e) => setTask(e.target.value)}
                    placeholder="Ej: Creá un banner en Canva con los colores de mi marca..."
                    rows={4}
                    className="w-full bg-white/5 border border-white/[0.08] rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-brand-orange/30 transition-colors resize-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-white/50 mb-1.5">URL inicial (opcional)</label>
                  <input
                    type="url"
                    value={startUrl}
                    onChange={(e) => setStartUrl(e.target.value)}
                    placeholder="https://..."
                    className="w-full bg-white/5 border border-white/[0.08] rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-brand-orange/30 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-white/50 mb-1.5">Navegador</label>
                  <div className="flex gap-2">
                    {[
                      { value: 'chromium', label: '🌐 Chromium' },
                      { value: 'firefox', label: '🦊 Firefox' },
                      { value: 'webkit', label: '🧭 WebKit' },
                    ].map(b => (
                      <button
                        key={b.value}
                        onClick={() => setBrowserType(b.value)}
                        className={`flex-1 px-3 py-2 rounded-lg text-sm border transition-colors ${
                          browserType === b.value
                            ? 'bg-brand-orange/20 border-brand-orange/40 text-white'
                            : 'bg-white/5 border-white/[0.08] text-white/50 hover:bg-white/[0.07]'
                        }`}
                      >
                        {b.label}
                      </button>
                    ))}
                  </div>
                </div>
                <button
                  onClick={handleCreateSession}
                  disabled={!task.trim() || isCreating}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-brand-orange hover:bg-brand-orange/90 disabled:bg-white/5 disabled:text-white/30 text-white font-medium rounded-xl transition-all"
                >
                  {isCreating ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Iniciando...</>
                  ) : (
                    <><Plus className="w-4 h-4" /> Iniciar Caja de Cristal</>
                  )}
                </button>
              </div>
            </div>
            <RecentSessions onSelect={(id) => {
              setSessionId(id)
              connectToSession(id)
              router.push(`/dashboard/caja-de-cristal?session=${id}`)
            }} onReplay={loadReplay} />
          </div>
        )}

        {activeTab === 'active' && (
          <ComputerUseActiveGrid onConnect={(id) => {
            setSessionId(id)
            connectToSession(id)
            router.push(`/dashboard/caja-de-cristal?session=${id}`)
          }} />
        )}

        {activeTab === 'templates' && (
          <ComputerUseTemplatesPanel onSelectTemplate={(t) => {
            setTask(t.task_description)
            setStartUrl(t.start_url || '')
            setActiveTab('new')
          }} />
        )}

        {activeTab === 'batch' && <ComputerUseBatchPanel />}

        {/* Info cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <InfoCard title="Supervisión Total" description="Vé cada click, scroll y navegación en tiempo real. Como estar mirando por encima del hombro del agente." />
          <InfoCard title="Múltiples Navegadores" description="Ejecutá sesiones en paralelo con Chromium, Firefox o WebKit. Monitoreá todo desde un solo panel." />
          <InfoCard title="Export & Replay" description="Exportá sesiones a PDF, CSV o JSON. Reproducí paso a paso cualquier sesión pasada con anotaciones." />
        </div>

        {/* Keyboard shortcuts hint */}
        <div className="mt-4 flex items-center justify-center">
          <button
            onClick={() => setShowShortcuts(!showShortcuts)}
            className="flex items-center gap-1.5 text-xs text-white/30 hover:text-white/50 transition-colors"
          >
            <Keyboard className="w-3 h-3" />
            Atajos de teclado
          </button>
        </div>
        {showShortcuts && (
          <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2 max-w-2xl mx-auto">
            {[
              { key: 'P', desc: 'Pausar sesión' },
              { key: 'R', desc: 'Reanudar sesión' },
              { key: 'Shift+S', desc: 'Detener sesión' },
              { key: 'Shift+F', desc: 'Pantalla completa' },
              { key: 'Shift+H', desc: 'Historial' },
              { key: 'Shift+M', desc: 'Chat' },
              { key: '← →', desc: 'Navegar replay' },
              { key: 'Espacio', desc: 'Play/Pause replay' },
            ].map(s => (
              <div key={s.key} className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-2">
                <kbd className="px-1.5 py-0.5 bg-white/10 rounded text-[10px] font-mono text-white/60">{s.key}</kbd>
                <span className="text-xs text-white/40">{s.desc}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // ========== LIVE SESSION VIEW ==========
  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-white/[0.06] bg-[#070a14]/50 backdrop-blur">
        <div className="flex items-center gap-3">
          <button onClick={handleBack} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
            <ArrowLeft className="w-4 h-4 text-white/40" />
          </button>
          <div>
            <h1 className="text-sm font-semibold text-white">Caja de Cristal</h1>
            <p className="text-xs text-white/30 truncate max-w-md">{task || 'Sesión de automatización'}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {sessionId && (
            <>
              <ComputerUseExportButton sessionId={sessionId} />
              <button
                onClick={() => loadReplay(sessionId)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-white/5 hover:bg-white/10 rounded-lg text-white/60 hover:text-white transition-colors"
              >
                <MonitorPlay className="w-3 h-3" />
                Replay
              </button>
              <button
                onClick={() => setShowGallery(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-white/5 hover:bg-white/10 rounded-lg text-white/60 hover:text-white transition-colors"
              >
                Gallery
              </button>
              <ComputerUseVoiceCommands
                onCommand={(cmd) => handleSendMessage(cmd)}
                disabled={status === 'completed' || status === 'failed'}
              />
              <ComputerUseScreenshotHistory
                sessionId={sessionId}
                steps={historySteps}
                currentStep={currentStep}
                onSelectStep={handleSelectHistoryStep}
              />
            </>
          )}
          <ComputerUseControls
            status={status}
            onPause={handlePause}
            onResume={handleResume}
            onStop={handleStop}
          />
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left panel */}
        <div className="flex-1 flex flex-col p-4 min-w-0 relative">
          <ComputerUseViewer
            imageBase64={screenshot}
            step={currentStep}
            url={currentUrl}
            lastAction={lastAction}
          />
          {highlightCoords && (
            <ComputerUseElementHighlight
              x={highlightCoords.x}
              y={highlightCoords.y}
              label="click"
              color="#f59e0b"
            />
          )}
          {/* Annotations panel */}
          {sessionId && (
            <div className="mt-3 shrink-0">
              <ComputerUseAnnotationsOverlay
                sessionId={sessionId}
                stepNumber={currentStep}
                annotations={annotations}
                onAnnotationAdded={(ann) => setAnnotations(prev => [...prev, ann])}
              />
            </div>
          )}
        </div>

        {/* Right panel */}
        <div className="w-96 flex flex-col gap-3 p-4 pr-6 overflow-hidden">
          <ComputerUseStatus
            status={status}
            step={currentStep}
            totalSteps={30}
            task={task || 'Automatización'}
            url={currentUrl}
          />
          <div className="flex-1 min-h-0">
            <ComputerUseLog logs={logs} />
          </div>
          <div className="h-64 shrink-0">
            <ComputerUseChat
              messages={chatMessages}
              onSendMessage={handleSendMessage}
              disabled={status === 'completed' || status === 'failed' || status === 'stopped'}
            />
          </div>
        </div>
      </div>

      {/* Replay overlay */}
      {showReplay && replayData && (
        <ComputerUseReplay
          steps={replayData.steps}
          task_description={replayData.task_description}
          onClose={() => setShowReplay(false)}
        />
      )}

      {/* Gallery overlay */}
      {showGallery && (
        <ComputerUseScreenshotGallery
          screenshots={historySteps.map(s => ({ step: s.step, url: s.url, image: s.image }))}
          onClose={() => setShowGallery(false)}
        />
      )}
    </div>
  )
}

function RecentSessions({ onSelect, onReplay }: { onSelect: (id: string) => void; onReplay: (id: string) => void }) {
  const [sessions, setSessions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    computerUseApi.listSessions().then((res) => {
      setSessions(res.items.slice(0, 5))
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  return (
    <div className="bg-[#0A0E1A] rounded-2xl border border-white/[0.08] p-6">
      <div className="flex items-center gap-2 mb-4">
        <History className="w-4 h-4 text-white/40" />
        <h2 className="text-lg font-semibold text-white">Sesiones recientes</h2>
      </div>
      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-5 h-5 text-white/20 animate-spin" />
        </div>
      ) : sessions.length === 0 ? (
        <p className="text-sm text-white/20 text-center py-8">No hay sesiones recientes</p>
      ) : (
        <div className="space-y-2">
          {sessions.map((s) => (
            <div
              key={s.id}
              className="w-full text-left p-3 rounded-xl bg-white/5 hover:bg-white/[0.07] border border-white/[0.04] transition-all group"
            >
              <div className="flex items-center justify-between">
                <button onClick={() => onSelect(s.id)} className="flex-1 text-left min-w-0">
                  <p className="text-sm text-white/70 truncate group-hover:text-white transition-colors">{s.task_description}</p>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      s.status === 'completed' ? 'bg-green-500/10 text-green-400' :
                      s.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                      s.status === 'running' ? 'bg-brand-teal/10 text-brand-teal' :
                      'bg-white/5 text-white/30'
                    }`}>
                      {s.status}
                    </span>
                    <span className="text-[10px] text-white/20">{s.total_steps} pasos</span>
                    {s.browser_type && (
                      <span className="text-[10px] text-white/20">{s.browser_type}</span>
                    )}
                  </div>
                </button>
                <button
                  onClick={() => onReplay(s.id)}
                  className="ml-2 p-1.5 hover:bg-white/10 rounded-lg text-white/30 hover:text-white transition-colors"
                  title="Replay"
                >
                  <MonitorPlay className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function InfoCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="bg-[#0A0E1A] rounded-2xl border border-white/[0.08] p-5">
      <h3 className="text-sm font-semibold text-white/70 mb-1">{title}</h3>
      <p className="text-xs text-white/30 leading-relaxed">{description}</p>
    </div>
  )
}
