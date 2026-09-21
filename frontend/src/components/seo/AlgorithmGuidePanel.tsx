'use client'

import React, { useEffect, useState } from 'react'
import { ChevronDown, ChevronRight, Loader2 } from 'lucide-react'
import {
  seoConfigApi,
  type AlgorithmCoverage,
  type AlgorithmGuide,
  type FactorEvidence,
  type PositioningAction,
  type PositioningSummary,
} from '@/lib/seoConfig'

interface AlgorithmGuidePanelProps {
  businessId: string
}

const COVERAGE_LABEL: Record<AlgorithmCoverage, string> = {
  measured: 'Medido con datos de la plataforma',
  web_audit: 'Auditoría de la página',
  guidance_only: 'Solo guía, sin medición',
}

const EVIDENCE_LABEL: Record<FactorEvidence, string> = {
  official: 'Lo documenta la plataforma',
  community: 'Consenso de vendedores, no oficial',
}

const SEVERITY_STYLE: Record<PositioningAction['severity'], string> = {
  critical: 'bg-red-50 text-red-700 border-red-200',
  warning: 'bg-amber-50 text-amber-700 border-amber-200',
  info: 'bg-slate-50 text-slate-700 border-slate-200',
}

export function AlgorithmGuidePanel({ businessId }: AlgorithmGuidePanelProps): React.JSX.Element {
  const [guides, setGuides] = useState<AlgorithmGuide[]>([])
  const [summary, setSummary] = useState<PositioningSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [failed, setFailed] = useState(false)
  const [open, setOpen] = useState<string | null>(null)

  useEffect(() => {
    const load = async (): Promise<void> => {
      try {
        const [guide, positioning] = await Promise.all([
          seoConfigApi.getAlgorithmGuide(businessId),
          seoConfigApi.getPositioningSummary(businessId),
        ])
        setGuides(guide.platforms)
        setSummary(positioning)
      } catch (error) {
        console.error('Error loading algorithm guide:', error)
        setFailed(true)
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [businessId])

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-slate-500 py-6 justify-center">
        <Loader2 className="w-4 h-4 animate-spin" /> Cargando guía de algoritmos…
      </div>
    )
  }

  if (failed) {
    return <p className="text-sm text-slate-500">No se pudo cargar la guía de algoritmos.</p>
  }

  const actions = summary?.top_actions ?? []
  const unscored = summary?.unscored_links ?? []

  return (
    <div className="space-y-6">
      {actions.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-900 mb-2">Qué corregir primero</h3>
          <ul className="space-y-2">
            {actions.map((action) => (
              <li key={action.id} className={`rounded-lg border p-3 text-sm ${SEVERITY_STYLE[action.severity]}`}>
                <p>{action.message}</p>
                {action.why && (
                  <p className="mt-1 text-xs opacity-80">
                    Por qué importa ({EVIDENCE_LABEL[action.why.evidence].toLowerCase()}): {action.why.note}
                  </p>
                )}
                {action.affected > 1 && (
                  <p className="mt-1 text-xs opacity-80">Afecta a {action.affected} publicaciones.</p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {unscored.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-900 mb-2">Publicaciones sin puntaje</h3>
          <ul className="space-y-1 text-sm text-slate-600">
            {unscored.map((link) => (
              <li key={link.link_id}>
                <span className="font-medium text-slate-800">{link.title}</span>: {link.reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div>
        <h3 className="text-sm font-semibold text-slate-900 mb-2">Cómo rankea cada plataforma</h3>
        <ul className="space-y-2">
          {guides.map((guide) => {
            const expanded = open === guide.platform
            return (
              <li key={guide.platform} className="rounded-lg border border-slate-200">
                <button
                  type="button"
                  onClick={() => setOpen(expanded ? null : guide.platform)}
                  className="w-full flex items-center gap-2 p-3 text-left"
                  aria-expanded={expanded}
                >
                  {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  <span className="font-medium text-slate-900">{guide.label}</span>
                  {guide.in_use && (
                    <span className="text-xs rounded-full bg-emerald-50 text-emerald-700 px-2 py-0.5">
                      La usás
                    </span>
                  )}
                  <span className="ml-auto text-xs text-slate-500">{COVERAGE_LABEL[guide.coverage]}</span>
                </button>

                {expanded && (
                  <div className="border-t border-slate-100 p-3 space-y-3 text-sm text-slate-700">
                    <p>{guide.summary}</p>
                    <p className="text-xs text-slate-500">{guide.disclosure}</p>

                    {!guide.researched && (
                      <p className="text-xs text-slate-500">
                        Todavía no investigamos esta plataforma: no mostramos factores para no inventarlos.
                      </p>
                    )}

                    {guide.factors.length > 0 && (
                      <ul className="space-y-2">
                        {guide.factors.map((factor) => (
                          <li key={factor.name}>
                            <span className="font-medium text-slate-900">{factor.name}</span>{' '}
                            <span
                              className={`text-xs rounded-full px-2 py-0.5 ${
                                factor.evidence === 'official'
                                  ? 'bg-blue-50 text-blue-700'
                                  : 'bg-slate-100 text-slate-600'
                              }`}
                            >
                              {EVIDENCE_LABEL[factor.evidence]}
                            </span>
                            <p className="text-slate-600">{factor.note}</p>
                          </li>
                        ))}
                      </ul>
                    )}

                    {guide.not_measurable.length > 0 && (
                      <div>
                        <p className="font-medium text-slate-900">Lo que no se puede medir</p>
                        <ul className="list-disc pl-5 text-slate-600">
                          {guide.not_measurable.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {guide.playbook.length > 0 && (
                      <div>
                        <p className="font-medium text-slate-900">Qué hacer</p>
                        <ul className="list-disc pl-5 text-slate-600">
                          {guide.playbook.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}
