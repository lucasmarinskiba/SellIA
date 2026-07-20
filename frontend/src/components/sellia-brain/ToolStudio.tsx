'use client'

/**
 * TOOL STUDIO — detalle + configuración + lanzamiento de una herramienta.
 *
 * Cada herramienta del "Recomendado para tu negocio" abre acá: qué hace, a qué
 * cuenta/plataforma está anexada (link real del perfil), inputs de configuración
 * y "Lanzar" → arma la indicación y la ejecuta vía Computer Use (flujo n8n +
 * dispatch real si el backend está vivo).
 */

import { useEffect, useState } from 'react'
import { X, Check, ExternalLink, Rocket, Wrench, AlertTriangle, ShieldCheck, Target, BookOpen, Plus } from 'lucide-react'
import { SELLIA } from '@/lib/sellia-theme'
import type { BusinessProfile, PlannedFlow } from '@/lib/business-profile'
import { TOOL_BY_ID, accountUrlFor, CATEGORY_COLOR } from '@/lib/tools-catalog'
import { STRATEGY_BY_ID } from '@/lib/growth-strategies'

const T = SELLIA

interface Props { toolId: string | null; profile: BusinessProfile | null; onClose: () => void; onLaunch: (flow: PlannedFlow) => void; onAddToPlan?: (flow: PlannedFlow) => void }

const buildFlow = (toolId: string, name: string, caps: string[], platformLabel: string, instruction: string): PlannedFlow => {
  const steps: PlannedFlow['steps'] = []
  const edges: PlannedFlow['edges'] = []
  steps.push({ id: 't.trigger', label: name, kind: 'cua', col: 0 })
  steps.push({ id: 't.agent', label: 'Agente ejecutor', kind: 'agent', group: 'experto', col: 1 })
  edges.push({ source: 't.trigger', target: 't.agent', rel: 'planifica' })
  caps.slice(0, 4).forEach((c, j) => {
    const id = `t.s${j}`
    steps.push({ id, label: c, kind: 'skill', group: 'analisis', col: 2 })
    edges.push({ source: 't.agent', target: id, rel: 'usa' })
  })
  steps.push({ id: 't.platform', label: platformLabel, kind: 'platform', group: 'web', col: 3 })
  edges.push({ source: caps.length ? `t.s0` : 't.agent', target: 't.platform', rel: 'ejecuta' })
  return { id: `tool.${toolId}.${Date.now()}`, name, kind: 'cua', mode: 'supervised', status: 'planned', instruction, steps, edges }
}

