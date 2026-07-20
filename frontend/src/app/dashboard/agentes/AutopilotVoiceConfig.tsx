'use client'

import { logger } from '@/lib/logger';
import { useState, useEffect } from 'react'
import { agentsApi, AgentPersonality, AutopilotVoiceConfig as VoiceConfig } from '@/lib/agents'
import { Settings, X, Save, Loader2, Mic } from 'lucide-react'

interface Props {
  personalities: AgentPersonality[]
  businessId: string
}

const AUTOPILOT_NAMES: Record<string, { name: string; emoji: string; desc: string }> = {
  captador: { name: 'Captador', emoji: '🎣', desc: 'Captación de leads' },
  cualificador: { name: 'Cualificador', emoji: '🎯', desc: 'Cualificación de leads' },
  vendedor: { name: 'Vendedor', emoji: '💰', desc: 'Cierre de ventas' },
  'post-venta': { name: 'Post-Venta', emoji: '🤝', desc: 'Fidelización y soporte' },
}

export default function AutopilotVoiceConfigPanel({ personalities, businessId }: Props) {
  const [open, setOpen] = useState(false)
  const [configs, setConfigs] = useState<Record<string, VoiceConfig>>({})
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!open || !businessId) return
    const load = async () => {
      setLoading(true)
      try {
        const data = await agentsApi.getAutopilotVoices(businessId)
        setConfigs(data.configs)
      } catch (e) {
        logger.error(String(e))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [open, businessId])

  const updateVoice = (slug: string, voiceSlug: string) => {
    setConfigs(prev => ({
      ...prev,
      [slug]: { ...prev[slug], voice_personality_slug: voiceSlug || null },
    }))
  }

  const saveConfig = async (slug: string) => {
    const cfg = configs[slug]
    if (!cfg) return

    const personality = personalities.find(p => p.slug === slug)
    const voicePersonality = personalities.find(p => p.slug === cfg.voice_personality_slug)
    if (!personality) return

    setSaving(true)
    try {
      await agentsApi.createOrUpdateConfig(businessId, {
        personality_id: personality.id,
        voice_personality_id: voicePersonality?.id || null,
        custom_instructions: cfg.custom_instructions,
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      logger.error(String(e))
      alert('Error al guardar configuración')
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 px-4 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm text-white/70 transition-all"
      >
        <Settings className="w-4 h-4" />
        Configurar Voz del Auto-Piloto
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-2xl bg-[#0a0e1a] border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center">
                  <Mic className="w-5 h-5 text-brand-orange" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Voz del Auto-Piloto</h3>
                  <p className="text-xs text-white/40">Asigná una personalidad experta a cada agente funcional</p>
                </div>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="p-2 rounded-lg hover:bg-white/5 text-white/40 hover:text-white/70 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 text-brand-orange animate-spin" />
                </div>
              ) : (
                Object.entries(AUTOPILOT_NAMES).map(([slug, info]) => {
                  const cfg = configs[slug]
                  const selectedVoice = personalities.find(p => p.slug === cfg?.voice_personality_slug)
                  return (
                    <div
                      key={slug}
                      className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:border-white/[0.10] transition-all"
                    >
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center text-2xl shrink-0">
                          {info.emoji}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <h4 className="text-sm font-semibold text-white">{info.name}</h4>
                            {selectedVoice && (
                              <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-orange/10 text-brand-orange border border-brand-orange/20">
                                Voz: {selectedVoice.name}
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-white/30 mb-3">{info.desc}</p>

                          <div className="flex items-center gap-3">
                            <select
                              value={cfg?.voice_personality_slug || ''}
                              onChange={e => updateVoice(slug, e.target.value)}
                              className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white/80 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                            >
                              <option value="" className="bg-[#0a0e1a]">Sin voz experta (default)</option>
                              {personalities
                                .filter(p => p.slug !== slug)
                                .sort((a, b) => a.name.localeCompare(b.name))
                                .map(p => (
                                  <option key={p.id} value={p.slug} className="bg-[#0a0e1a]">
                                    {p.emoji} {p.name} — {p.tagline}
                                  </option>
                                ))}
                            </select>
                            <button
                              onClick={() => saveConfig(slug)}
                              disabled={saving}
                              className="flex items-center gap-1.5 px-4 py-2 bg-brand-orange hover:bg-brand-orange-dark text-white text-sm font-medium rounded-lg transition-all disabled:opacity-50"
                            >
                              {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                              Guardar
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })
              )}
            </div>

            {saved && (
              <div className="px-6 py-3 bg-green-500/10 border-t border-green-500/20 text-green-400 text-xs text-center">
                Configuración guardada correctamente
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
