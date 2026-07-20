'use client'

/**
 * BUSINESS TOOLKIT — herramienta visual para vender.
 *
 * Según el perfil del negocio: recomienda flujos/automatizaciones/herramientas
 * a activar, valida los links cargados (abrir/estado) y lanza Computer Use con
 * una indicación armada desde el negocio + sus links reales.
 */

import { SELLIA } from '@/lib/sellia-theme'
import {
  type BusinessProfile, recommendFlows, validateLink, isComplete, planAccountFlows,
} from '@/lib/business-profile'
import { ExternalLink, Workflow, Wrench, Bot, Rocket, Settings } from 'lucide-react'

const T = SELLIA

const KIND_ICON: Record<string, React.ReactNode> = {
  automation: <Workflow size={13} />, tool: <Wrench size={13} />, agent: <Bot size={13} />,
}

import { TOOL_BY_ID, CATEGORY_COLOR } from '@/lib/tools-catalog'

interface Props { profile: BusinessProfile | null; onEdit: () => void; onPlan: () => void; onOpenTool: (id: string) => void; onPlanComplete: (toolIds: string[]) => void }

const card: React.CSSProperties = { background: T.panel, border: `1px solid ${T.border}`, borderRadius: 12, padding: 16 }

export default function BusinessToolkit({ profile, onEdit, onPlan, onOpenTool, onPlanComplete }: Props): React.JSX.Element {
  if (!isComplete(profile)) {
    return (
      <div style={{ ...card, textAlign: 'center', padding: 28, fontFamily: T.sans }}>
        <Rocket size={22} style={{ color: T.cobalt, marginBottom: 8 }} />
        <div style={{ fontSize: 14, fontWeight: 700, color: T.text }}>Completá tu negocio</div>
        <div style={{ fontSize: 12, color: T.text2, margin: '6px 0 14px' }}>
          Cargá qué vendés y tus links (venta, anuncios, redes) para que SellIA venda por vos.
        </div>
        <button type="button" onClick={onEdit} style={{ padding: '9px 18px', borderRadius: 9, border: 'none', background: T.cobalt, color: '#fff', fontWeight: 700, cursor: 'pointer', fontSize: 13 }}>
          Completar negocio
        </button>
      </div>
    )
  }

  const p = profile!
  const recs = recommendFlows(p)
  const links = [
    ...[...p.salesPlatforms, ...p.adPlatforms, ...p.socialLinks].filter(l => l.enabled && l.url).map(l => ({ id: l.id, label: l.label, url: l.url, tag: '' })),
    ...(p.customLinks ?? []).filter(l => l.enabled && l.url).map(l => ({ id: l.id, label: l.label || l.url, url: l.url, tag: l.type })),
  ]
  const accountFlows = planAccountFlows(p)

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, fontFamily: T.sans }}>
      {/* recomendaciones */}
      <div style={card}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: T.text }}>Recomendado para tu negocio</span>
          <span style={{ flex: 1 }} />
          <button type="button" onClick={onEdit} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11, color: T.text2, background: 'none', border: `1px solid ${T.border}`, borderRadius: 7, padding: '4px 9px', cursor: 'pointer' }}>
            <Settings size={12} /> Editar
          </button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {recs.map(r => {
            const tool = TOOL_BY_ID[r.id]
            const hasTool = !!tool
            const c = CATEGORY_COLOR[tool?.category ?? 'chat'] ?? T.cobalt
            return (
              <button key={r.id} type="button" disabled={!hasTool} onClick={() => hasTool && onOpenTool(r.id)}
                style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px', borderRadius: 9, background: T.bg, border: `1px solid ${hasTool ? c + '33' : T.border}`, cursor: hasTool ? 'pointer' : 'default', textAlign: 'left', width: '100%' }}>
                <span style={{ color: c }}>{KIND_ICON[r.kind]}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12.5, fontWeight: 600, color: T.text }}>{r.title}</div>
                  <div style={{ fontSize: 11, color: T.text3 }}>{tool?.kpi ?? r.reason}</div>
                </div>
                {hasTool && <span style={{ fontSize: 10, color: c, fontWeight: 700 }}>Abrir →</span>}
              </button>
            )
          })}
          {recs.length === 0 && <span style={{ fontSize: 12, color: T.text3 }}>Sin recomendaciones (cargá más datos).</span>}
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
          <button type="button" onClick={() => onPlanComplete(recs.filter(r => TOOL_BY_ID[r.id]).map(r => r.id))} disabled={recs.filter(r => TOOL_BY_ID[r.id]).length === 0}
            style={{ flex: 1, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 7, padding: '10px', borderRadius: 9, border: `1px solid ${T.cobalt}`, background: `${T.cobalt}1F`, color: T.cobalt, fontWeight: 700, cursor: 'pointer', fontSize: 12.5 }}>
            Plan completo ({recs.filter(r => TOOL_BY_ID[r.id]).length})
          </button>
          <button type="button" onClick={onPlan} disabled={accountFlows.length === 0}
            style={{ flex: 1, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 7, padding: '10px', borderRadius: 9, border: 'none', background: T.emerald, color: '#04110b', fontWeight: 800, cursor: accountFlows.length ? 'pointer' : 'not-allowed', opacity: accountFlows.length ? 1 : 0.5, fontSize: 12.5 }}>
            <Rocket size={15} /> Mis {accountFlows.length} cuentas
          </button>
        </div>
      </div>

      {/* validador de links */}
      <div style={card}>
        <div style={{ fontSize: 13, fontWeight: 700, color: T.text, marginBottom: 12 }}>Tus links ({links.length})</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
          {links.map(l => {
            const c = validateLink(l.url)
            return (
              <div key={l.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: c.ok ? T.emerald : T.amber, flexShrink: 0 }} />
                <span style={{ color: T.text2, width: 110, flexShrink: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {l.label}{l.tag ? <span style={{ marginLeft: 5, fontSize: 9, color: T.text3, border: `1px solid ${T.border}`, borderRadius: 4, padding: '0 4px' }}>{l.tag}</span> : null}
                </span>
                <a href={l.url.startsWith('http') ? l.url : `https://${l.url}`} target="_blank" rel="noreferrer"
                  style={{ color: T.cobalt, fontSize: 11.5, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                  {l.url} <ExternalLink size={11} style={{ flexShrink: 0 }} />
                </a>
                <span style={{ color: c.ok ? T.emerald : T.amber, fontSize: 11, flexShrink: 0 }}>{c.ok ? 'OK' : c.reason}</span>
              </div>
            )
          })}
          {links.length === 0 && <span style={{ fontSize: 12, color: T.text3 }}>Sin links cargados.</span>}
        </div>
      </div>
    </div>
  )
}