export default function ToolStudio({ toolId, profile, onClose, onLaunch, onAddToPlan }: Props): React.JSX.Element | null {
  const tool = toolId ? TOOL_BY_ID[toolId] : null
  const [v, setV] = useState<Record<string, string>>({})
  // smart-prefill desde el perfil al abrir / cambiar de herramienta
  useEffect(() => {
    const t = toolId ? TOOL_BY_ID[toolId] : null
    setV(t?.smartDefaults && profile ? t.smartDefaults(profile) : {})
  }, [toolId, profile])
  if (!tool) return null
  const accountUrl = accountUrlFor(tool, profile)
  const accent = CATEGORY_COLOR[tool.category ?? 'chat'] ?? T.cobalt
  const strat = tool.strategyRef ? STRATEGY_BY_ID[tool.strategyRef] : undefined
  const buildToolFlow = (): PlannedFlow => {
    let instruction = profile ? tool.buildInstruction(profile, v, accountUrl) : tool.desc
    if (tool.guardrail?.supervised) instruction = `[SUPERVISADO — pedí confirmación antes de acciones irreversibles] ${instruction}`
    return buildFlow(tool.id, tool.name, tool.capabilities, tool.platformLabel, instruction)
  }
  const launch = (): void => { onLaunch(buildToolFlow()); onClose() }
  const addToPlan = (): void => { onAddToPlan?.(buildToolFlow()); onClose() }

  return (
    <div className="fixed inset-0 z-[126] flex items-center justify-center px-4" onClick={onClose}
      style={{ background: 'rgba(5,8,16,0.78)', backdropFilter: 'blur(10px)' }}>
      <div onClick={e => e.stopPropagation()} style={{ width: '100%', maxWidth: 560, maxHeight: '88vh', overflowY: 'auto', background: T.panel, border: `1px solid ${T.borderStrong}`, borderRadius: 16, fontFamily: T.sans, color: T.text }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '16px 20px', borderBottom: `1px solid ${T.border}` }}>
          <span style={{ width: 30, height: 30, borderRadius: 8, display: 'grid', placeItems: 'center', background: `${accent}1F`, border: `1px solid ${accent}44`, color: accent }}><Wrench size={15} /></span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 15, fontWeight: 700 }}>{tool.name}</div>
            <div style={{ fontSize: 11, color: T.text2, fontFamily: T.mono }}>{tool.category ?? ''} · anexada a {tool.platformLabel}</div>
          </div>
          <button type="button" onClick={onClose} style={{ width: 30, height: 30, borderRadius: '50%', border: `1px solid ${T.border}`, background: 'transparent', color: T.text2, cursor: 'pointer' }}><X size={15} /></button>
        </div>

        <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <p style={{ margin: 0, fontSize: 13, color: T.text2 }}>{tool.desc}</p>

          {/* KPI + estrategia (inteligente/eficaz) */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {tool.kpi && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11.5, fontWeight: 600, color: accent, background: `${accent}14`, border: `1px solid ${accent}33`, borderRadius: 7, padding: '4px 9px' }}>
                <Target size={12} /> {tool.kpi}
              </span>
            )}
            {strat && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11.5, color: T.text2, border: `1px solid ${T.border}`, borderRadius: 7, padding: '4px 9px' }}>
                <BookOpen size={12} /> basado en: {strat.title}
              </span>
            )}
          </div>

          {/* guardrail responsable */}
          {tool.guardrail && (
            <div style={{ display: 'flex', gap: 8, padding: '9px 12px', borderRadius: 9, background: `${T.emerald}10`, border: `1px solid ${T.emerald}33` }}>
              <ShieldCheck size={15} style={{ color: T.emerald, flexShrink: 0, marginTop: 1 }} />
              <span style={{ fontSize: 11.5, color: T.text, lineHeight: 1.5 }}>
                {tool.guardrail.supervised ? <strong>Modo Supervisado · </strong> : null}{tool.guardrail.note}
              </span>
            </div>
          )}

          {/* checklist resolutiva */}
          {tool.checklist && tool.checklist.length > 0 && (
            <div>
              <div style={{ fontSize: 11, color: T.text3, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>Qué vas a obtener</div>
              {tool.checklist.map((c, i) => (
                <div key={i} style={{ display: 'flex', gap: 7, fontSize: 12, color: T.text2, marginBottom: 4 }}>
                  <Check size={12} style={{ color: accent, flexShrink: 0, marginTop: 2 }} />{c}
                </div>
              ))}
            </div>
          )}

          {/* cuenta anexada */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 12px', borderRadius: 9, background: T.bg, border: `1px solid ${T.border}` }}>
            <span style={{ fontSize: 12, color: T.text3 }}>Cuenta:</span>
            {accountUrl
              ? <a href={accountUrl.startsWith('http') ? accountUrl : `https://${accountUrl}`} target="_blank" rel="noreferrer" style={{ color: T.cobalt, fontSize: 12, display: 'inline-flex', alignItems: 'center', gap: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{accountUrl} <ExternalLink size={11} /></a>
              : <span style={{ fontSize: 12, color: T.amber }}>sin link cargado — agregalo en “Mi negocio” para anexar la cuenta</span>}
          </div>

          {/* qué hace */}
          <div>
            <div style={{ fontSize: 11, color: T.text3, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>Qué hace</div>
            {tool.capabilities.map((c, i) => (
              <div key={i} style={{ display: 'flex', gap: 7, fontSize: 12.5, color: T.text, marginBottom: 4 }}>
                <Check size={13} style={{ color: T.emerald, flexShrink: 0, marginTop: 2 }} />{c}
              </div>
            ))}
          </div>

          {/* aviso de seguridad (advisory) */}
          {tool.safetyNote && (
            <div style={{ display: 'flex', gap: 8, padding: '10px 12px', borderRadius: 9, background: `${T.amber}12`, border: `1px solid ${T.amber}40` }}>
              <AlertTriangle size={15} style={{ color: T.amber, flexShrink: 0, marginTop: 1 }} />
              <span style={{ fontSize: 12, color: T.text, lineHeight: 1.5 }}>{tool.safetyNote}</span>
            </div>
          )}

          {/* create_confirm: ¿creo por vos? */}
          {tool.studioMode === 'create_confirm' && (
            <div>
              <div style={{ fontSize: 12, color: T.text2, marginBottom: 6, fontWeight: 600 }}>¿Querés que SellIA lo cree por vos?</div>
              <div style={{ display: 'flex', gap: 8 }}>
                {[['si', 'Sí, creá por mí'], ['no', 'No, solo abrir mi Canva']].map(([val, lbl]) => (
                  <button key={val} type="button" onClick={() => setV(s => ({ ...s, create: val }))}
                    style={{ flex: 1, padding: '9px', borderRadius: 9, cursor: 'pointer', fontSize: 12.5, fontWeight: 600, fontFamily: T.sans, border: `1px solid ${(v.create ?? 'si') === val ? T.cobalt : T.border}`, background: (v.create ?? 'si') === val ? `${T.cobalt}1F` : 'transparent', color: (v.create ?? 'si') === val ? T.cobalt : T.text2 }}>
                    {lbl}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* advisory: estrategia */}
          {tool.studioMode === 'advisory' && tool.strategies && (
            <div>
              <div style={{ fontSize: 12, color: T.text2, marginBottom: 6, fontWeight: 600 }}>Estrategia del bot</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                {tool.strategies.map(st => {
                  const on = (v.strategy ?? tool.strategies![0].id) === st.id
                  return (
                    <button key={st.id} type="button" onClick={() => setV(s => ({ ...s, strategy: st.id }))}
                      style={{ textAlign: 'left', padding: '9px 11px', borderRadius: 9, cursor: 'pointer', fontFamily: T.sans, border: `1px solid ${on ? T.cobalt : T.border}`, background: on ? `${T.cobalt}1F` : T.bg }}>
                      <div style={{ fontSize: 12.5, fontWeight: 700, color: on ? T.cobalt : T.text }}>{st.label}</div>
                      <div style={{ fontSize: 11, color: T.text3 }}>{st.desc}</div>
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {/* config */}
          {tool.inputs.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ fontSize: 11, color: T.text3, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Configuración</div>
              {tool.inputs.map(inp => (
                <div key={inp.key}>
                  <label style={{ fontSize: 12, color: T.text2, marginBottom: 4, display: 'block', fontWeight: 600 }}>{inp.label}</label>
                  {inp.type === 'textarea'
                    ? <textarea value={v[inp.key] ?? ''} onChange={e => setV(s => ({ ...s, [inp.key]: e.target.value }))} placeholder={inp.placeholder} rows={2} style={inputStyle} />
                    : <input value={v[inp.key] ?? ''} onChange={e => setV(s => ({ ...s, [inp.key]: e.target.value }))} placeholder={inp.placeholder} style={inputStyle} />}
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ padding: '14px 20px', borderTop: `1px solid ${T.border}`, display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          {onAddToPlan && (
            <button type="button" onClick={addToPlan} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '10px 16px', borderRadius: 9, border: `1px solid ${T.border}`, background: 'transparent', color: T.text, fontWeight: 600, cursor: 'pointer', fontSize: 13 }}>
              <Plus size={15} /> Agregar al plan
            </button>
          )}
          <button type="button" onClick={launch} style={{ display: 'inline-flex', alignItems: 'center', gap: 7, padding: '10px 20px', borderRadius: 9, border: 'none', background: accent, color: '#101010', fontWeight: 800, cursor: 'pointer', fontSize: 13 }}>
            <Rocket size={15} /> Lanzar herramienta
          </button>
        </div>
      </div>
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '9px 11px', borderRadius: 8, background: SELLIA.bg,
  border: `1px solid ${SELLIA.border}`, color: SELLIA.text, fontSize: 13, outline: 'none',
  fontFamily: SELLIA.sans, boxSizing: 'border-box', resize: 'vertical',
}
