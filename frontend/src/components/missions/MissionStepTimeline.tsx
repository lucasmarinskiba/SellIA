'use client'

import { motion } from 'framer-motion'
import {
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  SkipForward,
  AlertCircle,
  Monitor,
  Zap,
  Camera as Instagram,
  Globe as Facebook,
  ShoppingBag,
  Globe,
  Mail,
  Search,
} from 'lucide-react'
import { MissionStep, StepStatus } from '@/lib/missions'
import Badge from '@/components/ui/Badge'

const platformIcons: Record<string, React.ReactNode> = {
  computer_use: <Monitor className="w-4 h-4" />,
  api: <Zap className="w-4 h-4" />,
  instagram: <Instagram className="w-4 h-4" />,
  facebook: <Facebook className="w-4 h-4" />,
  shopify: <ShoppingBag className="w-4 h-4" />,
  google: <Search className="w-4 h-4" />,
  meta_ads: <MegaphoneIcon />,
  email: <Mail className="w-4 h-4" />,
  web: <Globe className="w-4 h-4" />,
}

function MegaphoneIcon() {
  return (
    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m3 11 18-5v12L3 14v-3z" />
      <path d="M11.6 16.8a3 3 0 1 1-5.8-1.6" />
    </svg>
  )
}

const statusConfig: Record<StepStatus, { label: string; color: string; icon: React.ReactNode }> = {
  pending: { label: 'Pendiente', color: 'text-white/40', icon: <Clock className="w-4 h-4" /> },
  running: { label: 'En ejecución', color: 'text-brand-orange', icon: <Loader2 className="w-4 h-4 animate-spin" /> },
  completed: { label: 'Completado', color: 'text-emerald-400', icon: <CheckCircle className="w-4 h-4" /> },
  failed: { label: 'Fallido', color: 'text-red-400', icon: <XCircle className="w-4 h-4" /> },
  skipped: { label: 'Omitido', color: 'text-white/30', icon: <SkipForward className="w-4 h-4" /> },
  waiting_approval: { label: 'Esperando aprobación', color: 'text-amber-400', icon: <AlertCircle className="w-4 h-4" /> },
}

interface MissionStepTimelineProps {
  steps: MissionStep[]
}

export default function MissionStepTimeline({ steps }: MissionStepTimelineProps) {
  const sortedSteps = [...steps].sort((a, b) => a.step_number - b.step_number)

  return (
    <div className="space-y-0">
      {sortedSteps.map((step, index) => {
        const status = statusConfig[step.status]
        const icon = platformIcons[step.platform] || <Zap className="w-4 h-4" />
        const isLast = index === sortedSteps.length - 1

        return (
          <motion.div
            key={step.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.08 }}
            className="relative flex gap-4"
          >
            {/* Timeline line */}
            {!isLast && (
              <div className="absolute left-[19px] top-10 bottom-0 w-px bg-white/10" />
            )}

            {/* Status dot */}
            <div className="relative z-10 flex flex-col items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center border-2 ${
                  step.status === 'completed'
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                    : step.status === 'running'
                    ? 'bg-brand-orange/10 border-brand-orange/30 text-brand-orange'
                    : step.status === 'failed'
                    ? 'bg-red-500/10 border-red-500/30 text-red-400'
                    : 'bg-white/5 border-white/10 text-white/30'
                }`}
              >
                {status.icon}
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 pb-6">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-white/90">{step.title}</span>
                    <Badge variant={step.status === 'completed' ? 'success' : step.status === 'failed' ? 'destructive' : step.status === 'running' ? 'orange' : 'secondary'} className="text-[10px]">
                      {status.label}
                    </Badge>
                  </div>
                  {step.description && (
                    <p className="text-xs text-white/40 mt-1">{step.description}</p>
                  )}
                  <div className="flex items-center gap-2 mt-2">
                    <div className="flex items-center gap-1 text-xs text-white/30">
                      {icon}
                      <span className="capitalize">{step.platform}</span>
                    </div>
                    {step.action_type && (
                      <span className="text-xs text-white/20">· {step.action_type}</span>
                    )}
                  </div>
                </div>
              </div>

              {step.error_message && (
                <div className="mt-2 p-2 rounded-lg bg-red-500/5 border border-red-500/10 text-xs text-red-400">
                  {step.error_message}
                </div>
              )}

              {step.result && Object.keys(step.result).length > 0 && step.status === 'completed' && (
                <div className="mt-2 p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
                  <pre className="text-[10px] text-emerald-400/80 overflow-auto">
                    {JSON.stringify(step.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
