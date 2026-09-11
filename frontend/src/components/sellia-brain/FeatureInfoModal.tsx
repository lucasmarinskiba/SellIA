'use client'

import { AutomationToggleResponse } from '@/lib/api/toggles'

const FEATURE_INFO: Record<string, { details: string; cost: string; recommendation: string }> = {
  'agent:lead_scorer': {
    details: 'Califica leads por conversion probability usando ML model con 20+ features. Accuracy: 87%.',
    cost: '$0.05 por lead • ~250 leads/día en plan Pro',
    recommendation: 'Mantener enabled • Bajo costo, alto ROI',
  },
  'agent:cold_email': {
    details: 'Redacta emails de prospección personalizados. Copywriting avanzado + A/B optimización.',
    cost: '$0.02 por email • ~500 emails/mes en plan Pro',
    recommendation: 'Mantener enabled • Essential para outreach',
  },
  'agent:negotiation': {
    details: 'Estrategia de cierre y manejo de objeciones. Técnicas de Trump + Belfort Straight Line.',
    cost: '$0.10 por deal • ~20 deals/mes en plan Pro',
    recommendation: 'Activar solo si vendes deals complejos',
  },
  'automation:email_sequences': {
    details: 'Workflows automáticos de email nurturing. Triggered por eventos, delays configurables.',
    cost: 'Incluido en plan • Sin costo adicional',
    recommendation: 'Siempre enabled • Fundación de growth',
  },
  'automation:fomo_campaigns': {
    details: 'Urgencia + escasez + social proof. Timer countdown + stock limited alerts.',
    cost: 'Incluido en plan • Sin costo adicional',
    recommendation: 'Mantener enabled • Aumenta conversion 15-30%',
  },
  'automation:sms_marketing': {
    details: 'Mensajes automáticos vía WhatsApp/SMS. 98% open rate, 45% click rate.',
    cost: '$0.01 por SMS • ~5000 SMS/mes en plan Pro',
    recommendation: 'Activar para re-engagement campaigns',
  },
  'feature:dynamic_pricing': {
    details: 'Ajusta precios en tiempo real según demanda, competencia, inventario.',
    cost: 'Incluido en plan • Sin costo adicional',
    recommendation: 'Pro: +10-20% revenue • Mantener enabled',
  },
  'feature:predictive_analytics': {
    details: 'Forecasting de demanda y churn. Predice qué customers van a irse.',
    cost: 'Incluido en plan • Sin costo adicional',
    recommendation: 'Essential para retention strategy',
  },
  'feature:computer_use': {
    details: 'Automatización de tareas web. Browser automation + API integrations.',
    cost: '$0.50 por task • ~100 tasks/mes en plan Pro (caro)',
    recommendation: 'Activar solo si tareas manuales > $50/mes',
  },
}

interface FeatureInfoModalProps {
  toggle: AutomationToggleResponse
  onClose: () => void
}

export const FeatureInfoModal = ({ toggle, onClose }: FeatureInfoModalProps) => {
  const info = FEATURE_INFO[toggle.toggle_key] || {
    details: toggle.description || 'Sin información disponible',
    cost: 'Consultar pricing',
    recommendation: 'Contactar sales',
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-800 rounded-lg max-w-2xl w-full shadow-lg">
        {/* Header */}
        <div className="border-b border-slate-200 dark:border-slate-700 p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <span className="text-4xl">{toggle.icon || '⚙️'}</span>
              <div>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                  {toggle.display_name}
                </h2>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                  {toggle.toggle_key}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 text-2xl"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Qué hace */}
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-2 uppercase tracking-wide">
              Qué hace
            </h3>
            <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
              {info.details}
            </p>
          </div>

          {/* Costo */}
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-2 uppercase tracking-wide">
              💰 Costo
            </h3>
            <p className="text-slate-700 dark:text-slate-300 font-mono">
              {info.cost}
            </p>
          </div>

          {/* Recomendación */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-1 uppercase tracking-wide">
              💡 Recomendación
            </h3>
            <p className="text-blue-800 dark:text-blue-100">
              {info.recommendation}
            </p>
          </div>

          {/* Status */}
          <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700/30 rounded-lg">
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Estado</span>
            <span className={`px-3 py-1 rounded text-sm font-semibold ${
              toggle.is_enabled
                ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-100'
                : 'bg-slate-300 text-slate-800 dark:bg-slate-600 dark:text-slate-100'
            }`}>
              {toggle.is_enabled ? '✅ Habilitado' : '🚫 Deshabilitado'}
            </span>
          </div>

          {/* Usage if applicable */}
          {toggle.monthly_limit && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white uppercase tracking-wide">
                📊 Uso Mensual
              </h3>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-700 dark:text-slate-300">
                  {toggle.current_month_usage} / {toggle.monthly_limit}
                </span>
                <span className="font-mono font-semibold">
                  {Math.round((toggle.current_month_usage / toggle.monthly_limit) * 100)}%
                </span>
              </div>
              <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500"
                  style={{ width: `${Math.min((toggle.current_month_usage / toggle.monthly_limit) * 100, 100)}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-200 dark:border-slate-700 p-6">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded font-medium hover:bg-blue-600 transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}
